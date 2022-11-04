import requests

from . import config

def get(session: requests.Session, url: str) -> requests.Response:
    try:
        return session.get(url, **config.getkwargs)
    except requests.exceptions.Timeout:
        raise TimeoutError('请求网页"%s"超时' % url)
    except requests.exceptions.ConnectionError:
        raise ConnectionError('请求网页"%s"时发生连接错误，请检查网络连接' % url)

def post(session: requests.Session, url: str, data: dict) -> requests.Response:
    try:
        return session.post(url, data=data, **config.getkwargs)
    except requests.exceptions.Timeout:
        raise TimeoutError('向网页"%s"提交数据超时' % url)
    except requests.exceptions.ConnectionError:
        raise ConnectionError('向网页"%s"提交数据时发生连接错误，请检查网络连接' % url)
