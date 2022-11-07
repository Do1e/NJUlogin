import time, json
from NJUlogin.QRlogin import QRlogin

dest = 'http://p.nju.edu.cn/cas/&renew=true'
# or:
# dest = 'http%3A%2F%2Fp.nju.edu.cn%2Fcas%2F&renew=true'
qrlogin = QRlogin()
session = qrlogin.login(dest)

url = 'http://p.nju.edu.cn/api/portal/v1/getinfo?_=%d' % int(time.time() * 1000)
res = qrlogin.get(url, timeout=5)
# or:
# res = session.get(url, timeout=5)
data = json.loads(res.text)
print('余额: %.2f元' % (data['results']['rows'][0]['balance'] / 100))