import datetime
import re

import pandas as pd
import requests
import toml
from requests.exceptions import ConnectTimeout


class BookStoreInfo:
    def __init__(self, config_path, debug=False):

        self.df4 = None
        self.df1 = None
        self.full_data = None
        self.available_data = None
        self.ruled_appointment = None
        self.config_path = config_path
        self.CONFIG = toml.load(config_path)
        self.debug = debug
        self.refresh_available_info()
        self.getRuledAppointment()

    def makeOneAppointment(self, room_id, start_time, remain_hours):
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        begin_time = str(start_time * 60)
        end_time = str((start_time + remain_hours) * 60)
        ruleId = self.CONFIG['RULE_ID']
        cookies = {
            'JSESSIONID': self.CONFIG["JSESSIONID"],
        }
        referer = f'http://libwx.cau.edu.cn/space/discuss/openAppointDetail?\
                  roomid={room_id}&ustime={begin_time}&uetime={end_time}\
                  &selectDate={today}&ruleId={ruleId}&\
                  mobile=true&linkSign=discuss'
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, '
                          'like Gecko) Version/10.0 Mobile/14E304 Safari/602.1 Edg/95.0.4638.54',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': self.CONFIG['X_CSRF_TOKEN'],
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'http://libwx.cau.edu.cn',
            'Connection': 'keep-alive',
            'Referer': referer,
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
        }
        data = str({
            "_stime": begin_time,
            "_etime": end_time,
            "_roomid": room_id,
            "_currentday": today,
            "UUID": "VEmkgCYM",
            "ruleId": ruleId,
            "users": "2019307070109 2019321010102",
            "usercount": "2",
            "room_exp": "[]",
            "_seatno": "0",
            "LOCK": "true"
        }).replace("'", '"')
        return requests.post('http://libwx.cau.edu.cn/space/form/dynamic/saveFormLock',
                             headers=headers, cookies=cookies, data=data)

    def makeOneSeatEveryAppointment(self, roomId=None, force=False):
        if roomId is None:
            roomId = self.CONFIG['PREFER']
        if force:
            available_period = [[20, 21], [17, 18, 19],
                                [14, 15, 16], [11, 12, 13], [8, 9, 10]]
        else:
            available_period = []
            for hour in range(8, 22):
                if self.full_data.loc[roomId][str(hour)] == 'O':
                    if len(available_period) > 0 and len(available_period[-1]) < 3 \
                            and available_period[-1][-1] == hour - 1:
                        available_period[-1].append(hour)
                    else:
                        available_period.append([hour])
        res_dict = {}
        for available_time_period in available_period:
            res = self.makeOneAppointment(
                roomId, available_time_period[0], len(available_time_period))
            try:
                res_dict[str(available_time_period)] = res.json()
            except Exception as _:
                res_dict[str(available_time_period)] = 'json parse error'
        return res_dict

    def cancelAppointment(self, appoint_id):

        cookies = {
            'JSESSIONID': self.CONFIG["JSESSIONID"],
        }
        headers = {
            'Proxy-Connection': 'keep-alive',
            'Accept': '*/*',
            'DNT': '1',
            'X-CSRF-TOKEN': self.CONFIG['X_CSRF_TOKEN'],
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0.1; Moto G (4)) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/95.0.4638.54 Mobile Safari/537.36 Edg/95.0.1020.40',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'http://libwx.cau.edu.cn',
            'Referer': 'http://libwx.cau.edu.cn/space/discuss/myAppoint?linkSign=myReserve&type=discuss',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        }
        data = {
            'id': appoint_id
        }
        response = requests.post(
            'http://libwx.cau.edu.cn/space/discuss/cancleAppiont',
            headers=headers,
            cookies=cookies,
            data=data,
            verify=False
        )
        return response

    def getAppointmentRecords(self, ):
        cookies = {
            'JSESSIONID': self.CONFIG['JSESSIONID'],
        }

        headers = {
            'Proxy-Connection': 'keep-alive',
            'Accept': '*/*',
            'DNT': '1',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0.1; Moto G (4)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Mobile Safari/537.36 Edg/95.0.1020.40',
            'Referer': 'http://libwx.cau.edu.cn/space/discuss/myAppoint?linkSign=myReserve&type=discuss',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        }

        params = (
            ('cday', '1970-01-01_to_2050-01-01'),
            ('sign', ''),
            ('rtypeid', ''),
            ('type', 'discuss'),
        )

        response = requests.get('http://libwx.cau.edu.cn/space/discuss/queryAppiont',
                                headers=headers, params=params, cookies=cookies, verify=False)
        res = pd.DataFrame(response.json()["params"]["myappionts"]["pageList"])
        del res['uid']
        del res['pay']
        del res['title']
        return res

    def getRuledAppointment(self):
        import pandas as pd
        import numpy as np
        ap = self.getAppointmentRecords()
        ap = ap[ap['sign'] == False]
        ap['begintime'] = pd.to_datetime(ap['currentday'] + ' ' + ap['stime'])
        ap = ap[['id', 'begintime', 'etime', 'rname', 'status', 'flag', 'cstatus']]
        ap.sort_values(by='begintime', inplace=True, ascending=False)
        now_pd = pd.to_datetime(datetime.datetime.now())
        ap = ap[ap['begintime'] > now_pd]
        ap = ap[ap['cstatus'] == 0.0]
        self.ruled_appointment = ap
        return ap

    def request_with_cookies(self, sec, day=""):
        req_address = 'http://libwx.cau.edu.cn/space/discuss/findRoom'
        sec_list = ['', '0a4c97c5b7844420abdc7128715b8885',
                    '', '', '31df48baed5148a5ae4eb219cdd1e415']
        Section = sec_list[int(sec)]

        unknown = '57879bf578f24a43bae98434682bf176'
        if day == "":
            day = datetime.datetime.now().strftime('%Y-%m-%d')
        url = f"{req_address}/{Section}/{unknown}/{day}"
        try:
            res = requests.post(
                url=url,
                headers={
                    "X-CSRF-TOKEN": self.CONFIG['X_CSRF_TOKEN'],
                    "Cookie": f"JSESSIONID={self.CONFIG['JSESSIONID']}"
                },
                data={
                    "currentPage": 1,
                    "pageSize": 100
                },
                timeout=5.0
            ).json()
            df = pd.DataFrame(res["params"]["rooms"]["pageList"])
            ruleId = res["params"]["ruleId"]
            return True, df, ruleId

        except ConnectTimeout as _:
            print("[ERROR] NetWork Error! Please Check Connections Between Host and Server!")
            exit(0)
        except Exception as e:
            print(e)
            print(type(e))
            return False, None, None

    def write_toml(self):
        with open(self.config_path, "w") as f:
            toml.dump(self.CONFIG, f)

    def get_origin_info(self, sec='4'):
        checker, df, ruleId = self.request_with_cookies(sec)

        if not checker:
            # print("[INFO] Get New Cookies!")
            jsessionid, x_csrf_token = self.get_new_cookies()
            self.CONFIG["JSESSIONID"], self.CONFIG["X_CSRF_TOKEN"] = jsessionid, x_csrf_token
            self.write_toml()
            checker, df, ruleId = self.request_with_cookies(sec)
        self.CONFIG['RULE_ID'] = ruleId
        self.write_toml()
        df["times"] = df["times"].map(lambda x: "".join(
            [str('X' if line["select"] else 'O') for line in x]))
        df_n = df[["id", "rname", "times"]]
        return df_n

    def refresh_available_info(self):
        self.df1 = self.get_origin_info('1')
        self.df4 = self.get_origin_info('4')
        self.df = pd.DataFrame(pd.concat([self.df1, self.df4], axis=0))
        self.full_data = self.deal_available_info(self.df.copy())
        self.full_data.to_csv("full_data.csv")
        self.available_data = self.deal_available_info(
            self.df.copy(), available_filter=True)

    def deal_available_info(self, df, available_filter=False):
        if available_filter:
            hour_now = datetime.datetime.now().hour
            if datetime.datetime.now().minute > 30:
                hour_now += 1
            # print(f'{hour_now = }')
            unavailable_suffix = 'X' * max(22 - hour_now, 0)
            res = []
            for index, data in df.iterrows():
                if data['times'].endswith(unavailable_suffix):
                    continue
                res.append(data)
            df = pd.DataFrame(res, columns=df.columns)
        # print(df, "cur")
        df['avai'] = df['times'].map(lambda x: x.count('O'))
        df.index = df['id']
        del df['id']
        for i in range(14):
            df[f"{8 + i}"] = df['times'].map(lambda x: x[i])
        df = df.sort_values(by='avai', ascending=False)
        return df

    def sign(self, sign_config='SIGN_PARAM', roomId=None):
        if roomId is None:
            if len(self.ruled_appointment) == 0:
                return "No Appoint at that time!"
            roomName = self.ruled_appointment['rname'].values[-1]
            roomId = self.full_data[self.full_data['rname'] == roomName].index.values[-1]
        headers = {
            'Proxy-Connection': 'keep-alive',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0.1; Moto G (4)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Mobile Safari/537.36 Edg/95.0.1020.40',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        }

        params = self.CONFIG[sign_config]
        params['roomId'] = roomId

        response = requests.get('http://libwx.cau.edu.cn/space/static/cau/mediaCheckIn', headers=headers, params=params,
                                verify=False)
        res = re.search("<span>(.*)</span>", response.text).group(1)
        if res == (b'\xe5\xbd\x93\xe5\x89\x8d\xe9\xa2\x84\xe7\xba\xa6\xe5\xb7\xb2\xe7\xad\xbe\xe5\x88\xb0').decode(
                'utf-8'):
            res = "Already!"
        return res

    def get_new_cookies(self):
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
            ('openid', self.CONFIG["OPEN_ID"]),
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
        X_CSRF_TOKEN = re.search(
            r'name="_csrf" content="(?P<CUR>.*)"', response.text).groupdict()['CUR']
        return [JSESSIONID, X_CSRF_TOKEN]


def desensitize(data: pd.DataFrame):
    data['rname'] = data['rname'].map(lambda x: x.replace(
        '层', '-').replace(b'\xe5\x8c\xba\xe4\xba\xa4\xe6\xb5\x81\xe7\xa9\xba\xe9\x97\xb4'.decode('utf-8'), '-').replace(
        '排', '-').replace('组', ''))
    if 'times' in data.columns:
        del data['times']
    return data


def dprint(data):
    print(desensitize(data.copy()))
