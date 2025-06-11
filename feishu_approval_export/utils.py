import time

def timestamp_to_str(ts):
    if not ts:
        return ''
    # 飞书API返回的时间戳为毫秒
    try:
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(ts) / 1000))
    except Exception:
        return str(ts) 