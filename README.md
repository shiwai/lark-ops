# 飞书审批流自动化导出工具

本项目用于通过飞书开放平台导出指定审批流数据，并生成 CSV、JSON 和 HTML 归档文件。

## 主要功能

- **批量导出审批实例**：按指定时间范围分页获取审批实例列表，并拉取每条审批详情。
- **导出结构化数据**：生成审批摘要 CSV，并将每条审批详情保存为 JSON。
- **生成 HTML 报告**：将审批详情 JSON 渲染为 HTML，按申请人、年份和流水号归档到 `approval_htmls/`。
- **用户名称展示**：调用飞书通讯录接口，将部分审批人、申请人和抄送人的 `user_id` 转换为姓名。
- **本地配置审批流**：通过本地 `feishu_approval_export/config.py` 配置飞书应用凭证和审批流 Code。
- **可扩展模板**：可修改 `templates/approval_report.html` 调整 HTML 报告样式。

## 目录结构

```text
feishu_approval_export/
├── __init__.py
├── approval_exporter.py  # 审批流导出逻辑
├── feishu_api.py         # 飞书 API 请求封装
├── render.py             # 审批详情 JSON 转 HTML
└── utils.py              # 时间转换等工具函数
templates/
└── approval_report.html  # HTML 报告模板
main.py                   # 启动脚本
requirements.txt          # Python 依赖
```

以下文件或目录为本地生成内容，已被 `.gitignore` 忽略：

```text
feishu_approval_export/config.py  # 本地密钥和审批流配置
approval_export.csv               # 审批摘要 CSV
approval_jsons/                   # 审批详情 JSON
approval_htmls/                   # HTML 报告和附件归档
logs/                             # 运行日志
```

## 安装依赖

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 配置

创建本地配置文件 `feishu_approval_export/config.py`：

```python
APP_ID = "cli_xxx"
APP_SECRET = "xxx"
APPROVAL_CODE = "xxx"

# 可留空，程序会通过 APP_ID 和 APP_SECRET 自动获取 tenant_access_token。
TENANT_ACCESS_TOKEN = ""
```

## 使用说明

运行脚本后按提示输入导出时间范围：

```bash
python main.py
```

时间支持以下格式：

```text
2025-01-01
2025-01-01 00:00:00
```

导出完成后会生成：

- `approval_export.csv`：审批实例摘要。
- `approval_jsons/<instance_code>.json`：审批详情原始 JSON。
- `approval_htmls/<申请人>/<年份>/<流水号>/<流水号>.html`：HTML 审批报告。
- `logs/<运行时间>.log`：运行日志。

如需切换审批流类型，修改 `feishu_approval_export/config.py` 中的 `APPROVAL_CODE`。

## 参考文档

- [飞书开放平台审批流接入指引](https://open.feishu.cn/document/server-docs/approval-v4/development-guide/native-approval-access-guide)
