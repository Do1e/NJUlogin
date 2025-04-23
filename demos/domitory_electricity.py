import sys
sys.path.append('.')
from lxml import etree
from urllib import parse
from NJUlogin import pwdLogin
import getpass

username = input("请输入用户名：")
password = getpass.getpass("请输入密码：")

index_url = "https://epay.nju.edu.cn/epay/h5/nju/electric/edit"
campus_url = "https://epay.nju.edu.cn/epay/h5/getelesys.json"
building_url = "https://epay.nju.edu.cn/epay/h5/getbuild.json"
room_url = "https://epay.nju.edu.cn/epay/h5/getroom.json"
area_url = "https://epay.nju.edu.cn/epay/electric/queryelectricarea"
bill_url = "https://epay.nju.edu.cn/epay/electric/queryelectricbill"
campus_names = ["鼓楼校区", "仙林校区", "苏州校区", "浦口校区"]
UA = 'Mozilla/5.0 (Linux; Android 12; M2007J1SC Build/SKQ1.220303.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/104.0.5112.97 Mobile Safari/537.36 cpdaily/9.0.15 wisedu/9.0.15'

def get_campus_id(pwdsession, token, campus_name):
    response = pwdsession.post(campus_url, data={}, headers=token)
    response = response.json()["list"]
    for item in response:
        if item["elcname"][2:] == '电控' and item["elcname"][:2] == campus_name[:2]:
            campus_id = item["elcsysid"]
            break
    assert campus_id, f"未找到校区id"
    return campus_id

def get_area_id(pwdsession, token, campus_id):
    data = {"sysid": campus_id}
    data = parse.urlencode(data)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Content-Length": str(len(data)),
    }
    headers.update(token)
    response = pwdsession.post(area_url, data=data, headers=headers)
    area_id = response.json()["areas"][0]["areaId"]
    assert area_id, "未找到区域id"
    return area_id

def get_building_list(pwdsession, token, campus_id):
    data = {
        "sysid": campus_id,
        "areaid": 0,
        "districtid": 0,
    }
    data = parse.urlencode(data)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Content-Length": str(len(data)),
    }
    headers.update(token)
    response = pwdsession.post(building_url, data=data, headers=headers)
    response = response.json()["list"]
    building_list = []
    for item in response:
        building_list.append((item["buiId"], item["buiName"]))
    assert building_list, "未找到楼栋信息"
    return building_list

def get_room_list(pwdsession, token, campus_id, building_id):
    data = {
        "sysid": campus_id,
        "areaid": 0,
        "districtid": 0,
        "buildid": building_id,
        "floorid": 0,
    }
    data = parse.urlencode(data)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Content-Length": str(len(data)),
    }
    headers.update(token)
    response = pwdsession.post(room_url, data=data, headers=headers)
    response = response.json()["list"]
    room_list = []
    for item in response:
        room_list.append((item["roomId"], item["roomName"]))
    assert room_list, "未找到宿舍信息"
    return room_list

def get_token(response):
    html = etree.HTML(response.text)
    name = html.xpath('//meta[@name="_csrf_header"]/@content')[0]
    token = html.xpath('//meta[@name="_csrf"]/@content')[0]
    return {name: token}

def electric_func(pwdsession, token, campus_id, area_id, building_id, room_id):
    data = {
        "sysid": campus_id,
        "roomNo": room_id,
        "elcarea": area_id,
        "elcbuis": building_id,
    }
    data = parse.urlencode(data)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Content-Length": str(len(data)),
    }
    headers.update(token)
    response = pwdsession.post(bill_url, data=data, headers=headers)
    return response.json()['restElecDegree']

if __name__ == "__main__":
    try:
        pwdsession = pwdLogin(username, password, headers={"User-Agent": UA})
        pwdsession.login(dest=index_url)
        token = get_token(pwdsession.response)
    except Exception as e:
        print(f"登录失败: {type(e).__name__} {e}")
        exit(1)
    for i, campus_name in enumerate(campus_names):
        print(f"{i + 1}: {campus_name}")
    try:
        campus_name = campus_names[int(input("请选择校区: ")) - 1]
    except:
        print("输入错误")
        exit(1)

    try:
        campus_id = get_campus_id(pwdsession, token, campus_name)
        area_id = get_area_id(pwdsession, token, campus_id)
    except Exception as e:
        print(f"获取校区id失败: {type(e).__name__} {e}")
        exit(1)
    try:
        building_list = get_building_list(pwdsession, token, campus_id)
    except Exception as e:
        print(f"获取楼栋信息失败: {type(e).__name__} {e}")
        exit(1)

    for i, building in enumerate(building_list):
        print(f"{i + 1}: {building[1]}")
    try:
        input_id = input("请选择楼栋: ")
        building_id, building_name = building_list[int(input_id) - 1]
    except:
        print("输入错误")
        exit(1)

    try:
        room_list = get_room_list(pwdsession, token, campus_id, building_id)
    except Exception as e:
        print(f"获取宿舍信息失败: {type(e).__name__} {e}")
        exit(1)

    for i, room in enumerate(room_list):
        if room[1].isdigit():
            print(room[1], end="\t")
        else:
            print(f"{i + 1}: {room[1]}", end="\t")
        print("\n" if (i + 1) % 5 == 0 else "", end="")
    print()
    try:
        input_id = input("请选择宿舍: ")
        if room_list[0][1].isdigit():
            for room in room_list:
                if room[1] == input_id:
                    room_id = room[0]
                    break
            room_id = room_id
            room_name = input_id
        else:
            room_id, room_name = room_list[int(input_id) - 1]
    except:
        print("输入错误")
        exit(1)

    try:
        restElecDegree = electric_func(pwdsession, token, campus_id, area_id, building_id, room_id)
        print(f"宿舍: {campus_name}-{building_name}-{room_name} 剩余电量: {restElecDegree} 度")
    except Exception as e:
        print(f"获取电量失败: {type(e).__name__} {e}")
        exit(1)
