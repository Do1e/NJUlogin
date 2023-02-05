import requests
from lxml import etree
import random
import re
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64encode
import ddddocr

from .utils import config, urls
from ._base_ import baseLogin


class pwdLogin(baseLogin):
    def __init__(self, username: str, password: str, headers: dict = config.headers, getTimeout: int = config.getTimeout):
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
        -------
        """
        super().__init__(headers)
        self.username = username
        self.password = password
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

    def login(self, dest: str, trytimes: int = 0) -> requests.Session | None:
        captcha = self.getCaptcha()

        url = urls.login % dest
        html = self.get(url, timeout=self.getTimeout).text
        selector = etree.HTML(html)
        password = self.pwdEncrypt(self.get_pwdDefaultEncryptSalt(selector))

        data = {
            'username': self.username,
            'password': password,
            'lt': selector.xpath('//input[@name="lt"]/@value')[0],
            'captchaResponse': captcha,
            'dllt': selector.xpath('//input[@name="dllt"]/@value')[0],
            'execution': selector.xpath('//input[@name="execution"]/@value')[0],
            '_eventId': selector.xpath('//input[@name="_eventId"]/@value')[0],
            'rmShown': selector.xpath('//input[@name="rmShown"]/@value')[0]
        }
        res = self.post(url, data=data, timeout=self.getTimeout)
        if res.url == url or res is None:
            # print('登录失败')
            selector = etree.HTML(res.text)
            try:
                errorMsg = selector.xpath('//span[@id="msg"]/text()')[0]
            except IndexError:
                print('登录失败，未知错误，可能是需要手机验证码，请先尝试手动登录')
                return None
            if errorMsg == '无效的验证码':
                if trytimes >= 5:
                    print('登录失败，验证码识别错误次数过多')
                    return None
                print('登录失败，验证码识别错误，正在重试')
                return self.login(dest, trytimes + 1)
            else:
                print('登录失败，' + errorMsg)
            return None
        print('登录成功')
        return self.session
