import random
import time
from base64 import b64encode

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from lxml import etree

from .base import baseLogin
from .captchaOCR import CaptchaOCR
from .utils import urls


class pwdLogin(baseLogin):
    def __init__(self, username: str, password: str, *args, **kwargs):
        """账号密码登录"""
        super().__init__(*args, **kwargs)
        self.username = username
        self.password = password

    def getCaptcha(self) -> str:
        """获取验证码"""
        ms = int(time.time() * 1000)
        captcha = self.get(urls.captcha % ms).content
        ocr = CaptchaOCR()
        return ocr.get_text(captcha)
        """
        以下代码调试用，展示验证码图片手动填写
        from PIL import Image
        import io
        Image.open(io.BytesIO(captcha)).show()
        return input("请输入验证码: ").strip()
        """

    def get_pwdDefaultEncryptSalt(self, selector: etree._Element) -> str:
        """获取密码加密盐"""
        return selector.xpath('//*[@id="pwdEncryptSalt"]/@value')[0]

    def pwdEncrypt(self, pwdDefaultEncryptSalt: str) -> str:
        """密码加密"""
        char = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"
        rds1 = "".join([random.choice(char) for _ in range(64)])
        rds2 = "".join([random.choice(char) for _ in range(16)])
        data = (rds1 + self.password).encode("utf-8")
        key = pwdDefaultEncryptSalt.encode("utf-8")
        iv = rds2.encode("utf-8")
        pad_pkcs7 = pad(data, AES.block_size, style="pkcs7")
        aes = AES.new(key, AES.MODE_CBC, iv)
        return b64encode(aes.encrypt(pad_pkcs7)).decode("utf-8")

    def login(self, dest: str = None, trytimes: int = 0) -> requests.Session:
        if dest is not None:
            url = urls.login % dest
        else:
            url = urls.login.split("?")[0]
        html = self.get(url).text
        selector = etree.HTML(html)
        # 检查是否需要验证码
        check_resp = self.get(urls.checkNeedCaptcha, params={"username": self.username})
        need_captcha = check_resp.json().get("isNeed", True)
        captcha = self.getCaptcha() if need_captcha else ""
        password = self.pwdEncrypt(self.get_pwdDefaultEncryptSalt(selector))

        def get_field(name):
            vals = selector.xpath(f'//input[@name="{name}"]/@value')
            return vals[0] if vals else ""

        data = {
            "username": self.username,
            "password": password,
            "lt": get_field("lt"),
            "captcha": captcha,
            "dllt": get_field("dllt"),
            "execution": get_field("execution"),
            "_eventId": get_field("_eventId"),
            "rmShown": get_field("rmShown"),
        }
        res = self.post(url, data=data)
        if self.judge_not_login(res, url):
            # print('登录失败')
            selector = etree.HTML(res.text)
            try:
                msgs = selector.xpath('//span[@id="msg1"]/text()') or \
                       selector.xpath('//*[contains(@class,"msg") or contains(@class,"error")]//text()')
                errorMsg = msgs[0].strip()
            except IndexError:
                print("登录失败，未知错误，可能是需要手机验证码，请先尝试手动登录")
                return None
            if errorMsg in ("无效的验证码", "图形动态码错误"):
                if trytimes >= 5:
                    print("登录失败，验证码识别错误次数过多")
                    return None
                print("登录失败，验证码识别错误，正在重试")
                return self.login(dest, trytimes + 1)
            else:
                print("登录失败，" + errorMsg)
            return None
        self.response = res
        return self.session
