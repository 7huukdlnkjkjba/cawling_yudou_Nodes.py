import requests
import re
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import sys


def fetch_html(url):
    """获取网页HTML内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        # 尝试多种编码，最后用UTF-8兜底
        resp.encoding = resp.apparent_encoding if resp.apparent_encoding else 'utf-8'
        return resp.text
    except requests.RequestException as e:
        print(f"错误：无法获取 {url}。原因：{e}")
        return None


def get_today_str():
    """返回今天的日期字符串，格式为 YYYYMMDD"""
    return datetime.now().strftime("%Y%m%d")


def get_yesterday_str():
    """返回昨天的日期字符串，格式为 YYYYMMDD"""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y%m%d")


def extract_first_video_description(youtube_html):
    """从YouTube频道页面HTML中提取第一个视频的描述"""
    if not youtube_html:
        return None

    # 方法1：尝试从JSON数据中提取（更可靠）
    script_pattern = r'var ytInitialData = (.*?);'
    match = re.search(script_pattern, youtube_html, re.DOTALL)

    if match:
        try:
            yt_data = json.loads(match.group(1))

            # 尝试不同的路径查找视频描述
            possible_paths = [
                # 常见的视频网格布局路径
                ['contents', 'twoColumnBrowseResultsRenderer', 'tabs', 1, 'tabRenderer', 'content', 'richGridRenderer',
                 'contents', 0, 'richItemRenderer', 'content', 'videoRenderer'],
                # 备用路径1
                ['contents', 'twoColumnBrowseResultsRenderer', 'tabs', 0, 'tabRenderer', 'content',
                 'sectionListRenderer', 'contents', 0, 'itemSectionRenderer', 'contents', 0, 'gridRenderer', 'items', 0,
                 'gridVideoRenderer'],
                # 备用路径2
                ['contents', 'twoColumnBrowseResultsRenderer', 'tabs', 0, 'tabRenderer', 'content', 'richGridRenderer',
                 'contents', 0, 'richItemRenderer', 'content', 'videoRenderer']
            ]

            for path in possible_paths:
                try:
                    current = yt_data
                    for key in path:
                        current = current[key]

                    # 提取描述
                    if 'descriptionSnippet' in current and 'runs' in current['descriptionSnippet']:
                        description = ''.join([run['text'] for run in current['descriptionSnippet']['runs']])
                        return description
                    elif 'description' in current:
                        description = current['description']
                        return description
                except (KeyError, IndexError):
                    continue

        except json.JSONDecodeError as e:
            print(f"错误：无法解析JSON数据。原因：{e}")

    # 方法2：如果JSON解析失败，尝试直接在HTML中搜索描述
    print("提示：尝试使用备用方法提取视频描述...")

    # 搜索包含yudou.us链接的文本
    today = get_today_str()
    yesterday = get_yesterday_str()
    
    # 尝试匹配今天或昨天的链接
    patterns = [
        rf'https://www\.yudou\.us/({today}|{yesterday})/[a-z]{{3}}({today}|{yesterday})\.html',
        rf'https://www\.yudou\.us/({today}|{yesterday})/[a-zA-Z]{{3,5}}({today}|{yesterday})\.html',
        rf'https://www\.yudou\.us/({today}|{yesterday})/[^/\s]+\.html'
    ]

    for pattern in patterns:
        matches = re.findall(pattern, youtube_html)
        if matches:
            # 返回找到的第一个链接
            for match in matches:
                if isinstance(match, tuple):
                    # 如果是元组，取第一个元素
                    return f"https://www.yudou.us/{match[0]}/{match[1]}.html" if len(match) >= 2 else match[0]
                else:
                    return match

    print("错误：无法提取视频描述。")
    return None


def extract_target_link(description):
    """从视频描述中提取目标链接，优先今日，如果没有则使用昨日"""
    if not description:
        return None

    today = get_today_str()
    yesterday = get_yesterday_str()
    
    # 首先尝试查找今日链接
    print(f"  优先搜索今日目标链接: https://www.yudou.us/{today}/xxx{today}.html")
    pattern_today = rf'https://www\.yudou\.us/{today}/[a-z]{{3}}{today}\.html'
    match_today = re.search(pattern_today, description)
    
    if match_today:
        print(f"  成功找到今日链接: {match_today.group(0)}")
        return match_today.group(0)
    
    # 如果没找到今日链接，尝试更宽松的匹配
    print("  提示：未找到今日链接，尝试宽松匹配...")
    pattern_today_loose = rf'https://www\.yudou\.us/{today}/[^/\s]+\.html'
    match_today_loose = re.search(pattern_today_loose, description)
    
    if match_today_loose:
        print(f"  通过宽松匹配找到今日链接: {match_today_loose.group(0)}")
        return match_today_loose.group(0)
    
    # 如果还是没有找到，尝试查找昨日链接
    print(f"  提示：未找到今日链接，开始搜索昨日链接: https://www.yudou.us/{yesterday}/xxx{yesterday}.html")
    pattern_yesterday = rf'https://www\.yudou\.us/{yesterday}/[a-z]{{3}}{yesterday}\.html'
    match_yesterday = re.search(pattern_yesterday, description)
    
    if match_yesterday:
        print(f"  成功找到昨日链接: {match_yesterday.group(0)}")
        print(f"  注意：今日链接尚未发布，已使用昨日链接 ({yesterday})")
        return match_yesterday.group(0)
    
    # 如果没找到昨日链接，尝试更宽松的匹配
    print("  提示：未找到昨日链接，尝试宽松匹配...")
    pattern_yesterday_loose = rf'https://www\.yudou\.us/{yesterday}/[^/\s]+\.html'
    match_yesterday_loose = re.search(pattern_yesterday_loose, description)
    
    if match_yesterday_loose:
        print(f"  通过宽松匹配找到昨日链接: {match_yesterday_loose.group(0)}")
        print(f"  注意：今日链接尚未发布，已使用昨日链接 ({yesterday})")
        return match_yesterday_loose.group(0)

    return None


def extract_txt_link(html):
    """从目标页面HTML中提取唯一的.txt文件链接"""
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')

    # 查找所有包含 '.txt' 的链接
    all_links = soup.find_all('a', href=True)
    txt_links = [a['href'] for a in all_links if '.txt' in a['href']]

    # 如果没有在<a>标签中找到，尝试在页面所有文本中搜索
    if not txt_links:
        pattern = r'https?://[^\s"\']+\.txt'
        txt_links = re.findall(pattern, html)

    # 返回找到的第一个.txt链接
    return txt_links[0] if txt_links else None


def save_to_file(content, filename):
    """将内容保存到文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  成功！文件已保存为: {filename}")
        return True
    except Exception as e:
        print(f"  错误：无法保存文件 {filename}。原因：{e}")
        return False


