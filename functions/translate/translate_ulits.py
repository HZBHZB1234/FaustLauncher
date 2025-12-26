import requests
import json
import time
import hashlib
import uuid

class YoudaoTranslator:
    """有道翻译API封装类"""
    
    def __init__(self, app_key=None, app_secret=None):
        """
        初始化有道翻译API
        Args:
            app_key: 有道翻译API的应用ID
            app_secret: 有道翻译API的应用密钥
        """
        self.app_key = app_key or '1736249955e2ddc2'
        self.app_secret = app_secret or 'kwl2GRgG3LAXM2aEfZGFYOaozNOX6Lzg'
        self.base_url = 'https://openapi.youdao.com/api'
        
    def generate_sign_v3(self, text, salt, curtime):
        """生成v3签名"""
        if len(text) <= 20:
            input_str = text
        else:
            input_str = text[:10] + str(len(text)) + text[-10:]
        
        sign_str = self.app_key + input_str + str(salt) + str(curtime) + self.app_secret
        return hashlib.sha256(sign_str.encode('utf-8')).hexdigest()
    
    def detect_language(self, text):
        """检测文本语言"""
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return 'zh-CHS'
        elif any(char.isalpha() for char in text):
            return 'en'
        else:
            return 'auto'
    
    def translate(self, text, translation_type='auto_to_zh'):
        """
        使用有道翻译API进行翻译
        Args:
            text: 原始文本
            translation_type: 翻译类型，支持：
                'auto_to_zh' - 自动检测到中文
                'zh_to_en'   - 中文到英文
                'en_to_zh'   - 英文到中文
        Returns:
            翻译后的文本
        """
        if not text or not text.strip():
            return "请输入有效的文本"
        
        # 根据翻译类型设置语言方向
        translation_types = {
            'auto_to_zh': ('auto', 'zh-CHS'),
            'zh_to_en': ('zh-CHS', 'en'),
            'en_to_zh': ('en', 'zh-CHS')
        }
        
        if translation_type not in translation_types:
            return f"不支持的翻译类型: {translation_type}"
        
        from_lang, to_lang = translation_types[translation_type]
        
        try:
            # 自动检测语言
            if from_lang == 'auto':
                detected_lang = self.detect_language(text)
                from_lang = detected_lang if detected_lang != 'auto' else 'en'
            
            # 如果源语言和目标语言相同，直接返回原文
            if from_lang == to_lang:
                return text
            
            # 生成随机数和当前时间戳
            salt = str(uuid.uuid4())
            curtime = str(int(time.time()))
            
            # 生成签名
            sign = self.generate_sign_v3(text, salt, curtime)
            
            # 准备请求参数
            params = {
                'q': text,
                'from': from_lang,
                'to': to_lang,
                'appKey': self.app_key,
                'salt': salt,
                'sign': sign,
                'signType': 'v3',
                'curtime': curtime
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # 发送请求
            response = requests.post(self.base_url, data=params, headers=headers, timeout=10)
            
            # 检查响应状态
            if response.status_code != 200:
                return f"请求失败，状态码: {response.status_code}"
            
            # 解析响应
            result = response.json()
            
            # 检查错误码
            error_code = result.get('errorCode', '0')
            if error_code != '0':
                error_msg = self.get_error_message(error_code)
                return f"翻译失败: {error_msg}"
            
            # 提取翻译结果
            if 'translation' in result and result['translation']:
                return result['translation'][0]
            else:
                return "翻译结果为空"
                
        except requests.exceptions.Timeout:
            return "请求超时，请检查网络连接"
        except requests.exceptions.ConnectionError:
            return "网络连接错误，请检查网络设置"
        except json.JSONDecodeError:
            return "API返回的数据格式错误"
        except Exception as e:
            return f"翻译过程中出现未知错误: {str(e)}"
    
    def get_error_message(self, error_code):
        """获取错误码对应的错误信息"""
        error_messages = {
            '101': '缺少必填参数',
            '102': '不支持的语言类型',
            '103': '翻译文本过长',
            '104': '不支持的API类型',
            '105': '不支持的签名类型',
            '106': '不支持的响应类型',
            '107': '不支持的加密类型',
            '108': '应用ID无效',
            '109': '批量日志无效',
            '110': '无服务可用',
            '111': '开发者账号无效',
            '112': '请求服务无效',
            '113': '查询为空',
            '114': '签名验证失败',
            '116': 'q参数为空',
            '201': '解密失败，检查加密方式',
            '202': '签名验证失败',
            '203': '访问IP不在白名单中',
            '205': '应用不存在',
            '206': '应用未激活',
            '301': '词典查询失败',
            '302': '翻译查询失败',
            '303': '服务连接异常',
            '304': '服务查询失败',
            '401': '账户余额不足',
            '411': '访问频率受限',
            '412': '长请求过于频繁'
        }
        return error_messages.get(error_code, f'未知错误: {error_code}')

def translate_text(text, translation_type='auto_to_zh'):
    """
    翻译函数 - 主接口
    Args:
        text: 原始文本
        translation_type: 翻译类型
            'auto_to_zh' - 自动检测到中文 (默认)
            'zh_to_en'   - 中文到英文
            'en_to_zh'   - 英文到中文
    Returns:
        翻译后的文本
    """
    translator = YoudaoTranslator()
    return translator.translate(text, translation_type)

# 保留测试用的主函数（可选）
def main():
    """测试函数"""
    # 测试示例
    test_text = "Hello world"
    result = translate_text(test_text, 'auto_to_zh')
    print(f"测试翻译: {test_text} -> {result}")

if __name__ == "__main__":
    main()