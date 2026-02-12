import time

import requests
from lxml import etree
from qrcode import QRCode

from .base import baseLogin
from .utils import config, get_post, urls


class QR(object):
    def __init__(self, session: requests.Session, timeout: int):
        self.session = session
        self.timeout = timeout

    def getQR(self) -> str:
        """获取二维码URL"""
        self.ts = int(time.time() * 1000)
        url = urls.QRid % self.ts
        QRid = get_post.get(self.session, url, timeout=self.timeout,
                            params={"uuid": ""}).text
        self.QRid = QRid
        return urls.QRurl % QRid

    def printQR(self):
        """打印二维码至终端"""
        QRurl = self.getQR()
        qr = QRCode(border=1, box_size=10)
        qr.add_data(QRurl)
        try:
            qr.print_ascii(invert=True, tty=True)
        except OSError:
            qr.print_ascii(invert=True, tty=False)
            print("如果无法扫描二维码，请更改终端字体，如 Maple Mono、Fira Code 等。")
        print(f"微信或南京大学APP扫码登录。若无法扫描二维码，请访问以下链接获取二维码图片：\n{urls.QRimg % self.QRid}")


class QRlogin(baseLogin):
    def __init__(self, loginTimeout: int = config.loginTimeout, *args, **kwargs):
        """二维码登录"""
        super().__init__(*args, **kwargs)
        self.loginTimeout = loginTimeout

    def getStatus(self, qr: QR) -> str:
        """等候扫码，返回扫码状态"""
        url = urls.status % int(time.time() * 1000)
        status = self.get(url, params={"uuid": qr.QRid}).text
        return status

    def waitingLogin(self, qr: QR) -> bool:
        """等候登录，返回登录状态"""
        # 0: 未扫码, 1: 登录成功, 2: 已扫码未确认登录, 3: 二维码失效
        first2 = False
        for _ in range(self.loginTimeout):
            status = self.getStatus(qr)
            try:
                status = int(status)
                if status not in [0, 1, 2, 3]:
                    raise ValueError
            except ValueError:
                raise ValueError("未知状态，代码可能需要维护")
            if status == 2 and not first2:
                print("扫描成功，请在手机上『确认登录』")
                first2 = True
            elif status == 1:
                return True
            elif status == 3:
                print("二维码已失效")
                return False
            time.sleep(1)
        print("登录超时")
        return False

    def login(self, dest: str = None) -> requests.Session:
        if dest is not None:
            url = urls.login % dest
        else:
            url = urls.login.split("?")[0]
        html = self.get(url).text
        qr = QR(self.session, self.timeout)
        qr.printQR()
        if not self.waitingLogin(qr):
            return None

        selector = etree.HTML(html)
        def get_field(name):
            vals = selector.xpath(f'//input[@name="{name}"]/@value')
            return vals[0] if vals else ""

        data = {
            "lt": get_field("lt"),
            "uuid": qr.QRid,
            "cllt": "qrLogin",
            "dllt": get_field("dllt"),
            "execution": get_field("execution"),
            "_eventId": get_field("_eventId"),
            "rmShown": get_field("rmShown"),
        }
        res = self.post(url, data=data)
        if self.judge_not_login(res, url):
            print("登录失败")
            return None
        self.response = res
        return self.session
