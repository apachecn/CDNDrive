# coding: utf-8
import re
from CDNDrive.util import *
from .BaseApi import BaseApi


class ChaoXingApi(BaseApi):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/84.0.4147.125 Safari/537.36'
    }
    default_url = lambda self, obj_id: f"http://p.ananas.chaoxing.com/star3/origin/{obj_id}.png"
    extract_obj_id = lambda self, s: re.findall(r"[a-fA-F0-9]{32}", s)[0]
    get_cookies = lambda self: self.cookies

    def __init__(self):
        super().__init__()
        self.cookies = load_cookies('chaoxing')

    def meta2real(self, url):
        if re.match(r"^cxdrive://[a-fA-F0-9]{32}$", url):
            return self.default_url(self.extract_obj_id(url))
        else:
            return None

    def real2meta(self, url):
        if re.match(r"^http://p.ananas.chaoxing.com/star3/origin/[a-fA-F0-9]{32}.png$", url):
            return "cxdrive://" + self.extract_obj_id(url)
        else:
            return None

    def set_cookies(self, cookie_str):
        self.cookies = parse_cookies(cookie_str)
        save_cookies('chaoxing', self.cookies)

    def login(self, username, password):
        headers = ChaoXingApi.headers.copy()
        login_api = "https://passport2.chaoxing.com/api/login"
        params = {
            "name": username,
            "pwd": password,
            "verify": "0",
            "schoolid": ''
        }
        resp = request_retry(
            "get", login_api, params=params,
            headers=headers,
            cookies=self.cookies
        )
        if resp.status_code == 403:
            result = f"{username}登录得到403，登录请求被拒绝"
            return {'code': 114514, 'message': result}

        data = json.loads(resp.text)
        if not data['result']:
            result = f'{username}登录失败'
            return {'code': 114514, 'message': result}

        self.cookies = resp.cookies.get_dict()
        save_cookies('chaoxing', self.cookies)
        return {'code': 0, 'message': '登录成功'}

    def get_user_info(self, fmt=True):
        headers = ChaoXingApi.headers.copy()
        check_url = 'http://mooc1-1.chaoxing.com/api/workTestPendingNew'
        resp = request_retry(
                "get", check_url,
                headers=headers,
                cookies=self.cookies
            )
        if '登录' in resp.text:
            return '用户未登录'
        else:
            info_url = 'http://passport2.chaoxing.com/mooc/accountManage'
            resp = request_retry(
                "get", info_url,
                headers=headers,
                cookies=self.cookies
            )
            name = re.findall(r"messageName\">(.*?)</", resp.text)[0]
            phone = re.findall(r"messagePhone\">(.*?)</", resp.text)[0]
            if fmt:
                return f"姓名：{name}，手机号：{phone}"
            else:
                return dict(name=name, phone=phone)

    # def _get_course(self):
    #     headers = ChaoXingApi.headers.copy()
    #     course_url = 'https://mooc2-ans.chaoxing.com/visit/courses/list'

    def image_upload(self, img):
        headers = ChaoXingApi.headers.copy()
        upload_url = 'http://notice.chaoxing.com/pc/files/uploadNoticeFile'
        files = {
            'attrFile': (f"{int(time.time() * 1000)}.png", img)
        }
        try:
            resp = request_retry(
                "POST", upload_url,
                files=files,
                headers=headers,
                cookies=self.cookies
            )
            data = json.loads(resp.text)
            if data['status']:
                # img_url = self.default_url(data['att_file']['att_clouddisk']['fileId'])
                img_url = data['url'].split('?')[0]
                return {'code': 0, 'data': img_url}
            else:
                return None
        except Exception as e:
            return {'code': 114514, 'message': str(e)}
