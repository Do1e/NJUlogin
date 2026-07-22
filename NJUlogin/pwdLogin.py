import random
from base64 import b64encode

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from lxml import etree

from .base import baseLogin
from .sliderCaptcha import DEFAULT_ATTEMPTS, verify_slider_captcha
from .utils import urls


class pwdLogin(baseLogin):
    def __init__(self, username: str, password: str, *args, **kwargs):
        """账号密码登录"""
        super().__init__(*args, **kwargs)
        self.username = username
        self.password = password

    def get_pwdDefaultEncryptSalt(self, selector: etree._Element) -> str:
        """获取密码加密盐"""
        return selector.xpath('//*[@id="pwdEncryptSalt"]/@value')[0]

    def verifySliderCaptcha(self, referer: str, attempts: int = DEFAULT_ATTEMPTS) -> bool:
        """识别并验证新版滑块验证码。"""
        return verify_slider_captcha(self, referer, attempts=attempts)

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
        if need_captcha and not self.verifySliderCaptcha(
            url, attempts=max(1, DEFAULT_ATTEMPTS - trytimes)
        ):
            print("登录失败，滑块验证码验证错误次数过多")
            return None
        password = self.pwdEncrypt(self.get_pwdDefaultEncryptSalt(selector))

        forms = selector.xpath('//form[.//input[@name="cllt" and @value="userNameLogin"]]')
        if not forms:
            raise RuntimeError("未找到统一身份认证的账号密码登录表单")
        password_form = forms[0]

        def get_field(name):
            vals = password_form.xpath(f'.//input[@name="{name}"]/@value')
            return vals[0] if vals else ""

        data = {
            "username": self.username,
            "password": password,
            "lt": get_field("lt"),
            "captcha": "",
            "cllt": get_field("cllt") or "userNameLogin",
            "dllt": get_field("dllt"),
            "execution": get_field("execution"),
            "_eventId": get_field("_eventId"),
        }
        rm_shown = get_field("rmShown")
        if rm_shown:
            data["rmShown"] = rm_shown
        res = self.post(url, data=data)
        if self.judge_not_login(res, url):
            # print('登录失败')
            selector = etree.HTML(res.text)
            try:
                msgs = selector.xpath('//span[@id="showErrorTip"]//text()')
                errorMsg = msgs[0].strip()
            except IndexError:
                print("登录失败，未知错误，可能是需要手机验证码，请先尝试手动登录")
                return None
            print("登录失败，" + errorMsg)
            return None
        self.response = res
        return self.session
