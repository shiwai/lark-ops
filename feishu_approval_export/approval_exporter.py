import csv
from . import config
from .feishu_api import FeishuAPI
from .utils import timestamp_to_str
import os
import json
import logging

class ApprovalExporter:
    def __init__(self):
        self.api = FeishuAPI()
        self.approval_code = config.APPROVAL_CODE

    def export(self, start_time, end_time, output_file='approval_export.csv'):
        page_token = None
        all_instance_codes = []
        # 1. 获取所有instance_code_list，page_size=100
        while True:
            data = self.api.get_approval_instances(
                self.approval_code, start_time, end_time, page_size=100, page_token=page_token
            )
            instance_codes = data.get('data', {}).get('instance_code_list', [])
            all_instance_codes.extend(instance_codes)
            page_token = data.get('data', {}).get('page_token')
            if not page_token :
                break

        # 2. 获取每个instance的详情
        all_details = []
        user_id_name_map = {}
        json_dir = 'approval_jsons'
        os.makedirs(json_dir, exist_ok=True)
        for code in all_instance_codes:
            detail = self.api.get_approval_instance_detail(code)
            if detail.get('code') == 0 and 'data' in detail:
                ins = detail['data']
                # 保存json文件
                with open(os.path.join(json_dir, f'{code}.json'), 'w', encoding='utf-8') as jf:
                    json.dump(detail, jf, ensure_ascii=False, indent=2)
                # 收集user_id
                user_id = ins.get('user_id')
                if user_id and user_id not in user_id_name_map:
                    user_id_name_map[user_id] = None  # 先占位
                all_details.append(ins)
            else:
                logging.error(f'获取详情失败: {code}, 响应: {detail}')

        # 3. 批量获取用户名
        for uid in user_id_name_map.keys():
            user_id_name_map[uid] = self.api.get_user_name_by_id(uid)

        # 4. 写入CSV（用户名替换user_id）
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['instance_code', 'status', 'start_time', 'end_time', 'user_name'])
            for ins in all_details:
                user_id = ins.get('user_id')
                user_name = user_id_name_map.get(user_id, user_id)
                writer.writerow([
                    ins.get('instance_code'),
                    ins.get('status'),
                    timestamp_to_str(ins.get('start_time', 0)),
                    timestamp_to_str(ins.get('end_time', 0)),
                    user_name
                ])
        logging.info(f'导出完成，共{len(all_details)}条，文件：{output_file}')
        logging.info(f'所有审批流详情已保存到目录：{json_dir}') 