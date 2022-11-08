import requests
from lxml import etree
import random
import re
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64encode
from inputimeout import inputimeout, TimeoutOccurred
from user_agents import parse
import ddddocr

from .utils import config, urls
from ._base_ import baseLogin


class pwdLogin(baseLogin):
    def __init__(self, username: str, password: str, headers: dict = config.headers, getTimeout: int = config.getTimeout, mobileLogin: bool = False):
        """
        pwdLogin(username: str, password: str, headers: dict = config.headers, getTimeout: int = config.getTimeout)
        @description:
        账号密码登录
        -------
        @param:
        username: str, 账号
        password: str, 密码
        headers: dict, 请求头
        getTimeout: int, 请求超时时间，即在getTimeout秒内未获取到响应则抛出TimeoutError
        mobileLogin: bool, 是否是APP登录
        -------
        """
        if mobileLogin:
            assert parse(headers['User-Agent']).is_mobile, 'mobileLogin要求使用手机User-Agent'
        super().__init__(headers)
        self.username = username
        self.password = password
        self.mobileLogin = mobileLogin
        self.getTimeout = getTimeout

    def getCaptcha(self) -> str:
        """获取验证码"""
        captcha = self.get(urls.captcha, timeout=self.getTimeout).content
        ocr = ddddocr.DdddOcr(show_ad=False)
        return ocr.classification(captcha)

    def get_pwdDefaultEncryptSalt(self, selector: etree._Element) -> str:
        """获取密码加密盐"""
        pwdDefaultEncryptSalt = '\n'.join(selector.xpath('//script/text()'))
        return re.search(r'pwdDefaultEncryptSalt = "(.*)";', pwdDefaultEncryptSalt).group(1)

    def pwdEncrypt(self, pwdDefaultEncryptSalt: str) -> str:
        """密码加密"""
        char = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678'
        rds1 = ''.join([random.choice(char) for _ in range(64)])
        rds2 = ''.join([random.choice(char) for _ in range(16)])
        data = (rds1 + self.password).encode('utf-8')
        key = pwdDefaultEncryptSalt.encode('utf-8')
        iv = rds2.encode('utf-8')
        pad_pkcs7 = pad(data, AES.block_size, style='pkcs7')
        aes = AES.new(key, AES.MODE_CBC, iv)
        return b64encode(aes.encrypt(pad_pkcs7)).decode('utf-8')

    def login(self, dest: str) -> requests.Session | None:
        captcha = self.getCaptcha()

        url = urls.login % dest
        html = self.get(url, timeout=self.getTimeout).text
        selector = etree.HTML(html)
        password = self.pwdEncrypt(self.get_pwdDefaultEncryptSalt(selector))

        dataIdx = 1 if parse(self.session.headers['User-Agent']).is_pc else 0
        dllt = 'mobileLogin' if self.mobileLogin else selector.xpath('//input[@name="dllt"]/@value')[dataIdx]
        data = {
            'username': self.username,
            'password': password,
            'lt': selector.xpath('//input[@name="lt"]/@value')[dataIdx],
            'captchaResponse': captcha,
            'dllt': dllt,
            'execution': selector.xpath('//input[@name="execution"]/@value')[dataIdx],
            '_eventId': selector.xpath('//input[@name="_eventId"]/@value')[dataIdx],
            'rmShown': selector.xpath('//input[@name="rmShown"]/@value')[dataIdx]
        }
        res = self.post(url, data=data, timeout=self.getTimeout)

        if res.url == url:
            # 登录失败
            # 可能登录失败也可能是验证码错误
            selector = etree.HTML(res.text)
            errorMsg = selector.xpath('//span[@id="errorMsg"]/text()')[0]
            if errorMsg == '无效的验证码':
                # 验证码错误
                return self.login(dest)
            elif errorMsg == '您提供的用户名或者密码有误':
                # 账号密码错误
                print('登录失败，账号密码错误')
                return None
            else:
                # 需要输入动态码
                res = self.post(self.session, urls.dynamicCode, timeout=self.getTimeout,
                    data={'username': self.username, 'authCodeTypeName': 'reAuthDynamicCodeType'}
                )
                msg = 'fail'
                try:
                    msg = res.json()['returnMessage']
                    res = res.json()['res']
                    if msg.startswith('您已重复发送'):
                        res = 'success'
                    assert res == 'success'
                except:
                    print('登录失败，%s' % msg)
                    return None
                try:
                    dynamicCode = inputimeout(prompt='请输入发送至手机的动态码: ', timeout=120)
                except TimeoutOccurred:
                    print('登录失败，输入动态码超时')
                    return None
                data = {
                    'dynamicCode': dynamicCode,
                    'username': self.username,
                    'execution': selector.xpath('//input[@name="execution"]/@value')[0],
                    '_eventId': selector.xpath('//input[@name="_eventId"]/@value')[0]
                }
                res = self.post(self.session, url, data=data, timeout=self.getTimeout)
                if res.url == url:
                    print('登录失败，动态码错误')
                    return None

        print('登录成功')
        return self.session
