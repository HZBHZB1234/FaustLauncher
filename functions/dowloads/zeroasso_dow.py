import os
import requests
import subprocess
import tkinter as tk
from tkinter import ttk
import threading
import time
from functions.dowloads.github_ulits import GitHubReleaseFetcher
from functions.dowloads.dow_ulits import check_need_up_translate
from functions.window_ulits import center_window

# 7-Zip可执行文件路径
SEVEN_ZIP_PATH = r"7-Zip\7z.exe"

class DownloadGUI:
    """简化版下载GUI界面"""
    
    def __init__(self, parent, config_path: str = ""):
        self.root = tk.Toplevel(parent)
        self.root.withdraw()  # 先隐藏，防止闪烁
        self.root.title("下载中...")
        self.root.geometry("500x150")
        self.root.resizable(False, False)

        self.config_path = config_path
        self.is_downloading = True
        
        # 创建界面
        self.create_widgets()
        
        # 初始化后立即开始下载
        self.start_download()
        
    def create_widgets(self):
        """创建简化界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 当前文件
        self.current_file_var = tk.StringVar(value="正在初始化...")
        current_file_label = ttk.Label(main_frame, textvariable=self.current_file_var, font=('Microsoft YaHei', 10, 'bold'))
        current_file_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # 进度信息框架
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        # 进度百分比
        self.progress_text_var = tk.StringVar(value="0%")
        progress_label = ttk.Label(info_frame, textvariable=self.progress_text_var, font=('Microsoft YaHei', 9))
        progress_label.pack(side=tk.LEFT)
        
        # 下载速度
        self.speed_var = tk.StringVar(value="速度: 0 KB/s")
        speed_label = ttk.Label(info_frame, textvariable=self.speed_var, font=('Microsoft YaHei', 9))
        speed_label.pack(side=tk.RIGHT)
        
    def update_progress(self, percent, downloaded, total, speed):
        """更新进度显示"""
        self.progress_var.set(percent)
        
        # 格式化文件大小
        if total >= 1024*1024*1024:  # GB
            downloaded_str = f"{downloaded/1024/1024/1024:.1f}GB"
            total_str = f"{total/1024/1024/1024:.1f}GB"
        elif total >= 1024*1024:  # MB
            downloaded_str = f"{downloaded/1024/1024:.1f}MB"
            total_str = f"{total/1024/1024:.1f}MB"
        elif total >= 1024:  # KB
            downloaded_str = f"{downloaded/1024:.1f}KB"
            total_str = f"{total/1024:.1f}KB"
        else:  # Bytes
            downloaded_str = f"{downloaded}B"
            total_str = f"{total}B"
            
        self.progress_text_var.set(f"{percent:.1f}% ({downloaded_str}/{total_str})")
        self.speed_var.set(f"速度: {speed:.1f} KB/s")
        self.root.update_idletasks()
        
    def start_download(self):
        """开始下载"""
        self.is_downloading = True
        
        # 在新线程中运行下载
        thread = threading.Thread(target=self.run_download)
        thread.daemon = True
        thread.start()
        
    def run_download(self):
        """运行下载任务"""
        try:
            success = download_and_extract_gui(self, self.config_path)
            if success:
                self.root.destroy()
            else:
                self.current_file_var.set("❌ 下载失败，请检查错误信息")
        except Exception as e:
            self.current_file_var.set(f"❌ 下载过程中出现错误: {e}")
        finally:
            self.is_downloading = False

def get_github_release_url() -> tuple[str, str] | None:
    """从GitHub Release获取7z文件下载链接"""
    try:
        fetcher = GitHubReleaseFetcher(
            repo_owner="LocalizeLimbusCompany",
            repo_name="LocalizeLimbusCompany",
            use_proxy=True,
            proxy_url="https://gh-proxy.org/"
        )
        
        latest_release = fetcher.get_latest_release()
        if not latest_release:
            return None
            
        # 查找7z文件
        windows_assets = latest_release.get_assets_by_extension(".7z")
        for asset in windows_assets:
            if "LimbusLocalize" in asset.name:
                return asset.download_url, latest_release.name
                
        return None
    except Exception as e:
        print(f"获取GitHub Release失败: {e}")
        return None


# 保留原有的函数（用于命令行模式）
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
    
def download_file_with_gui(url, local_filename, gui, file_name):
    """带GUI进度显示的下载文件函数"""
    try:
        # 更新GUI状态
        gui.current_file_var.set(f"正在下载: {file_name}")
        
        # 发送请求
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # 获取文件大小
        total_size = int(response.headers.get('content-length', 0))
        if total_size == 0:
            # 如果无法获取文件大小，使用默认值
            total_size = 10 * 1024 * 1024  # 10MB作为默认值
        
        block_size = 8192
        
        # 创建目录
        os.makedirs(os.path.dirname(local_filename), exist_ok=True)
        
        # 开始时间
        start_time = time.time()
        downloaded_size = 0
        last_update_time = start_time
        last_downloaded_size = 0
        
        # 平滑进度条相关变量
        current_animated_percent = 0.0  # 当前动画显示的百分比
        target_percent = 0.0  # 目标百分比
        animation_speed = 0.15  # 动画速度系数，值越小越平滑
        last_animation_time = start_time
        
        # 下载文件
        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if not gui.is_downloading:
                    return False
                    
                if chunk:
                    speed = 0
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # 计算实时下载速度（每秒更新）
                    current_time = time.time()

                    elapsed_time = current_time - last_update_time
                    downloaded_since_last = downloaded_size - last_downloaded_size
                    
                    speed = downloaded_since_last / elapsed_time / 1024  # KB/s
                    
                    # 计算目标百分比
                    target_percent = (downloaded_size / total_size) * 100
                        
                    # 平滑渐变效果：持续向目标百分比移动
                    animation_elapsed = current_time - last_animation_time
                    if animation_elapsed > 0.01:  # 每0.01秒更新一次动画
                        if current_animated_percent < target_percent:
                            # 使用缓动函数实现平滑过渡
                            progress_diff = target_percent - current_animated_percent
                            current_animated_percent += progress_diff * animation_speed
                            
                            # 确保不超过目标值
                            if current_animated_percent > target_percent:
                                current_animated_percent = target_percent
                        
                        # 显示下载进度（使用平滑后的百分比）
                        gui.update_progress(current_animated_percent, downloaded_size, total_size, speed)
                        last_animation_time = current_time
                    
                    last_update_time = current_time
                    last_downloaded_size = downloaded_size
        
        # 下载完成后，平滑过渡到100%并停止震动
        final_animation_start = time.time()
        while current_animated_percent < 99.9:
            current_time = time.time()
            animation_elapsed = current_time - final_animation_start
            
            # 平滑过渡到100%
            if current_animated_percent < target_percent:
                progress_diff = target_percent - current_animated_percent
                current_animated_percent += progress_diff * animation_speed * 2  # 加速完成
            else:
                # 如果已经达到目标值，继续平滑到100%
                progress_diff = 100 - current_animated_percent
                current_animated_percent += progress_diff * animation_speed * 1.5
            
            if current_animated_percent > 99.9:
                current_animated_percent = 100
            
            gui.update_progress(current_animated_percent, downloaded_size, total_size, 0)
            time.sleep(0.01)  # 短暂延迟让动画更平滑
            
            # 防止无限循环
            if animation_elapsed > 2.0:  # 最多2秒完成动画
                current_animated_percent = 100
                break
        
        return True
        
    except requests.exceptions.RequestException as e:
        gui.current_file_var.set(f"❌ 下载失败: {e}")
        return False
    except Exception as e:
        gui.current_file_var.set(f"❌ 下载过程中出现错误: {e}")
    
def download_and_extract_gui(gui, config_path: str = "") -> bool:
    """带GUI的下载和解压主函数"""
    # 加载配置
    game_path = config_path
    
    if not game_path:
        gui.current_file_var.set("❌ 错误: 未配置游戏路径")
        return False
    
    # 检查游戏路径是否存在
    if not os.path.exists(game_path):
        gui.current_file_var.set(f"❌ 错误: 游戏路径不存在: {game_path}")
        return False
    
    # 检查写入权限
    if not check_write_permission(game_path):
        gui.current_file_var.set("❌ 错误: 没有写入权限")
        return False

    # 获取GitHub Release下载链接
    gui.current_file_var.set("正在获取 GitHub Release 信息...")
    github_url = ""
    timeout_counter = 0
    need_update_translate = True

    while not github_url:
        if timeout_counter >= 5:
            gui.current_file_var.set("❌ 获取GitHub Release信息失败，已达最大重试次数")
            return False
        
        github_url, name = get_github_release_url() # type: ignore

        if not github_url:
            gui.current_file_var.set("❌ 获取GitHub Release信息失败，准备重试...")
            timeout_counter += 1
            time.sleep(3)
        else:
            print (f"获取到下载链接: {github_url}\n 零协汉化版本号: {name}")
            if not check_need_up_translate(name):
                print("当前已是最新汉化版本，无需更新。")
                need_update_translate = False
            else:
                print("检测到新版本，准备更新...")
    
    # 定义要下载的文件列表
    download_files = [
        {
            'name': 'LimbusLocalize',
            'url': github_url,
            'temp_filename': 'LimbusLocalize_latest.7z'
        },
        {
            'name': 'LLCCN-Font',
            'url': 'https://lz.qaiu.top/parser?url=https://wwbet.lanzoum.com/igRGn3ezd23g&pwd=do1n',
            'temp_filename': 'LLCCN-Font.7z'
        }
    ]
    
    # 临时文件路径
    temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    success_count = 0
    
    for file_info in download_files:
        if not gui.is_downloading:
            break
            
        # 检查字体文件是否已存在
        if os.path.exists("Font/Context/ChineseFont.ttf") and \
           file_info['name'] == 'LLCCN-Font':
            success_count += 1
            continue
        if not need_update_translate and \
            file_info['name'] == 'LimbusLocalize':
            success_count += 1
            continue

        temp_file = os.path.join(temp_dir, file_info['temp_filename'])
        
        try:
            # 下载文件
            if not download_file_with_gui(file_info['url'], temp_file, gui, file_info['name']):
                continue
            
            # 验证下载的文件
            if not verify_download(temp_file):
                continue
            
            # 解压文件
            if not extract_7z_file(temp_file, game_path):
                continue
            
            success_count += 1
            
        except Exception as e:
            continue
        finally:
            # 清理临时文件
            cleanup_temp_files(temp_file)
    
    # 创建配置文件（只在至少一个文件处理成功时创建）
    if success_count > 0:
        create_config_file(game_path)
        
        # 检查字体文件
        if not os.path.exists("Font/Context/ChineseFont.ttf"):
            import shutil
            source_dir = "workshop/LimbusCompany_Data/Lang/LLC_zh-CN/Font/Context/ChineseFont.ttf"
            if os.path.exists(source_dir):
                print("复制字体文件到Font/Context目录...")
                try:
                    shutil.move(source_dir, 'Font/Context')
                except Exception:
                    pass

        return True
    else:
        return False

def main_gui(parrent, config_path: str = ""):
    """GUI入口点"""
    gui = DownloadGUI(parrent, config_path)
    
    # 居中显示窗口
    center_window(gui.root)
    
    return gui