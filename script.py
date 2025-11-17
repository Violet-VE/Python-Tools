import yaml
import subprocess
import re
import requests
from urllib.parse import urlparse, parse_qs
import os
import json


def load_config():
    with open('config.yml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        return config


def get_bilibili_cheese_title(ss_id, bilibili_cookies_path):
    """
    从Bilibili API获取cheese课程的标题
    :param ss_id: cheese课程的ss ID
    :param bilibili_cookies_path: Bilibili cookies文件路径
    :return: 课程标题
    """
    try:
        # 读取cookies文件
        with open(bilibili_cookies_path, 'r', encoding='utf-8') as f:
            cookies_data = f.read()
        
        # 构造请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Cookie': cookies_data
        }
        
        # 请求API获取已购买的课程列表
        api_url = "https://api.bilibili.com/pugv/pay/web/my/paid?ps=10&pn=1"
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                courses = data.get('data', {}).get('data', [])
                for course in courses:
                    if str(course.get('id')) == str(ss_id):
                        return course.get('title', f'ss{ss_id}')
        
        # 如果API请求失败或未找到，返回默认名称
        return f'ss{ss_id}'
    
    except Exception as e:
        print(f"获取Bilibili cheese标题时发生错误: {e}")
        return f'ss{ss_id}'


def get_bilibili_bangumi_title(url, bilibili_cookies_path):
    """
    从Bilibili番剧页面HTML中获取番剧标题
    :param url: 番剧URL
    :param bilibili_cookies_path: Bilibili cookies文件路径
    :return: 番剧标题
    """
    try:
        # 读取cookies文件
        with open(bilibili_cookies_path, 'r', encoding='utf-8') as f:
            cookies_data = f.read()
        
        # 构造请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Cookie': cookies_data
        }
        
        # 请求番剧页面
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            # 使用正则表达式查找class包含mediainfo_mediaTitle__的a标签的title属性
            import re
            pattern = r'<a[^>]*class="[^"]*mediainfo_mediaTitle__[^"]*"[^>]*title="([^"]*)"'
            match = re.search(pattern, response.text)
            if match:
                return match.group(1)
        
        # 如果未找到，从URL中提取ss ID作为默认名称
        video_id = url.split("/")[-1].split("?")[0]
        return video_id
    
    except Exception as e:
        print(f"获取Bilibili番剧标题时发生错误: {e}")
        # 从URL中提取ss ID作为默认名称
        video_id = url.split("/")[-1].split("?")[0]
        return video_id


