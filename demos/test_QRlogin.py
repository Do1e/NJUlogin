import time, json

import sys
sys.path.append('.')
from NJUlogin import QRlogin

dest = 'https://p.nju.edu.cn:443/api/cas/getinfo/&renew=true'
qrlogin = QRlogin()
session = qrlogin.login(dest)

url = 'https://p.nju.edu.cn/api/portal/v1/getinfo?_=%d' % int(time.time() * 1000)
res = qrlogin.get(url, timeout=5)
# or:
# res = session.get(url, timeout=5)
data = json.loads(res.text)
print('余额: %.2f元' % (data['results']['rows'][0]['balance'] / 100))
qrlogin.logout()
