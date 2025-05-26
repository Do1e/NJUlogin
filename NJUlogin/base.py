import requests
import json
from lxml import etree
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import base64
import os

from .utils import config, get_post, urls


class baseLogin(object):
    def __init__(
        self, headers: dict = config.headers, timeout: int = config.timeout):
        self.session = requests.Session()
        self.session.headers.update(headers)
        self.timeout = timeout

    def get(self, url: str, **kwargs) -> requests.Response:
        return get_post.get(self.session, url, timeout=self.timeout, **kwargs)

    def post(self, url: str, data: dict, **kwargs) -> requests.Response:
        return get_post.post(self.session, url, data, timeout=self.timeout, **kwargs)

    def judge_not_login(self, html: requests.Response, loginurl: str) -> bool:
        """判断是否登录成功"""
        return (
            html is None or html.url == loginurl or html.url.endswith("security_check")
        )

    def logout(self) -> None:
        """退出登录"""
        self.get(urls.logout)

    def logout_all(self) -> None:
        """退出所有设备的登录"""
        html = self.get(urls.onlineList)
        selector = etree.HTML(html.text)
        OnlineList = selector.xpath('//input[@value="踢出"]/@onclick')
        for item in OnlineList:
            tokenId = item.split("'")[1]
            self.post(urls.logoutOthers, data={"tokenId": tokenId})

    @property
    def available(self) -> bool:
        """判断是否登录成功"""
        html = self.get(urls.index)
        return html.url == urls.index

    def export(self, filename: str, password: str = None) -> None:
        """导出登录信息"""
        if not self.available:
            raise ValueError("未登录，无法导出登录信息")
        if password is None:
            with open(filename, "w") as f:
                json.dump(self.session.cookies.get_dict(), f, indent=2)
        else:
            cookies = json.dumps(self.session.cookies.get_dict(), indent=2).encode()
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend(),
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            fernet = Fernet(key)
            enc_cookie = fernet.encrypt(cookies)
            with open(filename, "wb") as f:
                f.write(enc_cookie + salt)

    def load(self, filename: str, password: str = None) -> None:
        """加载登录信息"""
        if password is None:
            try:
                with open(filename, "r") as f:
                    cookies = json.load(f)
            except UnicodeDecodeError:
                raise RuntimeError("请提供密码")
        else:
            with open(filename, "rb") as f:
                enc_cookie = f.read()
            salt = enc_cookie[-16:]
            enc_cookie = enc_cookie[:-16]
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend(),
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            fernet = Fernet(key)
            cookies = json.loads(fernet.decrypt(enc_cookie))
        self.session.cookies.update(cookies)
        if not self.available:
            raise ValueError("登录信息已失效，请重新登录")
