import requests, re, os, time, base64
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://www.yudou789.top/"

def get_today_str():
    return datetime.now().strftime("%Y%m%d")

def get_current_date_str():
    return datetime.now().strftime("%Y年%m月%d日")

def get_yesterday_date_str():
    return (datetime.now() - timedelta(days=1)).strftime("%Y年%m月%d日")

def extract_date_from_title(title):
    return f"{m.group(1)}{m.group(2)}{m.group(3)}" if (m:=re.search(r'(\d{4})年(\d{2})月(\d{2})日', title)) else get_today_str()

def fetch(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or 'utf-8'
        time.sleep(1)
        return resp.text
    except Exception as e:
        print(f"错误：{url} 失败 - {e}")
        return None

def main():
    print("开始获取玉豆节点...")
    
    home_html = fetch(BASE_URL)
    if not home_html:
        return
    
    # 使用BeautifulSoup查找最新文章链接
    soup = BeautifulSoup(home_html, 'html.parser')
    current_date = get_current_date_str()
    yesterday_date = get_yesterday_date_str()
    
    # 查找所有文章链接
    all_links = soup.find_all('a', href=True)
    article_url = None
    article_title = None
    
    # 优先查找今日文章
    for link in all_links:
        link_text = link.get_text().strip()
        if current_date in link_text and "免费精选节点" in link_text:
            article_url = link['href']
            article_title = link_text
            break
    
    # 如果没有今日文章，查找昨日文章
    if not article_url:
        for link in all_links:
            link_text = link.get_text().strip()
            if yesterday_date in link_text and "免费精选节点" in link_text:
                article_url = link['href']
                article_title = link_text
                break
    
    # 如果没找到特定日期的文章，尝试获取第一个文章链接
    if not article_url:
        for link in all_links:
            link_text = link.get_text().strip()
            if "免费精选节点" in link_text:
                article_url = link['href']
                article_title = link_text
                break
    
    if not article_url:
        print("错误：无法找到最新文章")
        return
    
    # 补全URL
    if not article_url.startswith('http'):
        article_url = BASE_URL + article_url
    
    print(f"找到最新文章: {article_title}")
    
    article_html = fetch(article_url)
    if not article_html:
        return
    
    # 提取密码
    soup = BeautifulSoup(article_html, 'html.parser')
    password = None
    
    # 方法1：从 data-secret 属性提取密码（使用JS解码器的方法）
    wrapper = soup.find(class_='cl-noindent-wrapper')
    
    if wrapper:
        secret = wrapper.get('data-secret')
        if secret:
            try:
                # 尝试base64解码
                password = base64.b64decode(secret).decode('utf-8')
                print(f"从data-secret解码得到密码：{password}")
            except:
                # 尝试常用密码
                common_passwords = [
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
                for pwd in common_passwords:
                    try:
                        if base64.b64encode(pwd.encode('utf-8')).decode('utf-8') == secret:
                            password = pwd
                            print(f"常用密码匹配成功：{password}")
                            break
                    except:
                        pass
    
    # 方法2：从文本中提取密码（备用方法）
    if not password:
        all_text = soup.get_text()
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
                password = matches[0]
                print(f"从文本提取得到密码：{password}")
                break
    
    if not password:
        print("未在文章中找到密码")
    
    # 查找节点链接
    txt_url = None
    # 方法1：优先查找.txt文件链接
    all_links = soup.find_all('a', href=True)
    txt_links = []
    for link in all_links:
        href = link['href']
        if '.txt' in href:
            if not href.startswith('http'):
                href = BASE_URL + href
            txt_links.append(href)
    # 方法2：在页面所有文本中搜索.txt链接
    if not txt_links:
        pattern = r'https?://[^\s"\']+\.txt'
        txt_links = re.findall(pattern, article_html)
    # 去重并返回第一个链接
    if txt_links:
        unique_links = list(dict.fromkeys(txt_links))
        txt_url = unique_links[0]
    
    if not txt_url:
        print("错误：无法找到节点链接")
        return
    print(f"找到节点链接: {txt_url}")
    
    print("获取节点内容...")
    nodes_content = fetch(txt_url)
    if not nodes_content:
        return
    print("节点内容获取成功")
    
    # 使用extract_date_from_title函数获取日期
    date_str = extract_date_from_title(article_title)
    filename = f"nodes_{date_str}.txt"
    try:
        with open(os.path.join(SCRIPT_DIR, filename), 'w', encoding='utf-8') as f:
            f.write(nodes_content)
        print(f"节点已保存到：{filename}")
    except Exception as e:
        print(f"错误：保存失败 - {e}")
    
    print("\n操作完成！")

if __name__ == "__main__":
    main()