def execute_ytb_command(ytb_path, *args):
    """
    执行yt-dlp命令并实时输出结果
    :param ytb_path: yt-dlp可执行文件路径
    :param args: 命令行参数
    """
    # 使用UTF-8编码构建命令字符串用于显示
    cmd_str = f"正在执行: {ytb_path} {' '.join(args)}"
    print(cmd_str)

    try:
        # 确保yt-dlp路径存在
        if not os.path.exists(ytb_path):
            print(f"错误: yt-dlp路径不存在: {ytb_path}")
            return False, "yt-dlp路径不存在"

        # 使用Popen实时输出命令执行过程，使用GB2312编码
        process = subprocess.Popen(
            [ytb_path] + list(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='gb2312',
            errors='ignore',
            bufsize=1,
            universal_newlines=True
        )

        # 实时读取输出
        output_lines = []
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
                output_lines.append(output.strip())

        # 等待进程结束并获取返回码
        return_code = process.poll()
        return return_code == 0, "\n".join(output_lines)

    except FileNotFoundError:
        error_msg = f"错误: 找不到可执行文件: {ytb_path}"
        print(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"执行命令时发生错误: {e}"
        print(error_msg)
        return False, error_msg


def extract_fid_from_url(url):
    """
    从收藏夹URL中提取fid参数
    :param url: 收夹URL
    :return: fid值
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get('fid', [None])[0]


def extract_season_info_from_url(url):
    """
    从合集URL中提取mid和season_id参数
    :param url: 合集URL
    :return: (mid, season_id)值
    """
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip('/').split('/')
    mid = path_parts[1] if len(path_parts) > 1 else None

    query_params = parse_qs(parsed_url.query)
    season_id = query_params.get('type', [None])[0]

    return mid, season_id


def generate_api_url(fid, is_created_fav=False):
    """
    根据fid生成API URL
    :param fid: 收藏夹ID
    :param is_created_fav: 是否为创建的收藏夹
    :return: API URL
    """
    if is_created_fav:
        return f"https://api.bilibili.com/x/v3/fav/resource/list?media_id={fid}&pn=1&ps=36&keyword=&order=mtime&type=0&tid=0&platform=web&web_location=333.1387"
    else:
        return f"https://api.bilibili.com/x/space/fav/season/list?season_id={fid}&pn=1&ps=36&web_location=333.1387"


def generate_season_api_url(mid, season_id):
    """
    根据mid和season_id生成合集API URL
    :param mid: 用户ID
    :param season_id: 合集ID
    :return: API URL
    """
    return f"https://api.bilibili.com/x/polymer/web-space/seasons_archives_list?mid={mid}&season_id={season_id}&sort_reverse=false&page_size=30&page_num=1&web_location=333.1387"


def fetch_fav_list_data(api_url):
    """
    获取收藏夹数据
    :param api_url: API URL
    :return: 响应数据
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(api_url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"HTTP错误: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {e}")
        return None
    except Exception as e:
        print(f"解析响应时发生错误: {e}")
        return None


def sanitize_filename(filename):
    """
    清理文件名中的非法字符
    :param filename: 原始文件名
    :return: 清理后的文件名
    """
    # 移除Windows不允许的字符
    illegal_chars = '\\/:<>"|?*'
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    
    # 移除控制字符和其他不可见字符（包括退格符\x08等）
    cleaned_chars = []
    for char in filename:
        # 保留常规字符，移除控制字符（除了常见的空白字符）
        if char == ' ' or (32 <= ord(char) <= 126) or ord(char) > 127:
            cleaned_chars.append(char)
        else:
            # 用下划线替换控制字符
            cleaned_chars.append('_')
    filename = ''.join(cleaned_chars)
    
    # 限制文件名长度以避免路径过长问题
    if len(filename) > 150:
        filename = filename[:150]
    
    return filename.strip()


def is_video_file_valid(file_path):
    """
    检查视频文件是否有效
    :param file_path: 视频文件路径
    :return: (is_valid, reason)
    """
    if not os.path.exists(file_path):
        return False, "文件不存在"

    # 检查文件大小
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        return False, "文件大小为0"

    # 对于MP4文件，可以进行更详细的检查
    if file_path.lower().endswith('.mp4'):
        # 简单检查文件头
        try:
            with open(file_path, 'rb') as f:
                header = f.read(12)
                if len(header) >= 12 and header[4:8] != b'ftyp':
                    return False, "不是有效的MP4文件"
        except Exception as e:
            return False, f"文件读取错误: {e}"

    return True, "文件有效"


def get_downloaded_videos(download_path):
    """
    获取已下载的视频文件列表
    :param download_path: 下载路径
    :return: 视频文件列表
    """
    video_files = []
    if os.path.exists(download_path):
        for root, dirs, files in os.walk(download_path):
            for file in files:
                if file.lower().endswith('.mp4'):
                    video_files.append(os.path.join(root, file))
    return video_files


def download_bilibili_fav_list(config, url, custom_path=None):
    """
    下载B站收藏夹视频
    :param config: 配置信息
    :param url: 收藏夹URL
    :param custom_path: 自定义路径
    """
    # 提取fid
    fid = extract_fid_from_url(url)
    if not fid:
        print("无法从URL中提取fid参数，请检查URL格式")
        return False, "无法从URL中提取fid参数"

    # 判断是否为创建的收藏夹 (ftype=create)
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    is_created_fav = query_params.get('ftype', [''])[0] == 'create'

    # 生成API URL
    api_url = generate_api_url(fid, is_created_fav)

    # 获取数据
    data = fetch_fav_list_data(api_url)
    if not data or data.get('code') != 0:
        print("无法获取收藏夹数据")
        return False, "无法获取收藏夹数据"

    ytb_path = config.get('ytb_path')
    base_download_path = custom_path if custom_path else config.get('download_path')
    bilibili_cookies_path = config.get('bilibili_cookies_path')

    if is_created_fav:
        # 处理创建的收藏夹
        info = data.get('data', {}).get('info', {})
        collection_title = info.get('title', 'unknown_collection')
        medias = data.get('data', {}).get('medias', [])
        # 对于创建的收藏夹，需要从medias中提取bvid
        media_items = [{'bvid': media.get('bvid'), 'title': media.get('title')} for media in medias if media.get('bvid')]
    else:
        # 处理普通收藏夹
        info = data.get('data', {}).get('info', {})
        collection_title = info.get('title', 'unknown_collection')
        medias = data.get('data', {}).get('medias', [])
        media_items = medias

    # 清理文件名
    collection_title = sanitize_filename(collection_title)

    # 创建目标目录
    full_path = os.path.join(base_download_path, collection_title)
    os.makedirs(full_path, exist_ok=True)

    # 获取已下载的视频
    downloaded_videos = get_downloaded_videos(full_path)

    print(f"开始下载合集: {collection_title}，共 {len(media_items)} 个视频")

    success_count = 0
    for i, media in enumerate(media_items, 1):
        bvid = media.get('bvid')
        title = media.get('title')

        # 生成视频URL
        video_url = f"https://www.bilibili.com/video/{bvid}"

        # 检查是否已经下载过该视频
        video_exists = False
        for video_file in downloaded_videos:
            if bvid in video_file:
                is_valid, reason = is_video_file_valid(video_file)
                if is_valid:
                    print(f"视频 {title} ({bvid}) 已存在且有效，跳过下载")
                    video_exists = True
                    success_count += 1
                else:
                    print(f"视频 {title} ({bvid}) 存在但无效 ({reason})，重新下载")
                break

        if video_exists:
            continue

        # 构造命令参数
        command_args = [
            video_url,
            "--embed-thumbnail",
            "--embed-metadata",
            "--merge-output-format", "mp4",
            "-P", full_path,
            "--cookies", bilibili_cookies_path
        ]

        print(f"\n正在下载 ({i}/{len(media_items)}): {title} ({bvid})")
        success, output = execute_ytb_command(ytb_path, *command_args)
        if success:
            success_count += 1
            print(f"下载成功: {title} ({bvid})")
        else:
            print(f"下载失败: {title} ({bvid})")
            # 继续下载下一个视频而不是停止

    print(f"\n合集 {collection_title} 下载完成! 成功: {success_count}/{len(media_items)}")
    return True, f"合集下载完成，成功: {success_count}/{len(media_items)}"


def download_bilibili_season_list(config, url, custom_path=None):
    """
    下载B站合集视频
    :param config: 配置信息
    :param url: 合集URL
    :param custom_path: 自定义路径
    """
    # 提取mid和season_id
    mid, season_id = extract_season_info_from_url(url)
    if not mid or not season_id:
        print("无法从URL中提取mid或season_id参数，请检查URL格式")
        return False, "无法从URL中提取mid或season_id参数"

    # 生成API URL
    api_url = generate_season_api_url(mid, season_id)

    # 获取数据
    data = fetch_fav_list_data(api_url)
    if not data or data.get('code') != 0:
        print("无法获取合集数据")
        return False, "无法获取合集数据"

    ytb_path = config.get('ytb_path')
    base_download_path = config.get('download_path')
    bilibili_cookies_path = config.get('bilibili_cookies_path')
    meta = data.get('data', {}).get('meta', {})
    collection_title = meta.get('name', 'unknown_collection')

    # 清理文件名
    collection_title = sanitize_filename(collection_title)

    # 创建目标目录
    full_path = os.path.join(base_download_path, collection_title)
    os.makedirs(full_path, exist_ok=True)

    # 获取已下载的视频
    downloaded_videos = get_downloaded_videos(full_path)

    archives = data.get('data', {}).get('archives', [])
    print(f"开始下载合集: {collection_title}，共 {len(archives)} 个视频")

    success_count = 0
    for i, archive in enumerate(archives, 1):
        bvid = archive.get('bvid')
        title = archive.get('title')

        # 生成视频URL
        video_url = f"https://www.bilibili.com/video/{bvid}"

        # 检查是否已经下载过该视频
        video_exists = False
        for video_file in downloaded_videos:
            if bvid in video_file:
                is_valid, reason = is_video_file_valid(video_file)
                if is_valid:
                    print(f"视频 {title} ({bvid}) 已存在且有效，跳过下载")
                    video_exists = True
                    success_count += 1
                else:
                    print(f"视频 {title} ({bvid}) 存在但无效 ({reason})，重新下载")
                break

        if video_exists:
            continue

        # 构造命令参数
        command_args = [
            video_url,
            "--embed-thumbnail",
            "--embed-metadata",
            "--merge-output-format", "mp4",
            "-P", full_path,
            "--cookies", bilibili_cookies_path
        ]

        print(f"\n正在下载 ({i}/{len(archives)}): {title} ({bvid})")
        success, output = execute_ytb_command(ytb_path, *command_args)
        if success:
            success_count += 1
            print(f"下载成功: {title} ({bvid})")
        else:
            print(f"下载失败: {title} ({bvid})")
            # 继续下载下一个视频而不是停止

    print(f"\n合集 {collection_title} 下载完成! 成功: {success_count}/{len(archives)}")
    return True, f"合集下载完成，成功: {success_count}/{len(archives)}"


def download_bilibili_single_video(config, url, custom_path=None):
    """
    下载单个B站视频（包括普通视频、课程视频和番剧视频）
    :param config: 配置信息
    :param url: 视频URL
    :param custom_path: 自定义路径
    """
    ytb_path = config.get('ytb_path')
    base_download_path = custom_path if custom_path else config.get('download_path')
    bilibili_cookies_path = config.get('bilibili_cookies_path')

    # 获取视频ID（对于不同类型的URL采用不同方式）
    video_id = None
    if "bilibili.com/video/BV" in url:
        # 普通视频
        video_id = url.split("/")[-1].split("?")[0]
    elif "bilibili.com/cheese/play/ss" in url:
        # 课程视频 (仅ss格式)
        video_id = url.split("/")[-1].split("?")[0]
    elif "bilibili.com/bangumi/play/" in url:
        # 番剧视频 (包括ep和ss格式)
        video_id = url.split("/")[-1].split("?")[0]

    # 创建视频特定目录
    if "bilibili.com/cheese/play/ss" in url:
        # 对于cheese课程，获取标题并创建目录
        ss_id = video_id.replace('ss', '')
        cheese_title = get_bilibili_cheese_title(ss_id, bilibili_cookies_path)
        video_dir_name = f"{cheese_title}_{video_id}"
    else:
        # 其他视频使用ID作为目录名
        video_dir_name = f"{video_id}"
    
    download_path = os.path.join(base_download_path, video_dir_name)
    os.makedirs(download_path, exist_ok=True)

    # 检查是否已经下载过该视频
    if video_id:
        downloaded_videos = get_downloaded_videos(download_path)
        for video_file in downloaded_videos:
            if video_id in video_file:
                is_valid, reason = is_video_file_valid(video_file)
                if is_valid:
                    print(f"视频 {video_id} 已存在且有效，跳过下载")
                    return True, "视频已存在且有效，跳过下载"
                else:
                    print(f"视频 {video_id} 存在但无效 ({reason})，重新下载")
                break

    # 构造命令参数
    command_args = [
        url,
        "--embed-thumbnail",
        "--embed-metadata",
        "--merge-output-format", "mp4",
        "-P", download_path,
        "--cookies", bilibili_cookies_path
    ]

    if "cheese" in url:
        video_type = "B站课程视频"
    elif "bangumi" in url:
        video_type = "B站番剧视频"
    else:
        video_type = "B站视频"

    print(f"正在下载{video_type}: {url}")
    success, output = execute_ytb_command(ytb_path, *command_args)
    if success:
        print(f"{video_type}下载完成!")
    else:
        print(f"{video_type}下载失败!")
    return success, output


def download_youtube_content(config, url, custom_path=None):
    """
    下载YouTube内容（单个视频或播放列表）
    :param config: 配置信息
    :param url: YouTube URL
    :param custom_path: 自定义路径
    """
    ytb_path = config.get('ytb_path')
    base_download_path = custom_path if custom_path else config.get('download_path')
    youtube_cookies_path = config.get('youtube_cookies_path')

    # 创建特定目录
    url_identifier = None
    if "watch?v=" in url:
        url_identifier = url.split("watch?v=")[1].split("&")[0]
    elif "playlist?list=" in url:
        url_identifier = url.split("playlist?list=")[1].split("&")[0]

    # 创建内容特定目录 (使用ID，稍后yt-dlp会自动添加标题)
    content_dir_name = f"{url_identifier}" if url_identifier else "unknown_content"
    download_path = os.path.join(base_download_path, content_dir_name) if url_identifier else base_download_path
    os.makedirs(download_path, exist_ok=True)

    # 检查是否已经下载过该内容
    # 对于YouTube，我们简单地检查URL是否在已下载的文件名中
    downloaded_videos = get_downloaded_videos(download_path)
    if url_identifier:
        for video_file in downloaded_videos:
            if url_identifier in video_file:
                is_valid, reason = is_video_file_valid(video_file)
                if is_valid:
                    content_type = "YouTube播放列表" if "playlist" in url else "YouTube视频"
                    print(f"{content_type}相关内容已存在且有效，跳过下载")
                    return True, "内容已存在且有效，跳过下载"
                else:
                    print(f"YouTube内容存在但无效 ({reason})，重新下载")
                break

    # 构造命令参数
    command_args = [
        "--write-auto-subs",
        "--sub-lang", "en",
        "--proxy", "127.0.0.1:23333",
        "--embed-thumbnail",
        "--embed-metadata",
        "--merge-output-format", "mp4",
        url,
        "-P", download_path,
        "--cookies", youtube_cookies_path
    ]

    content_type = "YouTube播放列表" if "playlist" in url else "YouTube视频"
    print(f"正在下载{content_type}: {url}")
    success, output = execute_ytb_command(ytb_path, *command_args)
    if success:
        print(f"{content_type}下载完成!")
    else:
        print(f"{content_type}下载失败!")
    return success, output


def process_url(config, url, custom_path=None):
    """
    根据URL类型处理下载
    :param config: 配置信息
    :param url: URL
    :param custom_path: 自定义路径
    :return: (success, output)
    """
    if "favlist" in url and "bilibili.com" in url:
        # B站收藏夹
        return download_bilibili_fav_list(config, url, custom_path)
    elif "bilibili.com/lists/" in url and "type=season" in url:
        # B站合集
        return download_bilibili_season_list(config, url, custom_path)
    elif ("video/BV" in url and "bilibili.com" in url) or \
            ("bilibili.com/cheese/play/ss" in url) or \
            ("bilibili.com/bangumi/play/" in url):
        # 单个B站视频、课程视频或番剧视频
        return download_bilibili_single_video(config, url, custom_path)
    elif ("youtube.com/playlist" in url) or ("youtube.com/watch" in url and "v=" in url):
        # YouTube播放列表或单个视频
        return download_youtube_content(config, url, custom_path)
    else:
        error_msg = "不支持的URL类型"
        print(error_msg)
        return False, error_msg


def read_urls_from_file(file_path):
    """
    从文件中读取URL和路径
    :param file_path: 文件路径
    :return: URL和路径的列表
    """
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('✅'):
                    # 跳过已经完成的URL（以✅开头的行）
                    parts = line.split(' ', 1)
                    url = parts[0]
                    path = parts[1] if len(parts) > 1 else None
                    urls.append((url, path, line))  # 保存原始行内容
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
    return urls


def update_url_in_file(original_file_path, result_file_path, original_line, success, error_msg=None):
    """
    更新结果文件和原始文件中的URL状态
    :param original_file_path: 原始文件路径
    :param result_file_path: 结果文件路径
    :param original_line: 原始行
    :param success: 是否成功
    :param error_msg: 错误信息
    """
    try:
        # 如果结果文件不存在，先复制原始文件
        if not os.path.exists(result_file_path):
            with open(original_file_path, 'r', encoding='utf-8') as original, \
                    open(result_file_path, 'w', encoding='utf-8') as result:
                result.write(original.read())

        # 更新结果文件
        with open(result_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        with open(result_file_path, 'w', encoding='utf-8') as f:
            for line in lines:
                line_stripped = line.strip()
                if line_stripped == original_line:
                    if success:
                        f.write(f"✅ {line}")
                    else:
                        f.write(line)
                        # 错误信息在下一行，每行前加tab
                        if error_msg:
                            error_lines = error_msg.split('\n')
                            for error_line in error_lines:
                                if error_line.strip():  # 只写入非空行
                                    f.write(f"\t{error_line}\n")
                else:
                    f.write(line)
                    
        # 更新原始文件
        if success:
            with open(original_file_path, 'r', encoding='utf-8') as f:
                original_lines = f.readlines()
            
            with open(original_file_path, 'w', encoding='utf-8') as f:
                for line in original_lines:
                    line_stripped = line.strip()
                    if line_stripped == original_line:
                        f.write(f"✅ {line}")
                    else:
                        f.write(line)
    except Exception as e:
        print(f"更新文件时发生错误: {e}")


def process_urls_by_priority(config, urls_with_paths, original_file_path):
    """
    根据队列长度优先下载较多任务的平台
    :param config: 配置信息
    :param urls_with_paths: URL和路径的列表
    :param original_file_path: 原始文件路径
    """
    # 分离B站和YouTube的URL
    bilibili_urls = [(url, path, original) for url, path, original in urls_with_paths if "bilibili.com" in url]
    youtube_urls = [(url, path, original) for url, path, original in urls_with_paths if "youtube.com" in url]

    # 生成结果文件路径
    result_file_path = f"{original_file_path}.result"

    # 根据数量决定优先下载哪个平台
    if len(bilibili_urls) >= len(youtube_urls):
        # 先下载B站，再下载YouTube
        print(f"检测到B站任务 ({len(bilibili_urls)} 个) 多于或等于 YouTube任务 ({len(youtube_urls)} 个)，优先下载B站内容")
        process_bilibili_urls(config, bilibili_urls, original_file_path, result_file_path)
        process_youtube_urls(config, youtube_urls, original_file_path, result_file_path)
    else:
        # 先下载YouTube，再下载B站
        print(f"检测到YouTube任务 ({len(youtube_urls)} 个) 多于 B站任务 ({len(bilibili_urls)} 个)，优先下载YouTube内容")
        process_youtube_urls(config, youtube_urls, original_file_path, result_file_path)
        process_bilibili_urls(config, bilibili_urls, original_file_path, result_file_path)


def process_bilibili_urls(config, urls, original_file_path, result_file_path):
    """
    处理B站URL
    :param config: 配置信息
    :param urls: B站URL列表
    :param original_file_path: 原始文件路径
    :param result_file_path: 结果文件路径
    """
    for url, custom_path, original_line in urls:
        success, output = process_url(config, url, custom_path)
        update_url_in_file(original_file_path, result_file_path, original_line, success, output if not success else None)


def process_youtube_urls(config, urls, original_file_path, result_file_path):
    """
    处理YouTube URL
    :param config: 配置信息
    :param urls: YouTube URL列表
    :param original_file_path: 原始文件路径
    :param result_file_path: 结果文件路径
    """
    for url, custom_path, original_line in urls:
        success, output = process_url(config, url, custom_path)
        update_url_in_file(original_file_path, result_file_path, original_line, success, output if not success else None)


def process_bilibili_fav_list(config):
    """
    主函数：处理URL列表
    """
    while True:
        # 提示用户输入URL或文件路径
        user_input = input("\n请输入URL或包含URL的文件路径 (输入'exit'退出): ").strip()

        if user_input.lower() == 'exit':
            print("程序退出")
            break

        if not user_input:
            continue

        # 检查输入是否为文件路径
        if os.path.isfile(user_input):
            # 从文件读取URL
            urls_with_paths = read_urls_from_file(user_input)
            if urls_with_paths:
                process_urls_by_priority(config, urls_with_paths, user_input)
            else:
                print("文件中没有有效的URL")
        else:
            # 直接处理单个URL
            success, output = process_url(config, user_input)
            if success:
                print("下载完成!")
            else:
                print(f"下载失败: {output}")


def main():
    config = load_config()
    # 直接进入下载流程
    process_bilibili_fav_list(config)


if __name__ == '__main__':
    main()
