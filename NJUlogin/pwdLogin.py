import requests
from lxml import etree
import random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64encode
from inputimeout import inputimeout, TimeoutOccurred
import ddddocr

from .utils import config, urls, get_post


class pwdLogin(object):
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
        self.session = requests.Session()
        self.session.headers.update(headers)
        self.username = username
        self.password = password
        self.getTimeout = getTimeout

    def getCaptcha(self) -> str:
        """获取验证码"""
        captcha = get_post.get(self.session, urls.captcha, timeout=self.getTimeout).content
        ocr = ddddocr.DdddOcr(show_ad=False)
        return ocr.classification(captcha)

    def get_pwdDefaultEncryptSalt(self, selector: etree._Element) -> str:
        """获取密码加密盐"""
        pwdDefaultEncryptSalt = selector.xpath('//input[@id="pwdDefaultEncryptSalt"]/@value')[0]
        return pwdDefaultEncryptSalt

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
        html = get_post.get(self.session, url, timeout=self.getTimeout).text
        selector = etree.HTML(html)
        password = self.pwdEncrypt(self.get_pwdDefaultEncryptSalt(selector))

        data = {
            'username': self.username,
            'password': password,
            'lt': selector.xpath('//input[@name="lt"]/@value')[1],
            'captchaResponse': captcha,
            'dllt': selector.xpath('//input[@name="dllt"]/@value')[1],
            'execution': selector.xpath('//input[@name="execution"]/@value')[1],
            '_eventId': selector.xpath('//input[@name="_eventId"]/@value')[1],
            'rmShown': selector.xpath('//input[@name="rmShown"]/@value')[0]
        }
        res = get_post.post(self.session, url, data=data, timeout=self.getTimeout)

        if res.url == url:
            # 可能登录失败也可能是验证码错误
            selector = etree.HTML(res.text)
            res = get_post.post(self.session, urls.dynamicCode, timeout=self.getTimeout,
                data={'username': self.username, 'authCodeTypeName': 'reAuthDynamicCodeType'}
            )
            msg = 'fail'
            try:
                msg = res.json()['returnMessage']
                res = res.json()['res']
                if msg == '发送动态码失败':
                    msg += '，可能原因：\n1. 账号密码填写错误，请检查后重试\n2. 识别图形验证码有误，请重新运行程序\n如果无法解决，可暂时尝试浏览器登录，之后一周不用重新获取动态码，并欢迎提交issue'
                elif msg.startswith('您已重复发送'):
                    res = 'success'
                assert res == 'success'
            except:
                print('登录失败，%s' % msg)
                return None
            try:
                dynamicCode = inputimeout(prompt='请输入发送至手机的验证码: ', timeout=120)
            except TimeoutOccurred:
                print('登录失败，输入验证码超时')
                return None
            data = {
                'dynamicCode': dynamicCode,
                'username': self.username,
                'execution': selector.xpath('//input[@name="execution"]/@value')[0],
                '_eventId': selector.xpath('//input[@name="_eventId"]/@value')[0]
            }
            res = get_post.post(self.session, url, data=data, timeout=self.getTimeout)
            if res.url == url:
                print('登录失败，动态码错误')
                return None

        print('登录成功')
        return self.session
