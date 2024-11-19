import sys

sys.path.append(".")
from NJUlogin import pwdLogin, QRlogin, baseLogin
from scripts.pwd import *


def test_export_load():
    pwdlogin = pwdLogin(username, password)
    assert not pwdlogin.available
    pwdlogin.login()
    assert pwdlogin.available

    pwdlogin.export(f"scripts/{username}.json")
    del pwdlogin
    baselogin = baseLogin()
    baselogin.load(f"scripts/{username}.json")
    assert baselogin.available
    del baselogin

    qrlogin = QRlogin()
    assert not qrlogin.available
    qrlogin.login()
    assert qrlogin.available

    qrlogin.export(f"scripts/{username}.bin", password="123456")
    del qrlogin
    baselogin = baseLogin()
    baselogin.load(f"scripts/{username}.bin", password="123456")
    assert baselogin.available
    del baselogin


if __name__ == "__main__":
    test_export_load()
