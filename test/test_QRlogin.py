import sys

sys.path.append(".")
from NJUlogin import QRlogin


def test_QRlogin():
    dest = "https://authserver.nju.edu.cn/authserver/index.do"
    qrlogin = QRlogin()
    session = qrlogin.login(dest)
    assert session is not None
    assert qrlogin.available
    qrlogin.logout_all()
    qrlogin.logout()


if __name__ == "__main__":
    test_QRlogin()
