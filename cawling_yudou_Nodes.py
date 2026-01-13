import requests, re, json, sys, time, subprocess, os, random
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# 获取脚本所在目录的绝对路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def fetch_html(url):
    """获取网页HTML内容，增加重试机制和反爬延迟"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }
    
    max_retries = 3
    for retry in range(max_retries):
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            # 尝试多种编码，最后用UTF-8兜底
            resp.encoding = resp.apparent_encoding if resp.apparent_encoding else 'utf-8'
            # 添加反爬延迟，模拟人类浏览行为
            time.sleep(random.uniform(1, 3))
            return resp.text
        except requests.RequestException as e:
            if retry < max_retries - 1:
                print(f"警告：获取 {url} 失败，{retry+1}/{max_retries}，3秒后重试... 原因：{e}")
                time.sleep(3)
            else:
                print(f"错误：无法获取 {url}。原因：{e}")
                return None

def get_today_str():
    """返回今天的日期字符串，格式为 YYYYMMDD"""
    return datetime.now().strftime("%Y%m%d")

def get_yesterday_str():
    """返回昨天的日期字符串，格式为 YYYYMMDD"""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y%m%d")

def get_current_date_str():
    """返回今天的日期字符串，格式为 2026年01月02日"""
    return datetime.now().strftime("%Y年%m月%d日")

def get_yesterday_date_str():
    """返回昨天的日期字符串，格式为 2026年01月01日"""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y年%m月%d日")



def get_latest_article_link(html):
    """从首页HTML中提取最新文章的链接"""
    if not html:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 先尝试查找带有日期的文章链接
    current_date = get_current_date_str()
    yesterday_date = get_yesterday_date_str()
    
    # 查找所有文章链接
    all_links = soup.find_all('a', href=True)
    
    # 优先查找今日文章
    for link in all_links:
        link_text = link.get_text().strip()
        if current_date in link_text and "免费精选节点" in link_text:
            href = link['href']
            if not href.startswith('http'):
                href = "https://www.yudou789.top" + href
            return href, link_text
    
    # 如果没有今日文章，查找昨日文章
    for link in all_links:
        link_text = link.get_text().strip()
        if yesterday_date in link_text and "免费精选节点" in link_text:
            href = link['href']
            if not href.startswith('http'):
                href = "https://www.yudou789.top" + href
            return href, link_text
    
    # 如果没找到特定日期的文章，尝试获取第一个文章链接
    for link in all_links:
        link_text = link.get_text().strip()
        if "免费精选节点" in link_text:
            href = link['href']
            if not href.startswith('http'):
                href = "https://www.yudou789.top" + href
            return href, link_text
    
    return None, None

def find_encrypted_txt_link(article_html):
    """从文章页面（第一层DOM）中查找加密txt链接"""
    if not article_html:
        return None
    
    soup = BeautifulSoup(article_html, 'html.parser')
    
    # 方法1：优先查找.txt文件链接
    all_links = soup.find_all('a', href=True)
    txt_links = []
    
    for link in all_links:
        href = link['href']
        text = link.get_text().strip().lower()
        
        # 跳过分类链接、首页链接和HTML页面链接
        if 'category' in href or href == '/' or href == '#' or href.endswith('.html'):
            continue
        
        # 只接受.txt文件链接
        if '.txt' in href:
            if not href.startswith('http'):
                href = "https://www.yudou789.top" + href
            txt_links.append(href)
    
    # 方法2：在页面所有文本中搜索.txt链接
    if not txt_links:
        pattern = r'https?://[^\s"\']+\.txt'
        txt_links = re.findall(pattern, article_html)
    
    # 方法3：在HTML中搜索可能的.txt下载链接
    if not txt_links:
        pattern = r'<a[^>]+href=["\']([^"\']*\.txt[^"\']*)["\'][^>]*>'
        matches = re.findall(pattern, article_html, re.IGNORECASE)
        for match in matches:
            href = match
            if not href.startswith('http'):
                href = "https://www.yudou789.top" + href
            txt_links.append(href)
    
    # 去重并返回第一个链接
    if txt_links:
        # 去重
        unique_links = list(dict.fromkeys(txt_links))
        return unique_links[0]
    
    return None

def extract_encrypted_content(txt_html):
    """从加密页面中提取加密内容"""
    if not txt_html:
        return None
    
    # 尝试直接获取文本内容（如果是纯文本文件）
    if '<' not in txt_html[:100]:  # 可能是纯文本
        return txt_html.strip()
    
    # 否则是HTML页面，需要提取加密内容
    soup = BeautifulSoup(txt_html, 'html.parser')
    
    # 玉豆分享特殊处理：查找带有data-secret属性的元素
    wrapper = soup.find('.cl-noindent-wrapper')
    if not wrapper:
        wrapper = soup.select_one('[data-secret]')
    
    if wrapper:
        secret_data = wrapper.get('data-secret')
        if secret_data:
            # 返回特殊格式，包含secret_data和HTML内容，用于后续破解
            return f"YUDOU_ENCRYPT:{secret_data}:{txt_html}"
    
    # 方法1：查找<textarea>标签
    textarea = soup.find('textarea')
    if textarea:
        content = textarea.get_text().strip()
        if content:
            return content
    
    # 方法2：查找<pre>标签
    pre = soup.find('pre')
    if pre:
        content = pre.get_text().strip()
        if content:
            return content
    
    # 方法3：查找<div>或<span>中可能包含的加密文本
    for tag in soup.find_all(['div', 'span', 'p']):
        content = tag.get_text().strip()
        # 检查是否是Base64编码的文本特征
        if (len(content) > 100 and 
            re.match(r'^[A-Za-z0-9+/=]+$', content.replace('\n', '').replace('\r', ''))):
            return content
    
    # 方法4：查找所有文本并尝试识别加密内容
    all_text = soup.get_text()
    lines = all_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if len(line) > 50 and not any(word in line.lower() for word in ['html', 'http', '<', '>', 'script']):
            return line
    
    # 方法5：在原始HTML中搜索Base64模式
    pattern = r'[A-Za-z0-9+/=]{100,}'
    matches = re.findall(pattern, txt_html)
    
    if matches:
        # 返回最长的匹配项（最可能是加密内容）
        return max(matches, key=len)
    
    return None



def extract_password_from_article(article_html):
    """从文章页面中提取密码，优先从JS解码器中获取"""
    if not article_html:
        return None
    
    import base64
    
    soup = BeautifulSoup(article_html, 'html.parser')
    
    # 方法1：优先查找带有data-secret属性的元素（Base64编码密码）
    secret_elements = soup.select('[data-secret]')
    for elem in secret_elements:
        secret_data = elem.get('data-secret')
        if secret_data:
            try:
                # 解码Base64
                decoded = base64.b64decode(secret_data).decode('utf-8')
                # 检查是否是4位数字密码
                if re.match(r'^\d{4}$', decoded):
                    return decoded
            except Exception as e:
                print(f"解码Base64密码失败: {e}")
    
    # 方法2：查找JS解码器中的密码映射
    today = get_today_str()  # 格式：YYYYMMDD
    
    # 查找所有script标签
    scripts = soup.find_all('script')
    for script in scripts:
        script_content = script.string
        if script_content:
            # 尝试匹配密码映射模式，例如：{"20260105":"2266"} 或类似格式
            # 匹配各种可能的密码映射格式
            patterns = [
                # 匹配对象字面量：{"20260105":"2266", ...}
                r'\{\s*["\'](\d{8})["\']\s*:\s*["\'](\d{4})["\']\s*(?:,|\})',
                # 匹配数组格式：["20260105","2266"] 或 [["20260105","2266"]]
                r'["\'](\d{8})["\']\s*,\s*["\'](\d{4})["\']',
                # 匹配函数调用中的密码：getPassword("20260105") 或类似
                rf'passwords?\s*[=:]?\s*\{{[^}}]*["\']{today}["\']\s*:\s*["\'](\d{{4}})["\']',
                # 匹配直接赋值：var password = "2266" 或 const pwd = "2266"
                r'[var|let|const]\s+\w*password\w*\s*=\s*["\'](\d{4})["\']'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, script_content, re.IGNORECASE)
                if matches:
                    for match in matches:
                        # 处理不同匹配结果格式
                        if isinstance(match, tuple):
                            # 如果是元组，检查第一个元素是否是今天的日期
                            if len(match) == 2 and match[0] == today:
                                return match[1]
                            # 否则尝试返回第二个元素（密码）
                            elif len(match) == 2:
                                return match[1]
                            # 如果只有一个元素，直接返回
                            elif len(match) == 1:
                                return match[0]
                        else:
                            # 字符串匹配，直接返回
                            return match
    
    # 方法3：查找包含"密码"的文本（原逻辑）
    all_text = soup.get_text()
    
    # 正则表达式匹配密码：通常是4位数字
    password_patterns = [
        r'密码[:：]\s*(\d{4})',
        r'今日密码[:：]\s*(\d{4})',
        r'提取码[:：]\s*(\d{4})',
        r'key[:：]\s*(\d{4})',
        r'KEY[:：]\s*(\d{4})',
        r'密码\s*=\s*(\d{4})',
        r'提取码\s*=\s*(\d{4})'
    ]
    
    for pattern in password_patterns:
        matches = re.findall(pattern, all_text)
        if matches:
            return matches[0]
    
    # 方法4：查找包含密码的HTML元素（原逻辑）
    for tag in soup.find_all(['div', 'span', 'p', 'strong']):
        text = tag.get_text().strip()
        if '密码' in text or '提取码' in text or 'KEY' in text or 'key' in text:
            matches = re.findall(r'\d{4}', text)
            if matches:
                return matches[0]
    
    # 方法5：如果以上都失败，返回空
    return None


def validate_filename(filename):
    """验证文件名安全性，防止路径遍历攻击"""
    # 只允许文件名包含字母、数字、下划线和连字符
    if not re.match(r'^[a-zA-Z0-9-_]+\.\w+$', filename):
        return False
    # 确保文件名不包含路径分隔符
    if '/' in filename or '\\' in filename or '..' in filename:
        return False
    return True

def save_to_file(content, filename):
    """将内容保存到文件"""
    try:
        # 验证文件名安全性
        if not validate_filename(filename):
            print(f"  错误：文件名 {filename} 不安全")
            return False
        # 拼接脚本目录和文件名，确保文件保存在脚本所在目录
        file_path = os.path.join(SCRIPT_DIR, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  成功！文件已保存为: {file_path}")
        return True
    except Exception as e:
        file_path = os.path.join(SCRIPT_DIR, filename)
        print(f"  错误：无法保存文件 {file_path}。原因：{e}")
        return False


def extract_date_from_title(title):
    """从文章标题中提取日期，格式：YYYYMMDD"""
    # 匹配标题中的日期格式：2026年01月06日
    pattern = r'(\d{4})年(\d{2})月(\d{2})日'
    match = re.search(pattern, title)
    if match:
        year = match.group(1)
        month = match.group(2)
        day = match.group(3)
        return f"{year}{month}{day}"
    # 如果没找到，返回当前日期
    return get_today_str()


def main():
    base_url = "https://www.yudou789.top/"
    
    print(f"开始爬取玉豆分享最新节点文件...")
    
    # 步骤1：获取网站首页
    home_html = fetch_html(base_url)
    if not home_html:
        print("错误：无法访问目标网站")
        sys.exit(1)
    
    # 步骤2：查找最新文章链接
    article_url, article_title = get_latest_article_link(home_html)
    if not article_url:
        print("错误：无法找到最新文章链接")
        sys.exit(1)
    
    print(f"找到最新文章: {article_title}")
    
    # 从文章标题中提取日期
    article_date = extract_date_from_title(article_title)
    print(f"文章日期：{article_date}")
    
    # 步骤3：访问文章页面
    article_html = fetch_html(article_url)
    if not article_html:
        print("错误：无法访问文章页面")
        sys.exit(1)
    
    # 步骤4：从文章页面提取密码
    password = extract_password_from_article(article_html)
    if password:
        print(f"✅ 今日密码：{password}")
    else:
        print("🔍 未在文章中找到密码，尝试其他方式...")
    
    # 步骤5：查找加密文件链接
    txt_url = find_encrypted_txt_link(article_html)
    
    if not txt_url:
        print("错误：无法找到加密文件链接")
        sys.exit(1)
    
    print(f"找到节点文件链接: {txt_url}")
    
    # 步骤5：直接访问并保存txt文件内容
    txt_content = fetch_html(txt_url)
    if not txt_content:
        print("错误：无法访问节点文件")
        sys.exit(1)
    
    # 使用文章日期命名文件
    filename = f"nodes_{article_date}.txt"
    # 验证文件名安全性
    if validate_filename(filename):
        file_path = os.path.join(SCRIPT_DIR, filename)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            print(f"文件已保存到 {file_path}")
        except Exception as e:
            print(f"错误：无法保存文件 {file_path}。原因：{e}")
    else:
        print(f"错误：文件名 {filename} 不安全")
    
    # 删除JS解码器
    js_file_path = os.path.join(SCRIPT_DIR, "yudou_decode.js")
    if os.path.exists(js_file_path):
        try:
            os.remove(js_file_path)
            print(f"JS解码器已删除：{js_file_path}")
        except Exception as e:
            print(f"错误：无法删除JS解码器。原因：{e}")
    
    # 显示最终结果
    print(f"爬取完成！")
    if password:
        print(f"📅 文章日期：{article_date}")
        print(f"🔑 最终密码：{password}")

if __name__ == "__main__":
    main()