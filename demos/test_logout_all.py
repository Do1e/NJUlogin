import getpass

from NJUlogin import pwdLogin


username = input("请输入用户名：")
password = getpass.getpass("请输入密码：")

dest = 'https://authserver.nju.edu.cn/authserver/index.do'
pwdlogin = pwdLogin(username, password)
session = pwdlogin.login(dest)
pwdlogin.logout_all()
pwdlogin.logout()
