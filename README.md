# 飞书审批流自动化导出工具

本项目用于通过飞书开放平台自动化导出审批流数据，并支持多种格式的导出和可视化。

## 主要功能
- **自动批量导出审批流实例**：支持指定时间范围，自动分页获取所有审批流实例。
- **审批流HTML可视化**：自动将所有JSON审批流详情渲染为美观的HTML文件，保存在`approval_htmls/`目录，便于浏览和归档。
- **自定义审批流类型**：支持配置不同的审批流Code，适配多种导出场景， 如审批、用证用印等。
- **可扩展模板**：支持自定义Jinja2模板，灵活调整审批流HTML展示样式。

## 目录结构
```
feishu_approval_export/
├── __init__.py
├── config.py           # 配置文件，含token等信息
├── feishu_api.py       # 封装飞书API的请求
├── approval_exporter.py# 审批流导出逻辑
├── render.py           # 审批流JSON转HTML渲染
├── utils.py            # 工具函数
templates/
└── approval_report.html# 审批流HTML模板
main.py                 # 启动脚本
requirements.txt        # 依赖库
approval_jsons/         # 审批流详情JSON文件输出目录
approval_htmls/         # 审批流HTML文件输出目录
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用说明

1. 在`feishu_approval_export/config.py`中填写你的飞书应用App ID、App Secret、审批流Code等信息。
2. 运行以下命令导出审批流数据并自动生成HTML报告：

   ```bash
   python main.py <开始时间戳(ms)> <结束时间戳(ms)> [导出文件名]
   # 示例
   python main.py 1735660800000 1751299200000
   ```

   - 审批流关键信息将导出到`approval_export.csv`（或自定义文件名）。
   - 审批流详情JSON文件保存在`approval_jsons/`目录。
   - 审批流HTML报告保存在`approval_htmls/`目录。

3. 可根据需要自定义`templates/approval_report.html`模板，调整HTML报告样式。

4. 支持多种审批流类型，修改`config.py`中的`APPROVAL_CODE`即可切换。

## 参考文档

- [飞书开放平台审批流接入指引](https://open.feishu.cn/document/server-docs/approval-v4/development-guide/native-approval-access-guide) 