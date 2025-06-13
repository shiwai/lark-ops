import sys
import os
from feishu_approval_export.approval_exporter import ApprovalExporter
from feishu_approval_export.render import render_approval_json_to_html
from feishu_approval_export.utils import str_to_timestamp, input_time
import concurrent.futures
from feishu_approval_export.feishu_api import FeishuAPI
import pickle
import json
from datetime import datetime
import logging
import time

def setup_logger():
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d%H%M%S')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger()

def format_time_range(start_time, end_time):
    if isinstance(start_time, str):
        start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    else:
        start_dt = datetime.fromtimestamp(int(start_time) / 1000)
        end_dt = datetime.fromtimestamp(int(end_time) / 1000)
    return f"{start_dt.strftime('%Y年%m月%d日 %H:%M')} 至 {end_dt.strftime('%Y年%m月%d日 %H:%M')}"

def render_one(args):
    json_path, user_id_name_map = args
    html_dir = 'approval_htmls'
    from feishu_approval_export.render import render_approval_json_to_html
    import os
    
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)['data']
    
    # 收集所有需要的user_id
    user_ids = set()
    
    # 1. 申请人
    user_id = data.get('user_id')
    if user_id:
        user_ids.add(user_id)
    
    # 2. task_list中的审批人
    for task in data.get('task_list', []):
        task_user_id = task.get('user_id')
        if task_user_id:
            user_ids.add(task_user_id)
    
    # 3. timeline中的抄送人和审批人
    for tl in data.get('timeline', []):
        if tl.get('type') == 'CC':
            for cc in tl.get('cc_user_list', []):
                cc_user_id = cc.get('user_id')
                if cc_user_id:
                    user_ids.add(cc_user_id)
        elif tl.get('type') == 'PASS':
            tl_user_id = tl.get('user_id')
            if tl_user_id:
                user_ids.add(tl_user_id)
    
    # 4. 评论作者
    for comment in data.get('comment_list', []):
        comment_user_id = comment.get('user_id')
        if comment_user_id:
            user_ids.add(comment_user_id)
            
    # 确保所有user_id都在映射中
    api = FeishuAPI()
    for uid in user_ids:
        if uid not in user_id_name_map:
            user_id_name_map[uid] = api.get_user_name_by_id(uid)
    
    applicant_name = user_id_name_map.get(user_id, user_id)
    serial_number = data['serial_number']
    
    start_time = data.get('start_time')
    year = str(datetime.fromtimestamp(int(start_time) / 1000).year) if start_time else '未知年份'
    
    serial_dir = os.path.join(html_dir, applicant_name, year, serial_number)
    os.makedirs(serial_dir, exist_ok=True)
    html_path = os.path.join(serial_dir, f'{serial_number}.html')
    render_approval_json_to_html(json_path, html_path, user_id_name_map)
    return html_path

def main():
    logger = setup_logger()
    
    if len(sys.argv) >= 3:
        start_time = sys.argv[1]
        end_time = sys.argv[2]
    else:
        logger.info('请输入导出数据的时间范围')
        start_time = input_time('开始时间 (yyyy-mm-dd hh:mm:ss)：')
        end_time = input_time('结束时间 (yyyy-mm-dd hh:mm:ss)：')

    time_range = format_time_range(start_time, end_time)
    logger.info(f'开始导出审批数据，时间范围：{time_range}')
    
    exporter = ApprovalExporter()
    exporter.export(start_time, end_time)
    
    json_dir = 'approval_jsons'
    json_files = [fname for fname in os.listdir(json_dir) if fname.endswith('.json')]
    logger.info(f'成功导出 {len(json_files)} 条审批数据')

    html_dir = 'approval_htmls'
    os.makedirs(html_dir, exist_ok=True)
    
    user_ids = set()
    for fname in json_files:
        with open(os.path.join(json_dir, fname), encoding='utf-8') as f:
            data = json.load(f)['data']
            uid = data.get('user_id')
            if uid:
                user_ids.add(uid)
    
    logger.info(f'开始获取用户信息，共 {len(user_ids)} 个用户')
    api = FeishuAPI()
    user_id_name_map = {uid: api.get_user_name_by_id(uid) for uid in user_ids}
    logger.info('用户信息获取完成')

    logger.info('开始生成HTML文件')
    args_list = [(os.path.join(json_dir, fname), user_id_name_map) for fname in json_files]
    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
        html_files = list(executor.map(render_one, args_list))
    logger.info(f'HTML生成完成，共生成 {len(html_files)} 个文件，存放目录：{html_dir}')

if __name__ == '__main__':
    main() 