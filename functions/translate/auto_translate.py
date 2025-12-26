import os
import json
from pathlib import Path
from functions.translate.translate_ulits import translate_text
from time import sleep
import re

class AutoTranslate:
    def __init__(self, source_path, target_path, blacklist_files=None):
        self.source_path = Path(source_path)
        self.target_path = Path(target_path)
        # 这些字段翻译
        self.excluded_keys = {'content','teller','dlg','desc', 'dialog', 'abName', 'name'}
        self.blacklist_files = set(blacklist_files) if blacklist_files else set()
        self.translation_errors = []
    
    def _load_json_file(self, file_path):
        try:
            # 先尝试使用utf-8-sig解码BOM文件
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                return json.load(f)
        except UnicodeDecodeError:
            # 如果utf-8-sig失败，尝试普通utf-8
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载JSON文件失败 {file_path}: {e}")
                return None
        except Exception as e:
            print(f"加载JSON文件失败 {file_path}: {e}")
            return None
    
    def _save_json_file(self, file_path, data):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存JSON文件失败 {file_path}: {e}")
            return False
    
    def _should_translate_value(self, key, value):
        """检查字段是否需要翻译"""
        if key not in self.excluded_keys:
            return False
        
        if not isinstance(value, str):
            return False
        
        if not value.strip():
            return False
        
        # 检查是否已经是中文
        if self._is_chinese(value):
            return False
        
        return True
    
    def _is_chinese(self, text):
        """检查文本是否已经是中文"""
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        return bool(chinese_pattern.search(text))
    
    def _find_item_by_id(self, data_list, item_id):
        """根据id在dataList中查找项目"""
        for item in data_list:
            if item.get('id') == item_id:
                return item
        return None
    
    def _get_missing_items(self, source_items, target_items):
        """获取源文件中存在但目标文件中缺失的项目"""
        source_ids = {item.get('id') for item in source_items if item.get('id') is not None}
        target_ids = {item.get('id') for item in target_items if item.get('id') is not None}
        
        missing_ids = source_ids - target_ids
        missing_items = []
        
        for item in source_items:
            if item.get('id') in missing_ids:
                missing_items.append(item)
        
        return missing_items
    
    def _translate_item_fields(self, source_item, target_item):
        """翻译项目中的字段，只翻译需要翻译的字段"""
        translated_item = target_item.copy() if target_item else {}
        
        # 确保所有源项目的字段都被保留
        for key, value in source_item.items():
            if key not in translated_item:
                translated_item[key] = value
        
        # 只翻译需要翻译的字段
        for key, value in source_item.items():
            # 如果字段不在需要翻译的列表中，跳过翻译
            if key not in self.excluded_keys:
                continue

            if '??' in translated_item[key]:
                continue
                
            # 检查是否需要翻译
            if self._should_translate_value(key, value):
                # 对于缺失的项目（target_item为None），直接进行翻译
                # 对于已存在的项目，如果目标项中已经存在该字段且是中文，跳过翻译
                if target_item is not None and key in translated_item:
                    # 检查目标字段是否已经是中文，如果是则跳过翻译
                    if self._is_chinese(translated_item[key]):
                        continue
                
                # 进行翻译
                try:
                    translated_value = translate_text(value, translation_type='auto_to_zh')
                    if "翻译失败" not in translated_value:
                        translated_item[key] = translated_value
                        print(f"✅ 翻译成功: {key} = {translated_value}")
                    else:
                        # 翻译失败，保留原值
                        translated_item[key] = value
                        self.translation_errors.append(f"翻译失败: {key} = {value}")
                        print(f"❌ 翻译失败: {key} = {value}")
                except Exception as e:
                    print(f"💥 翻译异常: {key} = {value}, 错误: {e}")
                    translated_item[key] = value
                    self.translation_errors.append(f"翻译异常: {key} = {value}")
                
                sleep(0.3)  # 增加延迟避免频率限制
        
        return translated_item
    
    def _process_json_file(self, source_file, target_file):
        """处理单个JSON文件"""
        source_data = self._load_json_file(source_file)
        if not source_data:
            return False, 0
        
        # 如果目标文件不存在，创建空的目标数据结构
        if not target_file.exists():
            target_data = {'dataList': []}
        else:
            target_data = self._load_json_file(target_file)
            if not target_data:
                target_data = {'dataList': []}
            elif 'dataList' not in target_data:
                target_data['dataList'] = []
        
        source_items = source_data.get('dataList', [])
        target_items = target_data.get('dataList', [])
        
        # 获取缺失的项目
        missing_items = self._get_missing_items(source_items, target_items)
        translated_count = 0
        
        # 处理缺失的项目
        for source_item in missing_items:
            item_id = source_item.get('id')
            if not item_id:
                continue
            
            print(f"🔍 发现缺失项目: ID={item_id}")
            translated_item = self._translate_item_fields(source_item, None)
            target_items.append(translated_item)
            translated_count += 1
        
        # 更新已存在的项目（只翻译需要翻译的字段）
        for target_item in target_items:
            item_id = target_item.get('id')
            if not item_id:
                continue
            
            source_item = self._find_item_by_id(source_items, item_id)
            if source_item:
                # 只更新需要翻译的字段
                updated_item = self._translate_item_fields(source_item, target_item)
                target_items[target_items.index(target_item)] = updated_item
        
        target_data['dataList'] = target_items
        success = self._save_json_file(target_file, target_data)
        return success, translated_count
    
    def _get_target_filename(self, source_filename):
        """将源文件名 EN_xxx.json 转换为目标文件名 xxx.json"""
        if source_filename.startswith('EN_') and source_filename.endswith('.json'):
            return source_filename[3:]  # 移除 EN_ 前缀
        return source_filename
    
    def _is_blacklisted(self, filename):
        """检查文件是否在黑名单中"""
        target_filename = self._get_target_filename(filename)
        return target_filename in self.blacklist_files
    
    def _copy_directory_structure(self):
        """只创建目录结构，不复制文件内容"""
        for root, dirs, files in os.walk(self.source_path):
            relative_path = os.path.relpath(root, self.source_path)
            target_dir = self.target_path / relative_path
            
            if relative_path != '.':
                os.makedirs(target_dir, exist_ok=True)
    
    def run(self, progress_callback=None):
        """运行翻译任务"""
        print(f"🚀 开始自动翻译: {self.source_path} -> {self.target_path}")
        print(f"📋 排除字段: {self.excluded_keys}")
        print(f"📁 文件名转换规则: EN_xxx.json -> xxx.json")
        if self.blacklist_files:
            print(f"🚫 黑名单文件: {self.blacklist_files}")
        
        if not self.source_path.exists():
            print(f"❌ 源路径不存在: {self.source_path}")
            return False
        
        # 只创建目录结构，不复制文件内容
        self._copy_directory_structure()
        
        # 获取所有JSON文件
        json_files = []
        for root, dirs, files in os.walk(self.source_path):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(Path(root) / file)
        
        total_files = len(json_files)
        processed_files = 0
        total_translated = 0
        
        for source_file in json_files:
            relative_path = source_file.relative_to(self.source_path)
            filename = source_file.name
            
            # 检查是否在黑名单中
            if self._is_blacklisted(filename):
                print(f"⏭️ 跳过黑名单文件: {relative_path}")
                processed_files += 1
                if progress_callback:
                    progress_callback(processed_files, total_files, f"跳过黑名单文件: {relative_path}")
                continue
            
            # 转换文件名
            target_filename = self._get_target_filename(filename)
            target_relative_path = Path(relative_path).parent / target_filename
            target_file = self.target_path / target_relative_path
            
            print(f"\n📄 处理文件: {relative_path} -> {target_relative_path}")
            
            if progress_callback:
                progress_callback(processed_files, total_files, f"处理文件: {target_relative_path}")
            
            result = self._process_json_file(source_file, target_file)
            if isinstance(result, tuple) and len(result) == 2:
                success, translated_count = result
                if success:
                    processed_files += 1
                    total_translated += translated_count
                    status = "✅ 完成处理" if translated_count == 0 else f"✅ 完成处理 (新增 {translated_count} 条翻译)"
                    print(f"{status}: {target_relative_path}")
                else:
                    print(f"❌ 处理失败: {target_relative_path}")
            else:
                print(f"❌ 处理失败: {target_relative_path} (返回类型错误)")
            
            if progress_callback:
                progress_callback(processed_files, total_files, f"完成: {target_relative_path}")
        
        print(f"\n🎉 翻译完成!")
        print(f"📊 总处理文件数: {processed_files}")
        print(f"📈 总新增翻译条目: {total_translated}")
        
        if self.translation_errors:
            print(f"\n⚠️ 翻译错误列表 ({len(self.translation_errors)} 个错误):")
            for error in self.translation_errors[:10]:  # 只显示前10个错误
                print(f"  - {error}")
            if len(self.translation_errors) > 10:
                print(f"  ... 还有 {len(self.translation_errors) - 10} 个错误")
        
        return True

def auto_translate(source_path, target_path, blacklist_files=None, progress_callback=None):
    translator = AutoTranslate(source_path, target_path, blacklist_files)
    return translator.run(progress_callback)

if __name__ == "__main__":
    # 示例黑名单文件
    blacklist_files = [
        "ProjectGSLessonName.json",  # 示例黑名单文件
        "SomeOtherFile.json"         # 另一个示例
    ]
    
    source_path = "D:\\steam\\steamapps\\common\\Limbus Company\\LimbusCompany_Data\\Assets\\Resources_moved\\Localize\\en"
    target_path = "E:/projects/python/FaustLauncher/workshop/LLC_zh-CN"
    
    auto_translate(source_path, target_path, blacklist_files)