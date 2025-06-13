import json
from jinja2 import Environment, FileSystemLoader
from .feishu_api import FeishuAPI
from .utils import timestamp_to_str
import requests
import os
import logging

env = Environment(loader=FileSystemLoader('templates'))
api = FeishuAPI()

def get_user_name(user_id=None, open_id=None):
    if user_id:
        return api.get_user_name_by_id(user_id)
    return ''

def _parse_attachments(data, form):
    attachments = []
    serial_number = data.get('serial_number', '')
    # 1. comment_list 里的附件
    for comment in data.get('comment_list', []):
        for file in comment.get('files', []):
            title = file.get('title') or '附件'
            url = file.get('url')
            if url:
                attachments.append({'name': f'{serial_number}-{title}', 'url': url})
    # 2. form 里的附件
    for item in form:
        # 2.1 type为attachment/attachmentV2
        if item.get('type') in ('attachment', 'attachmentV2'):
            # attachmentV2: value为url列表，ext为逗号分隔的文件名
            value = item.get('value')
            ext = item.get('ext')
            if isinstance(value, list):
                # ext可能是逗号分隔的文件名
                names = []
                if ext and isinstance(ext, str):
                    names = [x.strip() for x in ext.split(',')]
                for idx, url in enumerate(value):
                    if url:
                        fname = names[idx] if idx < len(names) else f'附件{idx+1}'
                        attachments.append({'name': f'{serial_number}-{fname}', 'url': url})
            # attachment: value为对象列表
            elif isinstance(value, list):
                for file in value:
                    title = file.get('title') or '附件'
                    url = file.get('url')
                    if url:
                        attachments.append({'name': f'{serial_number}-{title}', 'url': url})
    return attachments

def _download_attachments(attachments, target_dir):
    for att in attachments:
        url = att['url']
        fname = att['name']
        path = os.path.join(target_dir, fname)
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                with open(path, 'wb') as f:
                    f.write(resp.content)
            else:
                logging.error('[附件下载失败] %s 状态码: %d url: %s', fname, resp.status_code, url)
        except Exception as e:
            logging.error('[附件下载异常] %s 错误: %s url: %s', fname, str(e), url)

def render_approval_json_to_html(json_path, output_html, user_id_name_map=None):
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)['data']
    form = json.loads(data['form'])
    # print('DEBUG: form内容:', form)
    # 解析表单字段
    reason = next((x['value'] for x in form if x['name'] == '采购事由'), '')
    department = next((x['value'][0]['name'] for x in form if x['name'] == '部门'), '')
    expect_time = next((x['value'] for x in form if x['name'] == '期望交付时间'), '')
    category = next((x['value'][0] if isinstance(x['value'], list) and x['value'] else x['value'] for x in form if x['name'] == '采购类别'), '')
    # 费用明细
    fee_detail = []
    for item in form:
        if item['name'] == '费用明细':
            value = item['value']
            if value and isinstance(value, list):
                current_row = {}
                for row in value[0] if value and isinstance(value[0], list) else []:
                    if isinstance(row, dict):
                        if row.get('name') == '名称' and current_row:
                            fee_detail.append(current_row)
                            current_row = {}
                        if row.get('name'):
                            # 备注字段也加入
                            current_row[row['name']] = row.get('value', '')
                if current_row:
                    fee_detail.append(current_row)
    # 统一字段名映射，保证模板兼容
    fee_detail_fixed = []
    for row in fee_detail:
        fee_detail_fixed.append({
            'name': row.get('名称', ''),
            'model': row.get('型号', ''),
            'count': row.get('数量', ''),
            'amount': row.get('金额', ''),
            'invoice': row.get('发票', ''),
            'purchase_channel': row.get('采购渠道', ''),
            'pay_channel': row.get('支付渠道', ''),
            'remark': row.get('备注', ''),
        })
    # print('DEBUG: 解析出的fee_detail_fixed:', fee_detail_fixed)
    # 审批状态中文
    status_map = {'APPROVED': '已通过', 'REJECTED': '已拒绝', 'PENDING': '待审批', 'DONE': '已完成'}
    status_cn = status_map.get(data['status'], data['status'])
    # 收集全局备注
    global_comments = [c.get('comment', '') for c in data.get('comment_list', []) if c.get('comment')]

    # 审批记录
    approval_records = []
    # 先处理task_list（保留原有逻辑，备注暂时为空）
    task_map = {}
    for t in data['task_list']:
        task_map[(t.get('user_id'), t.get('end_time'))] = t
        if user_id_name_map:
            user_name = user_id_name_map.get(t.get('user_id'), t.get('user_id'))
        else:
            user_name = get_user_name(user_id=t.get('user_id'), open_id=t.get('open_id'))
        approval_records.append({
            'node_name': t['node_name'],
            'user_name': user_name,
            'time': timestamp_to_str(t['end_time']),
            'status': t['status'],
            'status_cn': status_map.get(t['status'], t['status']),
            'comment': '',
        })
    # timeline中PASS节点补充备注
    for tl in data.get('timeline', []):
        if tl.get('type') == 'PASS':
            # 匹配task_list中的审批节点
            for rec in approval_records:
                if user_id_name_map:
                    tl_name = user_id_name_map.get(tl.get('user_id'), tl.get('user_id'))
                else:
                    tl_name = get_user_name(user_id=tl.get('user_id'), open_id=tl.get('open_id'))
                if rec['user_name'] == tl_name and rec['time'] == timestamp_to_str(tl.get('create_time')):
                    if tl.get('comment'):
                        rec['comment'] = tl.get('comment')
        elif tl.get('type') == 'CC':
            cc_names = []
            for cc in tl.get('cc_user_list', []):
                if user_id_name_map:
                    cc_name = user_id_name_map.get(cc.get('user_id'), cc.get('user_id'))
                else:
                    cc_name = get_user_name(user_id=cc.get('user_id'), open_id=cc.get('open_id'))
                cc_names.append(cc_name)
            approval_records.append({
                'node_name': '抄送',
                'user_name': ', '.join(cc_names),
                'time': timestamp_to_str(tl.get('create_time')),
                'status': 'CC',
                'status_cn': '已抄送',
                'comment': '',
            })
    tpl = env.get_template('approval_report.html')
    user_id = data.get('user_id')
    if user_id_name_map and user_id:
        applicant_name = user_id_name_map.get(user_id, user_id)
    else:
        applicant_name = get_user_name(user_id=user_id, open_id=data.get('open_id'))
    serial_number = data['serial_number']
    # 附件处理
    attachments = _parse_attachments(data, form)
    if output_html is not None and attachments:
        # output_html: approval_htmls/人名/年份/serial_number/serial_number.html
        serial_dir = os.path.dirname(output_html)
        os.makedirs(serial_dir, exist_ok=True)
        _download_attachments(attachments, serial_dir)
    html = tpl.render(
        approval_name=data['approval_name'],
        serial_number=serial_number,
        applicant_name=applicant_name,
        apply_time=timestamp_to_str(data['start_time']),
        department_name=department,
        status=data['status'],
        status_cn=status_cn,
        reason=reason,
        expect_time=expect_time,
        category=category,
        fee_detail=fee_detail_fixed,
        approval_records=approval_records,
        global_comments=global_comments,
    )
    if output_html is not None:
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(html)
    return applicant_name, serial_number

# # 示例调用
# render_approval_json_to_html('approval_jsons/433B2B56-0EF7-4789-90C9-0F55B81FF342.json', 'output.html')