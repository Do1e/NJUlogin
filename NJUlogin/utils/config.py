import urllib3
urllib3.disable_warnings()

getTimeout = 2
loginTimeout = 60
getkwargs = {'timeout': getTimeout, 'verify': False}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.53',
}
