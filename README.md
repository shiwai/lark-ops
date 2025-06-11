# 飞书审批流自动化导出工具

本项目用于通过飞书开放平台自动化导出审批流数据。

## 主要功能
- 获取并导出飞书审批流数据
- 支持自定义审批流类型
- 支持定时任务或手动触发

## 目录结构
```
feishu_approval_export/
├── __init__.py
├── config.py           # 配置文件，含token等信息
├── feishu_api.py       # 封装飞书API的请求
├── approval_exporter.py# 审批流导出逻辑
├── main.py             # 启动脚本
└── utils.py            # 工具函数
```

## 使用说明
1. 在`config.py`中填写你的飞书应用App ID、App Secret、审批流Code等信息。
2. 运行`python main.py`即可导出审批流数据。

详细API文档参考：[飞书开放平台审批流接入指引](https://open.feishu.cn/document/server-docs/approval-v4/development-guide/native-approval-access-guide) 