import pymysql
import os

def set_bubble_json_files(host, port, user, password, database, battle_speech_file, cultivation_file, mowe_file):
    """
    在faust_launcher表格中设置三个JSON文件的内容
    
    Args:
        host: MySQL服务器地址
        port: 端口号
        user: 用户名
        password: 密码
        database: 数据库名
        battle_speech_file: BattleSpeechBubbleDlg.json文件内容
        cultivation_file: BattleSpeechBubbleDlg_Cultivation.json文件内容
        mowe_file: BattleSpeechBubbleDlg_mowe.json文件内容
    """
    try:
        # 连接MySQL数据库
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # 检查表格是否存在
            cursor.execute("SHOW TABLES LIKE 'faust_launcher'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                # 如果表格不存在，创建表格
                create_table_query = """
                CREATE TABLE faust_launcher (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    battle_speech_bubble LONGTEXT,
                    battle_speech_bubble_cultivation LONGTEXT,
                    battle_speech_bubble_mowe LONGTEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
                """
                cursor.execute(create_table_query)
                print("✅ 创建faust_launcher表格成功")
            
            # 检查记录是否存在
            cursor.execute("SELECT COUNT(*) as count FROM faust_launcher")
            record_count = cursor.fetchone()['count'] # type: ignore
            
            if record_count == 0:
                # 插入新记录
                insert_query = """
                INSERT INTO faust_launcher (battle_speech_bubble, battle_speech_bubble_cultivation, battle_speech_bubble_mowe) 
                VALUES (%s, %s, %s)
                """
                cursor.execute(insert_query, (battle_speech_file, cultivation_file, mowe_file))
                print("✅ 插入JSON文件记录成功")
            else:
                # 更新现有记录
                update_query = """
                UPDATE faust_launcher SET 
                battle_speech_bubble = %s, 
                battle_speech_bubble_cultivation = %s, 
                battle_speech_bubble_mowe = %s 
                WHERE id = 1
                """
                cursor.execute(update_query, (battle_speech_file, cultivation_file, mowe_file))
                print("✅ 更新JSON文件记录成功")
            
            # 验证设置
            cursor.execute("SELECT battle_speech_bubble, battle_speech_bubble_cultivation, battle_speech_bubble_mowe FROM faust_launcher WHERE id = 1")
            result = cursor.fetchone()
            
            if result:
                print(f"✅ JSON文件设置成功")
                print(f"  - BattleSpeechBubbleDlg.json: {len(result['battle_speech_bubble'])} 字符")
                print(f"  - BattleSpeechBubbleDlg_Cultivation.json: {len(result['battle_speech_bubble_cultivation'])} 字符")
                print(f"  - BattleSpeechBubbleDlg_mowe.json: {len(result['battle_speech_bubble_mowe'])} 字符")
        
        # 提交更改
        connection.commit()
        
        return True
        
    except pymysql.Error as e:
        print(f"❌ MySQL错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
    finally:
        # 确保连接关闭
        if 'connection' in locals() and connection.open: # type: ignore
            connection.close() # type: ignore

def get_bubble_json_files(host, port, user, password, database):
    """
    从faust_launcher表格中获取三个JSON文件的内容
    
    Args:
        host: MySQL服务器地址
        port: 端口号
        user: 用户名
        password: 密码
        database: 数据库名
        
    Returns:
        tuple: (battle_speech_file, cultivation_file, mowe_file) 如果不存在则返回(None, None, None)
    """
    try:
        # 连接MySQL数据库
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # 检查表格是否存在
            cursor.execute("SHOW TABLES LIKE 'faust_launcher'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                print("⚠️ faust_launcher表格不存在")
                return None, None, None
            
            # 查询JSON文件字段
            cursor.execute("SELECT battle_speech_bubble, battle_speech_bubble_cultivation, battle_speech_bubble_mowe FROM faust_launcher WHERE id = 1")
            result = cursor.fetchone()
            
            if result and result['battle_speech_bubble'] and result['battle_speech_bubble_cultivation'] and result['battle_speech_bubble_mowe']:
                print("✅ 获取JSON文件成功")
                return result['battle_speech_bubble'], result['battle_speech_bubble_cultivation'], result['battle_speech_bubble_mowe']
            else:
                print("⚠️ JSON文件字段为空或记录不存在")
                return None, None, None
        
    except pymysql.Error as e:
        print(f"❌ MySQL错误: {e}")
        return None, None, None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None, None, None
    finally:
        # 确保连接关闭
        if 'connection' in locals() and connection.open: # type: ignore
            connection.close() # type: ignore

def upload_bubble_files_from_temp(host, port, user, password, database, temp_dir=None):
    """
    上传temp目录中的三个JSON文件到数据库
    
    Args:
        host: MySQL服务器地址
        port: 端口号
        user: 用户名
        password: 密码
        database: 数据库名
        temp_dir: temp目录路径，如果为None则使用默认路径
        
    Returns:
        bool: 上传是否成功
    """
    if temp_dir is None:
        temp_dir = 'temp'
    
    # 检查temp目录是否存在
    if not os.path.exists(temp_dir):
        print(f"❌ temp目录不存在: {temp_dir}")
        return False
    
    # 检查三个JSON文件是否存在
    battle_speech_path = os.path.join(temp_dir, 'BattleSpeechBubbleDlg.json')
    cultivation_path = os.path.join(temp_dir, 'BattleSpeechBubbleDlg_Cultivation.json')
    mowe_path = os.path.join(temp_dir, 'BattleSpeechBubbleDlg_mowe.json')
    
    if not os.path.exists(battle_speech_path):
        print(f"❌ 文件不存在: {battle_speech_path}")
        return False
    if not os.path.exists(cultivation_path):
        print(f"❌ 文件不存在: {cultivation_path}")
        return False
    if not os.path.exists(mowe_path):
        print(f"❌ 文件不存在: {mowe_path}")
        return False
    
    try:
        # 读取三个JSON文件
        with open(battle_speech_path, 'r', encoding='utf-8') as f:
            battle_speech_content = f.read()
        
        with open(cultivation_path, 'r', encoding='utf-8') as f:
            cultivation_content = f.read()
        
        with open(mowe_path, 'r', encoding='utf-8') as f:
            mowe_content = f.read()
        
        print(f"✅ 读取JSON文件成功")
        print(f"  - BattleSpeechBubbleDlg.json: {len(battle_speech_content)} 字符")
        print(f"  - BattleSpeechBubbleDlg_Cultivation.json: {len(cultivation_content)} 字符")
        print(f"  - BattleSpeechBubbleDlg_mowe.json: {len(mowe_content)} 字符")
        
        # 上传到数据库
        if set_bubble_json_files(host, port, user, password, database, 
                               battle_speech_content, cultivation_content, mowe_content):
            print("✅ JSON文件上传到数据库成功")
            return True
        else:
            return False
        
    except Exception as e:
        print(f"❌ 上传JSON文件失败: {e}")
        return False

def download_bubble_files_to_game(host, port, user, password, database, game_path):
    """
    从数据库获取三个JSON文件并保存到游戏目录
    
    Args:
        host: MySQL服务器地址
        port: 端口号
        user: 用户名
        password: 密码
        database: 数据库名
        game_path: 游戏目录路径
        
    Returns:
        bool: 下载是否成功
    """
    # 从数据库获取三个JSON文件内容
    print("正在从数据库获取JSON文件内容...")
    battle_speech, cultivation, mowe = get_bubble_json_files(host, port, user, password, database)
    
    if not battle_speech or not cultivation or not mowe:
        print("❌ 无法从数据库获取JSON文件内容")
        return False
    
    print(f"✅ 成功获取三个JSON文件内容")
    print(f"  - BattleSpeechBubbleDlg.json: {len(battle_speech)} 字符")
    print(f"  - BattleSpeechBubbleDlg_Cultivation.json: {len(cultivation)} 字符")
    print(f"  - BattleSpeechBubbleDlg_mowe.json: {len(mowe)} 字符")
    
    # 检查游戏路径是否存在
    if not os.path.exists(game_path):
        print(f"❌ 游戏路径不存在: {game_path}")
        return False
    
    # 目标目录：游戏目录下的LimbusCompany_Data/Lang/LLC_zh-CN
    target_dir = os.path.join(game_path, 'LimbusCompany_Data', 'Lang', 'LLC_zh-CN')
    
    try:
        # 确保目标目录存在
        os.makedirs(target_dir, exist_ok=True)
        
        # 保存BattleSpeechBubbleDlg.json
        battle_speech_path = os.path.join(target_dir, 'BattleSpeechBubbleDlg.json')
        with open(battle_speech_path, 'w', encoding='utf-8') as f:
            f.write(battle_speech)
        print(f"✅ 保存 BattleSpeechBubbleDlg.json 成功")
        
        # 保存BattleSpeechBubbleDlg_Cultivation.json
        cultivation_path = os.path.join(target_dir, 'BattleSpeechBubbleDlg_Cultivation.json')
        with open(cultivation_path, 'w', encoding='utf-8') as f:
            f.write(cultivation)
        print(f"✅ 保存 BattleSpeechBubbleDlg_Cultivation.json 成功")
        
        # 保存BattleSpeechBubbleDlg_mowe.json
        mowe_path = os.path.join(target_dir, 'BattleSpeechBubbleDlg_mowe.json')
        with open(mowe_path, 'w', encoding='utf-8') as f:
            f.write(mowe)
        print(f"✅ 保存 BattleSpeechBubbleDlg_mowe.json 成功")
        
        print(f"✅ JSON文件已成功保存到: {target_dir}")
        return True
        
    except Exception as e:
        print(f"❌ 保存JSON文件失败: {e}")
        return False

def check_bubble_files_exist(host, port, user, password, database):
    """
    检查三个JSON文件字段是否存在且不为空
    
    Args:
        host: MySQL服务器地址
        port: 端口号
        user: 用户名
        password: 密码
        database: 数据库名
        
    Returns:
        bool: 三个JSON文件字段是否存在且不为空
    """
    battle_speech, cultivation, mowe = get_bubble_json_files(host, port, user, password, database)
    return battle_speech is not None and cultivation is not None and mowe is not None

def get_all_records(host, port, user, password, database):
    """
    获取faust_launcher表格中的所有记录
    
    Args:
        host: MySQL服务器地址
        port: 端口号
        user: 用户名
        password: 密码
        database: 数据库名
        
    Returns:
        list: 所有记录的列表
    """
    try:
        # 连接MySQL数据库
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # 检查表格是否存在
            cursor.execute("SHOW TABLES LIKE 'faust_launcher'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                print("⚠️ faust_launcher表格不存在")
                return []
            
            # 查询所有记录
            cursor.execute("SELECT * FROM faust_launcher ORDER BY id")
            results = cursor.fetchall()
            
            print(f"✅ 获取到 {len(results)} 条记录")
            return results
        
    except pymysql.Error as e:
        print(f"❌ MySQL错误: {e}")
        return []
    except Exception as e:
        print(f"❌ 错误: {e}")
        return []
    finally:
        # 确保连接关闭
        if 'connection' in locals() and connection.open: # type: ignore
            connection.close() # type: ignore

db_config = {
    'host': 'mysql2.sqlpub.com',
    'port': 3307,
    'user': 'mirroradmin',  # 用户名
    'password': 'cZGus9c0TrfhaLyd',  # 密码
    'database': 'mirrorchat_data'   # 数据库名
}

# 使用示例
if __name__ == "__main__":
    print("=" * 50)
    print("SQL Loader - JSON文件管理器")
    print("=" * 50)
    print("1. 上传temp目录中的JSON文件到数据库")
    print("2. 从数据库下载JSON文件到游戏目录")
    print("=" * 50)
    
    choice = input("请选择操作 (1或2): ").strip()

    success = True
    
    if choice == "1":
        success = upload_bubble_files_from_temp(**db_config)
    elif choice == "2":
        game_path = input("请输入游戏目录路径: ").strip()
        if not game_path:
            print("❌ 游戏目录路径不能为空")
        else:
            success = download_bubble_files_to_game(**db_config, game_path=game_path)
    else:
        print("❌ 无效选择")
        success = False
    
    if success:
        print("\n✅ 操作完成!")
    else:
        print("\n❌ 操作失败!")