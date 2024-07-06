import sys
sys.path.append('.')
from NJUlogin import pwdLogin, QRlogin, baseLogin
from scripts.pwd import *

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
