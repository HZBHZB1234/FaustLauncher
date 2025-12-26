import os
import requests
import subprocess

# 7-Zip可执行文件路径
SEVEN_ZIP_PATH = r"7-Zip\7z.exe"

def download_file(url, local_filename):
    """下载文件并显示进度"""
    try:
        # 发送请求
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # 获取文件大小
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        
        # 创建目录
        os.makedirs(os.path.dirname(local_filename), exist_ok=True)
        
        # 下载文件
        with open(local_filename, 'wb') as f:
            downloaded_size = 0
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # 显示下载进度
                    if total_size > 0:
                        percent = (downloaded_size / total_size) * 100
                        print(f"\r下载进度: {percent:.1f}% ({downloaded_size}/{total_size} bytes)", end='')
        
        print("\n下载完成!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"下载失败: {e}")
        return False
    except Exception as e:
        print(f"下载过程中出现错误: {e}")
        return False

def extract_with_7zip(archive_path, extract_path):
    """使用系统7zip解压（直接使用本地7z.exe）"""
    try:
        # 检查7z.exe是否存在
        if not os.path.exists(SEVEN_ZIP_PATH):
            print(f"错误: 7-Zip可执行文件不存在: {SEVEN_ZIP_PATH}")
            return False
        
        print(f"使用本地7-Zip解压: {SEVEN_ZIP_PATH}")
        
        # 确保目标目录存在
        os.makedirs(extract_path, exist_ok=True)
        
        # 检查文件大小，确保下载完整
        file_size = os.path.getsize(archive_path)
        if file_size < 1000:  # 如果文件太小，可能下载不完整
            print(f"警告: 压缩文件可能不完整，大小: {file_size} bytes")
            return False
        
        # 使用7z.exe解压
        result = subprocess.run([
            SEVEN_ZIP_PATH, 
            'x',           # 解压命令
            archive_path,   # 压缩文件路径
            f'-o{extract_path}',  # 输出目录
            '-y',          # 确认所有操作
            '-r'           # 递归处理子目录
        ], capture_output=True, text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
        
        if result.returncode == 0:
            print("7-Zip解压成功!")
            return True
        else:
            print(f"7-Zip解压失败，返回码: {result.returncode}")
            print(f"错误输出: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"7-Zip解压失败: {e}")
        return False

def extract_with_zipfile_backup(archive_path, extract_path):
    """备用方案：使用Python内置zipfile"""
    import zipfile
    try:
        print("尝试使用zipfile作为备用方案...")
        
        # 检查是否为zip格式
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        print("zipfile解压成功!")
        return True
    except zipfile.BadZipFile:
        print("文件不是zip格式，无法使用zipfile解压")
        return False
    except Exception as e:
        print(f"zipfile解压失败: {e}")
        return False

def extract_7z_file(archive_path, extract_path):
    """解压7z文件（主函数）"""
    print(f"开始解压文件到: {extract_path}")
    
    # 检查文件是否存在
    if not os.path.exists(archive_path):
        print(f"错误: 压缩文件不存在: {archive_path}")
        return False
    
    # 优先使用本地7-Zip
    if extract_with_7zip(archive_path, extract_path):
        return True
    
    # 如果7-Zip失败，尝试使用zipfile作为备用方案
    print("7-Zip解压失败，尝试使用zipfile备用方案...")
    return extract_with_zipfile_backup(archive_path, extract_path)

def create_config_file(game_path):
    """创建配置文件"""
    try:
        config_path = os.path.join(game_path, 'LimbusCompany_Data', 'Lang', 'config.json')
        config_dir = os.path.dirname(config_path)
        
        # 确保目录存在
        os.makedirs(config_dir, exist_ok=True)
        
        # 创建配置文件
        config_content = """{
    "lang": "LLC_zh-CN",
    "titleFont": "",
    "contextFont": "",
    "samplingPointSize": 78,
    "padding": 5
}"""
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"配置文件已创建: {config_path}")
        return True
        
    except Exception as e:
        print(f"创建配置文件失败: {e}")
        return False

def cleanup_temp_files(temp_path):
    """清理临时文件"""
    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            print("临时文件已清理")
    except Exception as e:
        print(f"清理临时文件失败: {e}")

def check_write_permission(path):
    """检查写入权限"""
    try:
        test_file = os.path.join(path, 'test_write_permission.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return True
    except Exception as e:
        print(f"警告: 路径 {path} 没有写入权限: {e}")
        return False

def verify_download(file_path):
    """验证下载的文件是否完整"""
    try:
        file_size = os.path.getsize(file_path)
        if file_size < 1000:
            print(f"错误: 下载的文件太小，可能不完整: {file_size} bytes")
            return False
        
        # 检查文件是否可以正常打开（基本验证）
        with open(file_path, 'rb') as f:
            header = f.read(10)
            if len(header) < 10:
                print("错误: 文件头读取失败，文件可能损坏")
                return False
        
        print(f"文件验证通过，大小: {file_size} bytes")
        return True
    except Exception as e:
        print(f"文件验证失败: {e}")
        return False

def download_and_extract(config_path: str = "") -> bool:
    """主函数：下载并解压文件"""
    # 加载配置
    game_path = config_path
    
    if not game_path:
        print("错误: 未配置游戏路径，请在config/settings.json中设置game_path")
        return False
    
    # 检查游戏路径是否存在
    if not os.path.exists(game_path):
        print(f"错误: 游戏路径不存在: {game_path}")
        return False
    
    # 检查写入权限
    if not check_write_permission(game_path):
        print("错误: 没有写入权限，请以管理员身份运行或检查路径权限")
        return False
    
    # 定义要下载的文件列表
    download_files = [
        {
            'name': 'LimbusLocalize',
            'url': 'https://download.zeroasso.top/files/LimbusLocalize_latest.7z',
            'temp_filename': 'LimbusLocalize_latest.7z'
        },
        {
            'name': 'LLCCN-Font',
            'url': 'https://download.zeroasso.top/files/LLCCN-Font.7z',
            'temp_filename': 'LLCCN-Font.7z'
        }
    ]
    
    # 临时文件路径
    temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
    
    success_count = 0
    
    for file_info in download_files:
        print(f"\n{'='*50}")
        print(f"开始处理: {file_info['name']}")
        print(f"{'='*50}")

        if os.path.exists("Font/Context/ChineseFont.ttf") and \
           file_info['name'] == 'LLCCN-Font':
            continue  # 已存在字体文件，跳过下载

        temp_file = os.path.join(temp_dir, file_info['temp_filename'])
        
        try:
            # 下载文件
            print(f"开始下载: {file_info['url']}")
            if not download_file(file_info['url'], temp_file):
                print(f"❌ {file_info['name']} 下载失败")
                continue
            
            # 验证下载的文件
            if not verify_download(temp_file):
                print(f"❌ {file_info['name']} 文件验证失败，请重新下载")
                continue
            
            # 解压文件
            if not extract_7z_file(temp_file, game_path):
                print(f"❌ {file_info['name']} 解压失败")
                continue
            
            print(f"✅ {file_info['name']} 处理成功")
            success_count += 1
            
        except Exception as e:
            print(f"❌ {file_info['name']} 处理过程中出现错误: {e}")
        finally:
            # 清理临时文件
            cleanup_temp_files(temp_file)
    
    # 创建配置文件（只在至少一个文件处理成功时创建）
    if success_count > 0:
        if not create_config_file(game_path):
            print("警告: 配置文件创建失败，但解压已完成")
        
        print(f"\n✅ 文件已成功解压到: {game_path}")
        print(f"✅ 成功处理了 {success_count}/{len(download_files)} 个文件")

        if not os.path.exists("Font/Context/ChineseFont.ttf"):
            import shutil

            print("⚠️ 注意: 本地字体文件缺失，正在修复...")
            # 把 workshop/LLC_zh-CN/Font/ 剪切到当前路径
            source_dir = os.path.join('workshop', 'LLC_zh-CN', 'Font', 'Context', 'ChineseFont.ttf')
            if os.path.exists(source_dir):
                try:
                    shutil.move(source_dir, 'Font'+'/Context')
                    print("✅ 字体文件已移动到 Font/Context/ 下")
                except Exception as e:
                    print(f"❌ 移动字体文件失败: {e}")

        return True
    else:
        print("\n❌ 所有文件处理失败")
        return False

def main(config_path: str = "") -> bool:
    """命令行入口点"""
    print("=" * 50)
    print("LimbusLocalize 下载器 (使用本地7-Zip版)")
    print("支持下载的文件:")
    print("1. LimbusLocalize_latest.7z - 游戏本地化文件")
    print("2. LLCCN-Font.7z - 中文字体文件")
    print("=" * 50)
    
    success = download_and_extract(config_path=config_path)
    
    if success:
        print("\n✅ 操作成功完成!")
    else:
        print("\n❌ 操作失败，请检查错误信息")
    
    return success

if __name__ == "__main__":
    main()