import sys
import os
from feishu_approval_export.approval_exporter import ApprovalExporter
from feishu_approval_export.render import render_approval_json_to_html
from feishu_approval_export.utils import str_to_timestamp, input_time
import concurrent.futures

def main():
    if len(sys.argv) >= 3:
        # 兼容老用法
        start_time = sys.argv[1]
        end_time = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else 'approval_export.csv'
    else:
        print('请输入导出数据的时间范围：')
        start_time = input_time('开始时间 (yyyy-mm-dd hh:mm:ss)：')
        end_time = input_time('结束时间 (yyyy-mm-dd hh:mm:ss)：')
        output_file = input('导出文件名（默认 approval_export.csv）：').strip() or 'approval_export.csv'
    exporter = ApprovalExporter()
    exporter.export(start_time, end_time, output_file)

    # 渲染所有json为html（多进程并发）
    json_dir = 'approval_jsons'
    html_dir = 'approval_htmls'
    os.makedirs(html_dir, exist_ok=True)
    json_files = [fname for fname in os.listdir(json_dir) if fname.endswith('.json')]

    def render_one(json_path):
        applicant_name, serial_number = render_approval_json_to_html(json_path, None)
        user_dir = os.path.join(html_dir, applicant_name)
        os.makedirs(user_dir, exist_ok=True)
        html_path = os.path.join(user_dir, f'{serial_number}.html')
        render_approval_json_to_html(json_path, html_path)
        return html_path

    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
        json_paths = [os.path.join(json_dir, fname) for fname in json_files]
        list(executor.map(render_one, json_paths))
    print(f'所有审批流HTML已生成到目录：{html_dir}')

if __name__ == '__main__':
    main() 