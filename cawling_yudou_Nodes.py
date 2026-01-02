import requests, re, json, sys, time, subprocess, os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import execjs  # 需要安装：pip install PyExecJS

def fetch_html(url):
    """获取网页HTML内容，增加重试机制"""
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
            resp = requests.get(url, headers=headers, timeout=30, verify=False)
            resp.raise_for_status()
            # 尝试多种编码，最后用UTF-8兜底
            resp.encoding = resp.apparent_encoding if resp.apparent_encoding else 'utf-8'
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

def download_js_decoder():
    """下载 JavaScript 解码器"""
    js_url = "https://raw.githubusercontent.com/7huukdlnkjkjba/yudou_decode/main/yudou_decode.js"
    
    print(f"步骤1：下载JS解码器...")
    js_content = requests.get(js_url, timeout=15).text
    
    if not js_content:
        print("错误：无法下载JS解码器")
        return None
    
    # 保存到本地文件
    with open("yudou_decode.js", "w", encoding="utf-8") as f:
        f.write(js_content)
    
    print("  JS解码器已下载到本地")
    return js_content

def load_js_decoder():
    """加载JS解码器"""
    # 设置execjs使用utf-8编码，避免Windows上的gbk问题
    os.environ['EXECJS_ENCODING'] = 'utf-8'
    
    if os.path.exists("yudou_decode.js"):
        with open("yudou_decode.js", "r", encoding="utf-8") as f:
            js_content = f.read()
    else:
        js_content = download_js_decoder()
    
    if not js_content:
        return None
    
    try:
        # 创建JS上下文
        ctx = execjs.compile(js_content)
        return ctx
    except Exception as e:
        print(f"错误：无法加载JS解码器。原因：{e}")
        return None

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

# 玉豆分享常见密码列表 - 优先尝试
COMMON_PASSWORDS = [
    "0000", "0123", "1111", "1112", "1122", "1133", "1144", "1155", "1166", "1177",
    "1188", "1199", "1222", "1234", "2211", "2222", "2233", "2244", "2255", "2266",
    "2277", "2288", "2299", "2333", "2345", "3311", "3322", "3333", "3344", "3355",
    "3366", "3377", "3388", "3399", "3444", "3456", "4321", "4411", "4422", "4433",
    "4444", "4455", "4466", "4477", "4488", "4499", "4555", "4567", "5511", "5522",
    "5533", "5544", "5555", "5566", "5577", "5588", "5599", "5666", "5678", "6611",
    "6622", "6633", "6644", "6655", "6666", "6677", "6688", "6699", "6777", "6789",
    "7711", "7722", "7733", "7744", "7755", "7766", "7777", "7788", "7799", "7888",
    "8811", "8822", "8833", "8844", "8855", "8866", "8877", "8888", "8899", "8999",
    "9900", "9911", "9922", "9933", "9944", "9955", "9966", "9977", "9988", "9999"
]


def crack_yudou_password(secret_data, html_content):
    """玉豆分享密码破解函数"""
    import base64
    
    # 尝试常用密码
    for pwd in COMMON_PASSWORDS:
        try:
            # 将密码转为Base64，与secret_data比较
            encoded_pwd = base64.b64encode(pwd.encode()).decode()
            if encoded_pwd == secret_data:
                return pwd
        except:
            continue
    
    # 暴力破解：尝试0000-9999
    for i in range(10000):
        pwd = str(i).zfill(4)
        try:
            encoded_pwd = base64.b64encode(pwd.encode()).decode()
            if encoded_pwd == secret_data:
                return pwd
        except:
            continue
    
    return None


def decode_with_js(encrypted_content, js_ctx):
    """使用JS解码器解密内容"""
    if not encrypted_content:
        return encrypted_content
    
    # 检查是否为玉豆分享加密格式
    if encrypted_content.startswith("YUDOU_ENCRYPT:"):
        try:
            # 解析格式：YUDOU_ENCRYPT:secret_data:html_content
            parts = encrypted_content.split(":", 2)
            if len(parts) != 3:
                return encrypted_content
            
            secret_data = parts[1]
            html_content = parts[2]
            
            # 破解密码
            password = crack_yudou_password(secret_data, html_content)
            if password:
                # 尝试直接从HTML中提取隐藏内容
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                # 查找隐藏内容
                hidden_content = soup.select_one('.cl-hidden-content')
                if hidden_content:
                    content = hidden_content.get_text().strip()
                    if content:
                        return content
                # 或者尝试查找所有可能的内容
                all_content = soup.get_text()
                # 过滤掉可能的HTML标签文本
                filtered_content = '\n'.join([line.strip() for line in all_content.split('\n') 
                                            if line.strip() and not any(keyword in line.lower() 
                                            for keyword in ['html', 'body', 'div', 'span', 'p', 'script', 'style', 'head', 'title'])])
                return filtered_content
            else:
                return encrypted_content
        except:
            return encrypted_content
    
    # 如果没有JS上下文，直接返回原始内容
    if not js_ctx:
        return encrypted_content
    
    try:
        # 尝试1：简单的Base64解码
        try:
            import base64
            # 清理可能的空白字符
            clean_content = encrypted_content.replace('\n', '').replace('\r', '').replace(' ', '')
            # 确保内容长度是4的倍数
            while len(clean_content) % 4 != 0:
                clean_content += '='
            # 尝试解码
            decoded = base64.b64decode(clean_content).decode('utf-8', errors='ignore')
            if decoded and decoded != clean_content:
                return decoded
        except:
            pass
        
        # 尝试2：URL安全的Base64解码
        try:
            import base64
            clean_content = encrypted_content.replace('\n', '').replace('\r', '').replace(' ', '')
            # URL安全Base64替换
            clean_content = clean_content.replace('-', '+').replace('_', '/')
            while len(clean_content) % 4 != 0:
                clean_content += '='
            decoded = base64.b64decode(clean_content).decode('utf-8', errors='ignore')
            if decoded and decoded != clean_content:
                return decoded
        except:
            pass
        
        # 尝试3：简单的字符替换（可能的凯撒密码）
        try:
            # 简单的字符偏移解密
            def caesar_decrypt(text, shift=3):
                result = ""
                for char in text:
                    if char.isalpha():
                        ascii_offset = 65 if char.isupper() else 97
                        result += chr((ord(char) - ascii_offset - shift) % 26 + ascii_offset)
                    else:
                        result += char
                return result
            
            decoded = caesar_decrypt(encrypted_content)
            return decoded
        except:
            pass
        
        return encrypted_content
    except:
        return encrypted_content  # 返回原始内容

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
    base_url = "https://www.yudou789.top/"
    today = get_today_str()
    
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
    
    # 步骤3：访问文章页面
    article_html = fetch_html(article_url)
    if not article_html:
        print("错误：无法访问文章页面")
        sys.exit(1)
    
    # 步骤4：查找加密文件链接
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
    
    # 直接保存txt文件到本地，不进行任何分析
    filename = f"nodes_{today}.txt"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        print(f"爬取完成！文件已保存到 {filename}")
        print(f"文件大小: {len(txt_content)} 字符")
    except Exception as e:
        print(f"错误：无法保存文件。原因：{e}")
        sys.exit(1)

if __name__ == "__main__":
    # 禁用SSL警告（有些网站证书可能有问题）
    requests.packages.urllib3.disable_warnings()
    
    main()