import os
import hashlib
import concurrent.futures
from collections import defaultdict
from itertools import repeat
import threading
import json
import time


def get_video_files(directory):
    """
    获取指定目录及其子目录中的所有视频文件。
    
    Args:
        directory (str): 要扫描视频文件的目录
        
    Returns:
        list: 视频文件路径列表
    """
    video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.f4v', '.flv', '.webm', '.m4v', '.mpg', '.mpeg', '.3gp', '.ts', '.rm', '.rmvb'}
    video_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1].lower() in video_extensions:
                video_files.append(os.path.join(root, file))
                
    return video_files


def calculate_file_hash(file_path, chunk_size=2*1024*1024):
    """
    计算文件的MD5哈希值。
    
    Args:
        file_path (str): 文件路径
        chunk_size (int): 每次读取的块大小，设置为2MB以提高大文件处理效率
        
    Returns:
        str: 文件的MD5哈希值，如果出错则返回None
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"计算 {file_path} 的哈希值时出错: {e}")
        return None


def extract_base_name(file_path):
    """
    提取不含扩展名和常见编号方案的文件基本名称。
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        str: 不含扩展名和常见编号的基本名称
    """
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    # 移除常见的编号模式如 _001, -01, 等等
    import re
    base_name = re.sub(r'[_\-]\d+$', '', base_name)
    return base_name


def find_duplicates_by_hash_fast(video_files, max_workers=4, progress_file=None):
    """
    通过并行计算哈希值查找重复的视频文件。
    
    Args:
        video_files (list): 视频文件路径列表
        max_workers (int): 最大并行工作线程数
        progress_file (str): 进度文件路径
        
    Returns:
        dict: 以哈希值为键，文件路径列表为值的字典
    """
    hash_dict = defaultdict(list)
    lock = threading.Lock()
    
    # 加载之前的进度（如果存在）
    processed_files = set()
    if progress_file and os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
                processed_files = set(progress_data.get('processed_files', []))
            print(f"已加载 {len(processed_files)} 个已处理文件的进度")
        except Exception as e:
            print(f"加载进度文件时出错: {e}")
    
    # 保存进度的函数
    def save_progress():
        if progress_file:
            try:
                progress_data = {
                    'processed_files': list(processed_files),
                    'last_update': time.time()
                }
                with open(progress_file, 'w') as f:
                    json.dump(progress_data, f)
            except Exception as e:
                print(f"保存进度时出错: {e}")
    
    def process_file(file_path):
        # 如果已经处理过，跳过
        if file_path in processed_files:
            return
            
        file_hash = calculate_file_hash(file_path)
        if file_hash:
            with lock:
                hash_dict[file_hash].append(file_path)
                processed_files.add(file_path)
                
                # 每处理100个文件保存一次进度
                if len(processed_files) % 100 == 0:
                    save_progress()
    
    total_files = len(video_files)
    print(f"开始处理 {total_files} 个文件...")
    
    # 使用线程池并行处理文件哈希计算
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_file = {executor.submit(process_file, file_path): file_path 
                         for file_path in video_files}
        
        # 监控进度
        completed = 0
        for future in concurrent.futures.as_completed(future_to_file):
            completed += 1
            if completed % 100 == 0 or completed == total_files:
                print(f"已处理 {completed}/{total_files} 个文件 ({completed/total_files*100:.1f}%)")
    
    # 最后保存一次进度
    save_progress()
    
    # 过滤掉只有一个文件的条目（无重复）
    duplicates = {hash_val: file_list for hash_val, file_list in hash_dict.items() if len(file_list) > 1}
    
    return duplicates


def find_duplicates_by_name(video_files):
    """
    通过比较基本名称查找可能重复的视频文件。
    
    Args:
        video_files (list): 视频文件路径列表
        
    Returns:
        dict: 以基本名称为键，文件路径列表为值的字典
    """
    name_dict = defaultdict(list)
    
    for file_path in video_files:
        base_name = extract_base_name(file_path)
        name_dict[base_name].append(file_path)
    
    # 过滤掉只有一个文件的条目（无重复）
    duplicates = {name: file_list for name, file_list in name_dict.items() if len(file_list) > 1}
    
    return duplicates


def format_file_size(file_path):
    """
    以人类可读的格式显示文件大小。
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        str: 格式化的文件大小
    """
    try:
        size = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    except:
        return "未知大小"


def save_results_to_file(duplicates, output_file, method):
    """
    将重复文件结果保存到文件中。
    
    Args:
        duplicates (dict): 重复文件字典
        output_file (str): 输出文件路径
        method (str): 检测方法 ("hash" 或 "name")
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            if method == "hash":
                f.write("重复文件检测结果（基于哈希值）\n")
                f.write("=" * 50 + "\n\n")
            else:
                f.write("可能重复的文件检测结果（基于文件名）\n")
                f.write("=" * 50 + "\n\n")
            
            if not duplicates:
                f.write("未找到重复文件。\n")
                return
            
            f.write(f"共发现 {len(duplicates)} 组重复文件:\n\n")
            
            for i, (key, file_list) in enumerate(duplicates.items(), 1):
                if method == "hash":
                    f.write(f"{i}. 重复组 (哈希值: {key[:16]}...):\n")
                else:
                    f.write(f"{i}. 相似名称组 (基本名称: {key}):\n")
                
                # 将相同组的所有文件放在一行，用分号分隔
                file_info_list = [f"{file_path} ({format_file_size(file_path)})" for file_path in file_list]
                f.write("; ".join(file_info_list) + "\n\n")
        
        print(f"结果已保存到: {output_file}")
    except Exception as e:
        print(f"保存结果文件时出错: {e}")


