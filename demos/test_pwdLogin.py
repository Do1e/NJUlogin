import getpass
import json
import time

from NJUlogin import pwdLogin


username = input("请输入用户名：")
password = getpass.getpass("请输入密码：")

dest = 'https://p.nju.edu.cn:443/api/cas/getinfo/&renew=true'

pwdlogin = pwdLogin(username, password)
session = pwdlogin.login(dest)

url = 'https://p.nju.edu.cn/api/portal/v1/getinfo?_=%d' % int(time.time() * 1000)
res = pwdlogin.get(url)
# or:
# res = session.get(url, timeout=5)
data = json.loads(res.text)
print('余额: %.2f元' % (data['results']['rows'][0]['balance'] / 100))
pwdlogin.logout()
