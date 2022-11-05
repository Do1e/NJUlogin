from NJUlogin.pwdLogin import pwdLogin

dest = 'http://p.nju.edu.cn/cas/&renew=true'
# or:
# dest = 'http%3A%2F%2Fp.nju.edu.cn%2Fcas%2F&renew=true'
pwdlogin = pwdLogin('XXXXXXXXX', 'XXXXXXXXX')
session = pwdlogin.login(dest)