def main():
    youtube_channel_url = "https://www.youtube.com/@yudou/videos"
    today = get_today_str()
    yesterday = get_yesterday_str()

    print(f"今日日期: {today}")
    print(f"昨日日期: {yesterday}")
    print(f"目标链接模式: https://www.yudou.us/{today}/xxx{today}.html")
    print(f"备用链接模式: https://www.yudou.us/{yesterday}/xxx{yesterday}.html")

    # 首先尝试自动获取
    print("\n步骤1：获取YouTube频道页面并提取第一个视频描述...")
    youtube_html = fetch_html(youtube_channel_url)

    if not youtube_html:
        # 如果自动获取失败，让用户手动输入
        print("\n提示：由于网络限制无法访问YouTube。")
        user_input = input(f"请手动输入目标链接（格式：https://www.yudou.us/YYYYMMDD/xxxYYYYMMDD.html）: ")
        if user_input:
            print(f"已使用手动输入的链接: {user_input}")
            # 直接使用用户输入的链接作为目标URL
            target_url = user_input
            # 跳过步骤2，直接进入步骤3
            print("\n步骤3：访问目标页面...")
            target_html = fetch_html(target_url)

            if not target_html:
                print("错误：无法获取目标页面。")
                sys.exit(1)

            print("步骤4：在目标页面中查找.txt文件链接...")
            txt_link = extract_txt_link(target_html)

            if not txt_link:
                print("错误：未在目标页面中找到.txt文件链接。")
                sys.exit(1)

            # 处理相对路径
            if txt_link.startswith('//'):
                txt_link = 'https:' + txt_link
            elif txt_link.startswith('/'):
                from urllib.parse import urlparse
                parsed_url = urlparse(target_url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                txt_link = base_url + txt_link
            elif not txt_link.startswith('http'):
                from urllib.parse import urljoin
                txt_link = urljoin(target_url, txt_link)

            print(f"  找到.txt链接: {txt_link}")

            print("\n步骤5：下载.txt文件内容并保存...")
            txt_content = fetch_html(txt_link)

            if txt_content:
                filename = f"nodes_{today}.txt"
                if save_to_file(txt_content, filename):
                    print("\n文件内容预览（前10行）：")
                    lines = txt_content.strip().split('\n')
                    for i, line in enumerate(lines[:10]):
                        print(f"  {i + 1}: {line}")
                    if len(lines) > 10:
                        print(f"  ... 以及另外 {len(lines) - 10} 行")
            else:
                print("错误：无法下载.txt文件内容。")
            return
        else:
            print("未输入任何链接，程序终止。")
            sys.exit(1)

    description = extract_first_video_description(youtube_html)
    if not description:
        print("错误：无法提取视频描述。")
        sys.exit(1)

    print("\n步骤2：在视频描述中查找目标链接（优先今日，若无则用昨日）...")

    target_url = extract_target_link(description)
    if not target_url:
        print(f"错误：未在视频描述中找到匹配的目标链接。")
        print(f"视频描述片段: {description[:200]}...")
        sys.exit(1)

    print(f"\n步骤3：访问目标页面: {target_url}")
    target_html = fetch_html(target_url)

    if not target_html:
        sys.exit(1)

    print("步骤4：在目标页面中查找.txt文件链接...")
    txt_link = extract_txt_link(target_html)

    if not txt_link:
        print("错误：未在目标页面中找到.txt文件链接。")
        sys.exit(1)

    # 处理相对路径
    if txt_link.startswith('//'):
        txt_link = 'https:' + txt_link
    elif txt_link.startswith('/'):
        from urllib.parse import urlparse
        parsed_url = urlparse(target_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        txt_link = base_url + txt_link
    elif not txt_link.startswith('http'):
        from urllib.parse import urljoin
        txt_link = urljoin(target_url, txt_link)

    print(f"  找到.txt链接: {txt_link}")

    print("\n步骤5：下载.txt文件内容并保存...")
    txt_content = fetch_html(txt_link)

    if txt_content:
        filename = f"nodes_{today}.txt"
        if save_to_file(txt_content, filename):
            print("\n文件内容预览（前10行）：")
            lines = txt_content.strip().split('\n')
            for i, line in enumerate(lines[:10]):
                print(f"  {i + 1}: {line}")
            if len(lines) > 10:
                print(f"  ... 以及另外 {len(lines) - 10} 行")
    else:
        print("错误：无法下载.txt文件内容。")


if __name__ == "__main__":
    main()