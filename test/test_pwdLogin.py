import sys

sys.path.append(".")
from NJUlogin import pwdLogin
from scripts.pwd import *


def test_pwdLogin():
    dest = "https://authserver.nju.edu.cn/authserver/index.do"
    pwdlogin = pwdLogin(username, password)
    session = pwdlogin.login(dest)
    assert session is not None
    assert pwdlogin.available
    pwdlogin.logout_all()
    pwdlogin.logout()


if __name__ == "__main__":
    test_pwdLogin()
