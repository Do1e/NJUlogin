import requests

from .utils import config, get_post, urls

class baseLogin(object):
    def __init__(self, headers: dict = config.headers):
        self.session = requests.Session()
        self.session.headers.update(headers)

    def get(self, url: str, **kwargs) -> requests.Response:
        return get_post.get(self.session, url, **kwargs)

    def post(self, url: str, data: dict, **kwargs) -> requests.Response:
        return get_post.post(self.session, url, data, **kwargs)

    def logout(self) -> None:
        """退出登录"""
        self.get(urls.logout, timeout=self.getTimeout)