def main():
    # 获取用户输入的目录路径
    directory = input("请输入要扫描的目录路径（直接回车默认为当前目录）: ").strip()
    if not directory:
        directory = "."
    
    directory = os.path.abspath(directory)
    
    if not os.path.exists(directory):
        print(f"错误: 目录 '{directory}' 不存在。")
        return
    
    if not os.path.isdir(directory):
        print(f"错误: '{directory}' 不是一个目录。")
        return
    
    print(f"正在扫描目录: {directory}")
    video_files = get_video_files(directory)
    total_files = len(video_files)
    print(f"找到 {total_files} 个视频文件。")
    
    if not video_files:
        print("未找到视频文件。")
        return
    
    # 获取用户选择的检测方法
    print("\n请选择检测重复文件的方法:")
    print("1. 哈希值检测（精确但较慢，适用于查找完全相同的文件）")
    print("2. 文件名检测（快速但可能有误报，适用于查找可能相似的文件）")
    choice = input("请输入选项（1 或 2，默认为 1）: ").strip()
    
    # 生成结果和进度文件名
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    if choice == "2":
        method = "name"
        output_file = f"duplicate_results_name_{timestamp}.txt"
        print("正在通过文件名查找相似文件...")
        duplicates = find_duplicates_by_name(video_files)
        save_results_to_file(duplicates, output_file, method)
    else:
        method = "hash"
        output_file = f"duplicate_results_hash_{timestamp}.txt"
        progress_file = f"duplicate_progress_{timestamp}.json"
        print("正在通过文件哈希值查找重复文件...")
        print("使用并行处理加速计算，请稍候...")
        print(f"进度将保存到: {progress_file}")
        duplicates = find_duplicates_by_hash_fast(video_files, progress_file=progress_file)
        save_results_to_file(duplicates, output_file, method)
        
        # 删除进度文件（任务完成）
        if os.path.exists(progress_file):
            try:
                os.remove(progress_file)
                print("已删除临时进度文件")
            except Exception as e:
                print(f"删除进度文件时出错: {e}")


if __name__ == "__main__":
    main()