import requests, re, os, base64, sys
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

BASE_URL = "https://www.yudou789.top/"

def fetch(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or 'utf-8'
        return resp.text
    except:
        return None

def main():
    home = fetch(BASE_URL)
    if not home:
        return
    soup = BeautifulSoup(home, 'html.parser')
    cur = datetime.now().strftime("%Y年%m月%d日")
    yes = (datetime.now() - timedelta(1)).strftime("%Y年%m月%d日")
    article_url = None
    title = ""
    for a in soup.find_all('a', href=True):
        t = a.get_text().strip()
        if "免费精选节点" in t and (cur in t or yes in t):
            article_url, title = a['href'], t
            break
    if not article_url:
        for a in soup.find_all('a', href=True):
            t = a.get_text().strip()
            if "免费精选节点" in t:
                article_url, title = a['href'], t
                break
    if not article_url:
        return
    if not article_url.startswith('http'):
        article_url = BASE_URL + article_url

    art = fetch(article_url)
    if not art:
        return
    soup = BeautifulSoup(art, 'html.parser')
    password = None
    wrap = soup.find(class_='cl-noindent-wrapper')
    if wrap:
        sec = wrap.get('data-secret')
        if sec:
            try:
                password = base64.b64decode(sec).decode('utf-8')
            except:
                pass
    if not password:
        m = re.search(r'(?:密码|提取码|key)[：:=]\s*(\d{4})', art, re.I)
        if m:
            password = m.group(1)

    txt_url = None
    for a in soup.find_all('a', href=True):
        if '.txt' in a['href']:
            txt_url = a['href']
            break
    if not txt_url:
        urls = re.findall(r'https?://[^\s"\'<>]+\.txt', art)
        if urls:
            txt_url = urls[0]
    if not txt_url:
        return
    if not txt_url.startswith('http'):
        txt_url = BASE_URL + txt_url

    content = fetch(txt_url)
    if not content:
        return

    m = re.search(r'(\d{4})年(\d{2})月(\d{2})日', title)
    date_str = f"{m[1]}{m[2]}{m[3]}" if m else datetime.now().strftime("%Y%m%d")
    filename = f"nodes_{date_str}.txt"
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), filename), 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    main()
