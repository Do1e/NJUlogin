import sys
sys.path.append('.')
from NJUlogin import pwdLogin
import getpass

username = input("请输入用户名：")
password = getpass.getpass("请输入密码：")

dest = 'https://authserver.nju.edu.cn/authserver/index.do'
pwdlogin = pwdLogin(username, password)
session = pwdlogin.login(dest)
pwdlogin.logout_all()
pwdlogin.logout()
