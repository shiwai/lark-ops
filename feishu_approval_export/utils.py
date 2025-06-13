import time
import re
import logging

def timestamp_to_str(ts):
    if not ts:
        return ''
    # 飞书API返回的时间戳为毫秒
    try:
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(ts) / 1000))
    except Exception:
        return str(ts)

def str_to_timestamp(s):
    """
    将yyyy-mm-dd hh:mm:ss格式字符串转为时间戳（毫秒）
    """
    try:
        return int(time.mktime(time.strptime(s, '%Y-%m-%d %H:%M:%S'))) * 1000
    except Exception:
        return None

def input_time(prompt):
    """
    交互式输入时间，支持yyyy-mm-dd或yyyy-mm-dd hh:mm:ss，返回时间戳（毫秒）
    """
    while True:
        s = input(prompt)
        # 支持yyyy-mm-dd
        if re.match(r'^\d{4}-\d{2}-\d{2}$', s):
            s = s + ' 00:00:00'
        if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', s):
            ts = str_to_timestamp(s)
            if ts:
                return ts
        logging.error('时间格式错误，请输入形如 yyyy-mm-dd 或 yyyy-mm-dd hh:mm:ss 的时间！') 