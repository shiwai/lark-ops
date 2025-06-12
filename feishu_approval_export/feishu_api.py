import requests
from . import config
import json

class FeishuAPI:
    BASE_URL = 'https://open.feishu.cn/open-apis/'

    def __init__(self):
        self.app_id = config.APP_ID
        self.app_secret = config.APP_SECRET
        self.token = config.TENANT_ACCESS_TOKEN

    def get_tenant_access_token(self):
        """
        获取tenant_access_token，token部分可手动填写或自动获取。
        """
        if self.token:
            return self.token
        url = self.BASE_URL + 'auth/v3/tenant_access_token/internal/'
        resp = requests.post(url, json={
            'app_id': self.app_id,
            'app_secret': self.app_secret
        })
        data = resp.json()
        self.token = data.get('tenant_access_token', '')
        return self.token

    def get_approval_instances(self, approval_code, start_time, end_time, page_size=100, page_token=None):
        """
        获取审批流实例列表，增强日志输出
        """
        url = self.BASE_URL + 'approval/v4/instances'
        headers = {
            'Authorization': f'Bearer {self.get_tenant_access_token()}'
        }
        params = {
            'approval_code': approval_code,
            'start_time': int(start_time),
            'end_time': int(end_time),
            'page_size': page_size
        }
        if page_token:
            params['page_token'] = page_token
        print("\n[飞书API请求] URL:", url)
        print("[飞书API请求] Headers:", headers)
        print("[飞书API请求] Params:", params)
        resp = requests.get(url, headers=headers, params=params)
        print("[飞书API响应] 状态码:", resp.status_code)
        print("[飞书API响应] 完整URL:", resp.url)
        try:
            print("[飞书API响应] 内容:", json.dumps(resp.json(), ensure_ascii=False, indent=2))
        except Exception:
            print("[飞书API响应] 内容(非json):", resp.text)
        return resp.json()

    def get_approval_instance_detail(self, instance_code):
        url = self.BASE_URL + f'approval/v4/instances/{instance_code}'
        headers = {
            'Authorization': f'Bearer {self.get_tenant_access_token()}'
        }
        print(f"[飞书API请求] 获取详情: {url}")
        resp = requests.get(url, headers=headers)
        print(f"[飞书API响应] 状态码: {resp.status_code}")
        try:
            json.dumps(resp.json(), ensure_ascii=False, indent=2)
            # print("[飞书API响应] 内容:", json.dumps(resp.json(), ensure_ascii=False, indent=2))
        except Exception:
            print("[飞书API响应] 内容(非json):", resp.text)
        return resp.json()

    def get_user_name_by_id(self, user_id):
        url = self.BASE_URL + f'contact/v3/users/{user_id}?department_id_type=open_department_id&user_id_type=user_id'
        headers = {
            'Authorization': f'Bearer {self.get_tenant_access_token()}'
        }
        resp = requests.get(url, headers=headers)
        # print(f"[用户信息API] 请求: {url}，状态码: {resp.status_code}，返回: {resp.text}")
        if resp.status_code == 200:
            data = resp.json()
            if data.get('code') == 0:
                user = data['data'].get('user', {})
                return user.get('name') or user.get('en_name') or user.get('user_id') or user_id
        return user_id

    def get_user_name_by_open_id(self, open_id):
        url = self.BASE_URL + f'contact/v3/users/{open_id}'
        headers = {
            'Authorization': f'Bearer {self.get_tenant_access_token()}'
        }
        resp = requests.get(url, headers=headers)
        print(f"[用户信息API] 请求: {url}，状态码: {resp.status_code}，返回: {resp.text}")
        if resp.status_code == 200:
            data = resp.json()
            if data.get('code') == 0:
                return data['data'].get('name') or data['data'].get('en_name') or open_id
        return open_id

    def get_user_name(self, user_id=None, open_id=None):
        if open_id:
            return self.get_user_name_by_open_id(open_id)
        elif user_id:
            return self.get_user_name_by_id(user_id)
        return '' 