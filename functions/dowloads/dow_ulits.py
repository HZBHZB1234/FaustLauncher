from json import load
import os

def check_need_up_translate() -> bool:
    if not os.path.exists('workshop/LLC_zh-CN/info/version.json'):
        return True

    version_timestamp = load(
        open('workshop/LimbusCompany_Data/Lang/LLC_zh-CN/info/version.json', 
             'r', encoding='utf-8')
    )['version']

    now_timestamp = load(
        open('workshop/LLC_zh-CN/info/version.json', 
             'r', encoding='utf-8')
    )['version']

    # 检测版本是否更新
    if version_timestamp != now_timestamp:
        return True
    
    return False
