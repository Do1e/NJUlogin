import sys
sys.path.append('.')
from NJUlogin import pwdLogin
from scripts.pwd import *

dest = 'https://authserver.nju.edu.cn/authserver/index.do'
pwdlogin = pwdLogin(username, password)
session = pwdlogin.login(dest)
pwdlogin.logout_all()
pwdlogin.logout()
