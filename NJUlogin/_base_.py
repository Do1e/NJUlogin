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

    def judge_not_login(self, html: requests.Response, loginurl: str) -> bool:
        """判断是否登录成功"""
        return html is None or html.url == loginurl

    def logout(self) -> None:
        """退出登录"""
        self.get(urls.logout, timeout=self.getTimeout)

    def logout_all(self) -> None:
        """退出所有设备的登录"""
        from lxml import etree
        html = self.get(urls.onlineList, timeout=self.getTimeout)
        selector = etree.HTML(html.text)
        OnlineList = selector.xpath('//input[@value="踢出"]/@onclick')
        for item in OnlineList:
            tokenId = item.split("'")[1]
            self.post(urls.logoutOthers, data={'tokenId': tokenId})
