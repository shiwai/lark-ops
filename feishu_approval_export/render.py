import json
from jinja2 import Environment, FileSystemLoader
from .feishu_api import FeishuAPI
from .utils import timestamp_to_str

env = Environment(loader=FileSystemLoader('templates'))
api = FeishuAPI()

def get_user_name(user_id=None, open_id=None):
    if user_id:
        return api.get_user_name_by_id(user_id)
    return ''

def render_approval_json_to_html(json_path, output_html):
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
        approval_records.append({
            'node_name': t['node_name'],
            'user_name': get_user_name(user_id=t.get('user_id'), open_id=t.get('open_id')),
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
                if rec['user_name'] == get_user_name(user_id=tl.get('user_id'), open_id=tl.get('open_id')) and rec['time'] == timestamp_to_str(tl.get('create_time')):
                    if tl.get('comment'):
                        rec['comment'] = tl.get('comment')
        elif tl.get('type') == 'CC':
            cc_names = []
            for cc in tl.get('cc_user_list', []):
                cc_names.append(get_user_name(user_id=cc.get('user_id'), open_id=cc.get('open_id')))
            approval_records.append({
                'node_name': '抄送',
                'user_name': ', '.join(cc_names),
                'time': timestamp_to_str(tl.get('create_time')),
                'status': 'CC',
                'status_cn': '已抄送',
                'comment': '',
            })
    tpl = env.get_template('approval_report.html')
    applicant_name = get_user_name(user_id=data.get('user_id'), open_id=data.get('open_id'))
    serial_number = data['serial_number']
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