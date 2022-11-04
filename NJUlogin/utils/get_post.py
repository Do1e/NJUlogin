import requests

from . import config

def get(session: requests.Session, url: str) -> requests.Response:
    try:
        return session.get(url, **config.getkwargs)
    except requests.exceptions.Timeout:
        raise TimeoutError('请求网页"%s"超时' % url)

def post(session: requests.Session, url: str, data: dict) -> requests.Response:
    try:
        return session.post(url, data=data, **config.getkwargs)
    except requests.exceptions.Timeout:
        raise TimeoutError('向网页"%s"提交数据超时' % url)
