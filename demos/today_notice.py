import sys
sys.path.append('.')
import re
import time
from urllib import parse
from bs4 import BeautifulSoup
from NJUlogin import pwdLogin
from scripts.pwd import *

url = 'https://ehallapp.nju.edu.cn/psfw/sys/tzggapp/bulletin/getAllBulletin.do'
params = {
    'pageNum': '1',
    'pageSize': '50',
    'title': '',
    'deptId': '',
    'startTime': '',
    'endTime': '',
    'DEPT_CODE': None,
    'USER_ID': username,
}
detail_url = 'https://ehallapp.nju.edu.cn/psfw/sys/tzggapp/ggll/loadNoticeDetailInfo.do'
read_url = 'https://ehallapp.nju.edu.cn/psfw/sys/tzggapp/bulletin/addBulletinRead.do'
user_info_url = 'https://ehallapp.nju.edu.cn/psfw/sys/tzggapp/bulletin/getCurrUserInfo.do'
today = time.strftime('%Y-%m-%d', time.localtime(time.time()))

pwdsession = pwdLogin(username, password)
pwdsession.login()

response = pwdsession.post(user_info_url, data='data={}')
params['DEPT_CODE'] = response.json()['deptCode']


response = pwdsession.get(url, params=params)
notices = response.json()['aList']
for notice in notices:
    wid = notice.get('WID', None)
    title = notice.get('TITLE', None)
    go_url = notice.get('GO_URL', None)
    publish_time = notice.get('PUBLISH_TIME', None)
    publisher = notice.get('PUBLISH_USER_DEPT_NAME', None)
    if publish_time[:10] != today:
        continue

    # 添加已读
    data = {'data': {'GGDM': notice['GGDM']}}
    data = parse.urlencode(data)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Content-Length': str(len(data)),
    }
    pwdsession.post(read_url, data=data, headers=headers)

    # 获取详情
    if go_url is None:
        data = {'data': {'GGDM': notice['GGDM'], "NOCOUNT": "1"}}
        data = parse.urlencode(data)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Content-Length': str(len(data)),
        }
        response = pwdsession.post(detail_url, data=data, headers=headers)
        html = response.json()['data']['GG_DATA']['GGNR']
        html = '<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>' + html + '</body></html>'
        full_text = BeautifulSoup(html, 'html.parser').get_text()
        full_text = full_text.replace('\xa0', ' ')
        full_text = re.sub(r' {2,}', '\n', full_text).strip()
    else:
        full_text = '详情请查看: ' + go_url
    print(f'{title}\n发布时间: {publish_time}\n发布人: {publisher}\n{full_text}\n\n\n')
