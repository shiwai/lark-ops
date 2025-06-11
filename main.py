import sys
import os
from feishu_approval_export.approval_exporter import ApprovalExporter
from feishu_approval_export.render import render_approval_json_to_html

def main():
    if len(sys.argv) < 3:
        print('用法: python main.py <开始时间戳(ms)> <结束时间戳(ms)> [导出文件名]')
        print('示例: python main.py 1735660800000 1751299200000')
        return
    start_time = sys.argv[1]
    end_time = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else 'approval_export.csv'
    exporter = ApprovalExporter()
    exporter.export(start_time, end_time, output_file)

    # 渲染所有json为html
    json_dir = 'approval_jsons'
    html_dir = 'approval_htmls'
    os.makedirs(html_dir, exist_ok=True)
    for fname in os.listdir(json_dir):
        if fname.endswith('.json'):
            json_path = os.path.join(json_dir, fname)
            html_path = os.path.join(html_dir, fname.replace('.json', '.html'))
            render_approval_json_to_html(json_path, html_path)
    print(f'所有审批流HTML已生成到目录：{html_dir}')

if __name__ == '__main__':
    main() 