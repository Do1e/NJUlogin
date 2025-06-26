import argparse
import getpass
import json
import time
import requests
from lxml import etree

from .pwdLogin import pwdLogin
from .QRlogin import QRlogin
from .utils import config

destURL = 'https://p.nju.edu.cn:443/api/cas/getinfo/&renew=true'
testURL = 'https://ipapi.do1e.cn/'
logoutURL = 'https://p.nju.edu.cn/api/portal/v1/logout'
kickURL = 'https://p.nju.edu.cn/api/selfservice/v1/online/kick/%d'
userInfoURL = 'https://p.nju.edu.cn/api/portal/v1/getinfo?_=%d'
idURL = 'https://p.nju.edu.cn/api/selfservice/v1/userinfo?_=%d'
useTimeURL = 'https://p.nju.edu.cn/api/selfservice/v1/volume/%02d/%d?_=%d'
onLineURL = 'https://p.nju.edu.cn/api/selfservice/v1/online?page=1&limit=10000&_=%d'
quickLoginURL = 'https://p.nju.edu.cn/api/portal/v1/quicklogin/domain/default?_=%d'
bindURL = 'https://p.nju.edu.cn/api/portal/v1/quicklogin/bind/default'
unbindURL = 'https://p.nju.edu.cn/api/portal/v1/quicklogin/unbind/id/%d'

def init_session():
    """初始化requests会话"""
    session = requests.Session()
    session.headers.update(config.headers)
    return session

def get_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--loginlib', type=str, metavar='loginlib', default='QRlogin', help='登录库，QRlogin或pwdLogin，默认为QRlogin')
    parser.add_argument('-i', '--login', action='store_true', default=False, help='登录')
    parser.add_argument('-o', '--logout', action='store_true', default=False, help='登出')
    parser.add_argument('-k', '--kick', type=int, metavar='online_id', help='登出指定在线设备，使用`-p`可获取online_id')
    parser.add_argument('-p', '--printinfo', action='store_true', default=False, help='打印信息')
    parser.add_argument('-a', '--add', type=str, metavar='name', help='添加当前设备为无感认证设备，name为设备名称')
    parser.add_argument('-d', '--delete', type=int, metavar='device_id', help='删除无感认证设备，指定设备ID，使用`-p`可获取device_id')
    return parser.parse_args()

def judge_args(args: argparse.Namespace):
    """判断命令行参数是否正确"""
    if not (args.login or args.logout or args.kick or args.printinfo or args.add or args.delete):
        raise ValueError('缺少必要操作参数，请使用 --login, --logout, --kick, --printinfo, --add, --delete 选项')
    if args.login and args.logout:
        raise ValueError('不能同时使用 --login 和 --logout 选项')

def is_logined() -> bool:
    session = init_session()
    try:
        res = session.get(testURL, timeout=2, verify=False)
        if res:
            return True
        else:
            return False
    except Exception:
        return False

def logout():
    session = init_session()
    try:
        res = session.post(logoutURL, data='{"domain":"default"}')
        data = json.loads(res.text)
        assert data['reply_code'] == 0
        print('已退出')
    except Exception:
        print('登出失败')

def kick(online_id: int):
    session = init_session()
    try:
        res = session.post(kickURL % online_id)
        data = json.loads(res.text)
        if data['reply_code'] == 0:
            print(f'已踢出在线设备 {online_id}')
        else:
            print(f'踢出在线设备 {online_id} 失败: {data["reply_msg"]}')
    except Exception as e:
        print('踢出在线设备失败:', str(e))

def _print_user_info():
    session = init_session()
    try:
        res = session.get(userInfoURL % int(time.time() * 1000), timeout=2)
        if res.status_code == 200:
            data = json.loads(res.text)
            if data['reply_code'] != 0:
                print('获取用户信息失败:', data['reply_msg'])
                return
            print(data['results']['rows'][0]['username'], end=' ')
            print(data['results']['rows'][0]['fullname'])
            print('余额: %.2f元' % (data['results']['rows'][0]['balance'] / 100))
        else:
            print('获取用户信息失败，状态码:', res.status_code)
    except Exception as e:
        print('获取用户信息失败:', str(e))

def _print_used_time():
    session = init_session()
    try:
        res = session.get(idURL % int(time.time() * 1000), timeout=2)
        if res.status_code == 200:
            data = json.loads(res.text)
            if data['reply_code'] != 0:
                print('获取用户信息失败:', data['reply_msg'])
                return
            service_id = data['results']['service'][0]['id']
            name = data['results']['service'][0]['name']
            description = data['results']['service'][0]['description']
        else:
            print('获取service_id失败，状态码:', res.status_code)
            return
    except Exception as e:
        print('获取service_id失败:', str(e))
        return

    print(f'{name} ({service_id})\n{description}')
    month = int(time.strftime('%m', time.localtime()))
    ts = int(time.time() * 1000)
    try:
        res = session.get(useTimeURL % (month, service_id, ts), timeout=2)
        if res.status_code == 200:
            data = json.loads(res.text)
            if data['reply_code'] != 0:
                print('获取已用时长失败:', data['reply_msg'])
                return
            used_time = data['results']['use_volume'] // 60
            hours, minutes = divmod(used_time, 60)
            print(f'已结算时长: {hours}小时{minutes}分钟')
        else:
            print('获取已用时长失败，状态码:', res.status_code)
    except Exception as e:
        print('获取已用时长失败:', str(e))

