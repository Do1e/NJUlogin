from NJUlogin import pwdLogin

dest = 'https://authserver.nju.edu.cn/authserver/index.do'
pwdlogin = pwdLogin('XXXXXXXXXX', 'XXXXXXXXXX')
session = pwdlogin.login(dest)
pwdlogin.logout_all()
pwdlogin.logout()