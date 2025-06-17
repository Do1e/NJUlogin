import requests
import numpy as np
import time
from PIL import Image
from io import BytesIO
import os
from lxml import etree

from .utils import config, urls, get_post
from .base import baseLogin


class QR(object):
    def __init__(self, session: requests.Session, timeout: int):
        self.session = session
        self.timeout = timeout

    def getQR(self) -> np.ndarray:
        """获取二维码图片，返回numpy数组"""
        self.ts = int(time.time() * 1000)
        url = urls.QRid % self.ts
        QRid = get_post.get(self.session, url, timeout=self.timeout).text
        self.QRid = QRid
        url = urls.QRimg % QRid
        QRdata = get_post.get(self.session, url, timeout=self.timeout).content
        qr = Image.open(BytesIO(QRdata)).convert("L")
        return np.array(qr)[6:-6, 6:-6]

    def printQR(self):
        """打印二维码至终端，同时也会保存一份QR.png到当前目录"""
        QRimg = self.getQR()
        Image.fromarray(QRimg).save("QR.png")
        char_full = "\u2588"
        char_up = "\u2580"
        char_down = "\u2584"
        for i in range(0, QRimg.shape[0] - 3, 6):
            for j in range(0, QRimg.shape[1], 3):
                if QRimg[i, j] < 128 and QRimg[i + 3, j] < 128:
                    print(char_full, end="")
                elif QRimg[i, j] < 128 and QRimg[i + 3, j] >= 128:
                    print(char_up, end="")
                elif QRimg[i, j] >= 128 and QRimg[i + 3, j] < 128:
                    print(char_down, end="")
                else:
                    print(" ", end="")
            print("")
        for j in range(0, QRimg.shape[1], 3):
            if QRimg[-1, j] < 128:
                print(char_up, end="")
            else:
                print(" ", end="")
        print("")

    def __del__(self):
        """清理二维码图片"""
        if os.path.exists("QR.png"):
            os.remove("QR.png")

class QRlogin(baseLogin):
    def __init__(self, loginTimeout: int = config.loginTimeout, *args, **kwargs):
        """二维码登录"""
        super().__init__(*args, **kwargs)
        self.loginTimeout = loginTimeout

    def getStatus(self, qr: QR) -> str:
        """等候扫码，返回扫码状态"""
        url = urls.status % (qr.ts, qr.QRid)
        status = self.get(url).text
        return status

    def waitingLogin(self, qr: QR) -> bool:
        """等候登录，返回登录状态"""
        # 0: 未扫码, 1: 登录成功, 2: 已扫码未确认登录
        first0, first2 = False, False
        for _ in range(self.loginTimeout):
            status = self.getStatus(qr)
            try:
                status = int(status)
                if status not in [0, 1, 2]:
                    raise ValueError
            except ValueError:
                raise ValueError("未知状态，代码可能需要维护")
            if status == 0 and not first0:
                print("微信或南京大学APP扫码登录")
                first0 = True
            elif status == 2 and not first2:
                print("扫描成功，请在手机上『确认登录』")
                first2 = True
            elif status == 1:
                return True
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
        data = {
            "lt": selector.xpath('//input[@name="lt"]/@value')[1],
            "uuid": qr.QRid,
            "dllt": selector.xpath('//input[@name="dllt"]/@value')[1],
            "execution": selector.xpath('//input[@name="execution"]/@value')[1],
            "_eventId": selector.xpath('//input[@name="_eventId"]/@value')[1],
            "rmShown": selector.xpath('//input[@name="rmShown"]/@value')[1],
        }
        res = self.post(url, data=data)
        if self.judge_not_login(res, url):
            print("登录失败")
            return None
        self.response = res
        return self.session