def _print_online_list():
    def int2ipv4(ip: int) -> str:
        l = [ip >> 24 & 0xff, ip >> 16 & 0xff, ip >> 8 & 0xff, ip & 0xff]
        return '.'.join([str(i) for i in l])

    session = init_session()
    ts = int(time.time() * 1000)
    try:
        res = session.get(onLineURL % ts, timeout=2)
        if res.status_code == 200:
            data = json.loads(res.text)
            online_users = data['results']['rows']
            print(f'在线设备: {len(online_users)}个')
            col_names = {
                'id': 10,
                'login_time': 20,
                'MAC addr': 18,
                'IPv4 addr': 16,
                'IPv6 addr': 0,
            }
            print(' '.join([f'{name:<{col_names[name]}}' for name in col_names.keys()]))
            for user in online_users:
                user_id = user['id']
                login_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(user['acctstarttime']))
                mac_addr = user['mac']
                ipv4_addr = int2ipv4(user['user_ipv4'])
                ipv6_addr = user['user_ipv6'] if user['user_ipv6'] else ''
                print(f'{user_id:<{col_names["id"]}} {login_time:<{col_names["login_time"]}} {mac_addr:<{col_names["MAC addr"]}} {ipv4_addr:<{col_names["IPv4 addr"]}} {ipv6_addr}')
        else:
            print('获取在线设备列表失败，状态码:', res.status_code)
    except Exception as e:
        print('获取在线设备列表失败:', str(e))

def _print_quick_login_list():
    session = init_session()
    ts = int(time.time() * 1000)
    try:
        res = session.get(quickLoginURL % ts, timeout=2)
        if res.status_code == 200:
            data = json.loads(res.text)
            if data['reply_code'] == 404:
                print('没有启用无感认证的设备')
                return
            if data['reply_code'] != 0:
                print('获取无感认证设备列表失败:', data['reply_msg'])
                return
            quick_logins = data['results']['rows']
            print(f'无感认证设备: {len(quick_logins)}个')
            col_names = {
                'MAC addr': 18,
                'device id': 15,
                'device name': 0,
            }
            print(' '.join([f'{name:<{col_names[name]}}' for name in col_names.keys()]))
            for login in quick_logins:
                mac_addr = login['mac']
                device_id = login['id']
                device_name = login['device']
                print(f'{mac_addr:<{col_names["MAC addr"]}} {device_id:<{col_names["device id"]}} {device_name}')
        else:
            print('获取无感认证设备列表失败，状态码:', res.status_code)
    except Exception as e:
        print('获取无感认证设备列表失败:', str(e))

def print_info():
    _print_user_info()
    _print_used_time()
    print()
    _print_online_list()
    print()
    _print_quick_login_list()

def add_quick_login(name: str):
    session = init_session()
    data = ('{"device":"%s"}' % name).encode('utf-8')
    try:
        res = session.post(bindURL, data=data, timeout=2)
        data = json.loads(res.text)
        assert data['reply_code'] == 0, data['reply_msg']
        print(f'已启用设备 {name} 的无感认证')
    except Exception as e:
        print(f'启用设备 {name} 的无感认证失败:', str(e))

def del_quick_login(device_id: int):
    session = init_session()
    try:
        res = session.post(unbindURL % device_id, timeout=2)
        data = json.loads(res.text)
        assert data['reply_code'] == 0, data['reply_msg']
        print(f'已删除设备 {device_id} 的无感认证')
    except Exception as e:
        print(f'删除设备 {device_id} 的无感认证失败:', str(e))

def main():
    args = get_args()
    judge_args(args)
    if args.loginlib == 'QRlogin':
        loginlib = QRlogin()
    elif args.loginlib == 'pwdLogin':
        username = input('请输入用户名: ').strip()
        password = getpass.getpass('请输入密码: ').strip()
        loginlib = pwdLogin(username, password)
    else:
        raise ValueError('不支持的登录库，请选择 QRlogin 或 pwdLogin')

    if args.login:
        session = loginlib.login(destURL)
        html = etree.HTML(loginlib.response.text)
        if html.xpath('//h2/text()'):
            print(html.xpath('//h2/text()')[0])
            exit(1)
        if session is None:
            raise RuntimeError('Login failed')

    if args.printinfo:
        isLogin = is_logined()
        if not isLogin:
            session = loginlib.login(destURL)
            if session is None:
                raise RuntimeError('Login failed')
        print_info()
        if not isLogin:
            logout()

    if args.kick is not None:
        isLogin = is_logined()
        if not isLogin:
            session = loginlib.login(destURL)
            if session is None:
                raise RuntimeError('Login failed')
        kick(args.kick)
        if not isLogin:
            logout()

    if args.add:
        isLogin = is_logined()
        if not isLogin:
            session = loginlib.login(destURL)
            if session is None:
                raise RuntimeError('Login failed')
        add_quick_login(args.add)
        if not isLogin:
            logout()

    if args.delete is not None:
        isLogin = is_logined()
        if not isLogin:
            session = loginlib.login(destURL)
            if session is None:
                raise RuntimeError('Login failed')
        del_quick_login(args.delete)
        if not isLogin:
            logout()

    if args.logout:
        logout()

    loginlib.logout()

if __name__ == '__main__':
    main()
