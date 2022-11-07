import time, json
from NJUlogin import pwdLogin

dest = 'http://p.nju.edu.cn/cas/&renew=true'
# or:
# dest = 'http%3A%2F%2Fp.nju.edu.cn%2Fcas%2F&renew=true'

mobile_headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 12; M2007J1SC Build/SKQ1.220303.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/104.0.5112.97 Mobile Safari/537.36 cpdaily/9.0.15 wisedu/9.0.15'
}
pwdlogin = pwdLogin('XXXXXXXXX', 'XXXXXXXXX')
# or:
# pwdlogin = pwdLogin('XXXXXXXXX', 'XXXXXXXXX', mobileLogin=True, headers=mobile_headers)
session = pwdlogin.login(dest)

url = 'http://p.nju.edu.cn/api/portal/v1/getinfo?_=%d' % int(time.time() * 1000)
res = pwdlogin.get(url, timeout=5)
# or:
# res = session.get(url, timeout=5)
data = json.loads(res.text)
print('余额: %.2f元' % (data['results']['rows'][0]['balance'] / 100))