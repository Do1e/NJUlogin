import getpass

from NJUlogin import QRlogin, baseLogin, pwdLogin


username = input("请输入用户名：")
password = getpass.getpass("请输入密码：")
pwdlogin = pwdLogin(username, password)
print(pwdlogin.available)
pwdlogin.login()
print(pwdlogin.available)

pwdlogin.export(f'scripts/{username}.json')
del pwdlogin
baselogin = baseLogin()
baselogin.load(f'scripts/{username}.json')
print(baselogin.available)
del baselogin


qrlogin = QRlogin()
print(qrlogin.available)
qrlogin.login()
print(qrlogin.available)

qrlogin.export(f'scripts/{username}.bin', password='123456')
del qrlogin
baselogin = baseLogin()
baselogin.load(f'scripts/{username}.bin', password='123456')
print(baselogin.available)
del baselogin
