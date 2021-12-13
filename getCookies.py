import requests
import re

def get_new_cookies(open_id):
    return get_new_cookies_new(open_id)

def get_new_cookies_new(open_id):
    common_headers = {
        'Connection': 'keep-alive',
        'DNT': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Cache-Control': 'max-age=0',

    }

    params = (
        ('parameter', '1'),
        ('openid', open_id),
    )

    response = requests.get('http://libwx.cau.edu.cn/remote/static/authIndex',
                            headers=common_headers, params=params, verify=False)
    url_suffix = re.search(
        r'window.location.href = urls \+ "(?P<CUR>.*);', response.text).groupdict()['CUR']

    headers = {
        **common_headers,
        'Referer': 'http://libwx.cau.edu.cn/remote/static/authIndex?parameter=1&openid=oJ7t-1fCfr-FokhmYcI5QerAJIxo',
    }
    response = requests.get('http://libwx.cau.edu.cn/space/static/dowechatlogin?type=discuss' +
                            url_suffix, headers=headers, verify=False, allow_redirects=False)
    JSESSIONID = re.search(r'JSESSIONID=(?P<CUR>.*); Path',
                           response.headers['Set-Cookie']).groupdict()['CUR']

    cookies = {
        'JSESSIONID': JSESSIONID,
    }

    headers = {
        **common_headers,
        'Referer': 'http://libwx.cau.edu.cn/space/discuss/notice?linkSign=notice&type=discuss&noticeId=7f35dde178074b17bc547ba78160930c',
    }

    params = (
        ('linkSign', 'discuss'),
        ('type', 'discuss'),
    )

    response = requests.get('http://libwx.cau.edu.cn/space/discuss/mobileIndex',
                            headers=headers, params=params, cookies=cookies, verify=False)
    # print(response.text)
    X_CSRF_TOKEN = re.search(
        r'name="_csrf" content="(?P<CUR>.*)"', response.text).groupdict()['CUR']
    # print(X_CSRF_TOKEN)
    return [JSESSIONID, X_CSRF_TOKEN]
