"""抓取 cwl.gov.cn/ygkj/kjgg/ 列表页，解析数据并保存到JSON文件"""
import requests
import re
import json
from bs4 import BeautifulSoup

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Cookie': 'HMF_C1=0d3831b75a5743fd8d6c009d0357374f7c753e1aad3ededb8226f5cb3f4b1b38a091a2dedae26b5af96ca4f95ec237ef1902a9c2309ba6375859c9543f5eb69d04; C3VK=40cfd2; 21_vq=28',
    'Host': 'www.cwl.gov.cn',
    'Referer': 'https://www.cwl.gov.cn/ygkj/kjgg/',
    'Sec-Ch-Ua': '"Chromium";v="146", "Not:A-Brand";v="24"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"macOS"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
}

url = "https://www.cwl.gov.cn/ygkj/kjgg/"

print("Requesting:", url)
resp = requests.get(url, headers=headers, timeout=15)
print(f"Status: {resp.status_code}, Size: {len(resp.text)}")

# 保存原始HTML
with open("cache/kjgg_list.html", "w", encoding="utf-8") as f:
    f.write(resp.text)

soup = BeautifulSoup(resp.text, "html.parser")
result = {}

# 1. 标题
result["title"] = soup.title.string if soup.title else ""

# 2. 所有链接
result["all_links"] = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    text = a.get_text(strip=True)
    if text and len(text) > 0:
        result["all_links"].append({"href": href, "text": text})

# 3. 筛选 shtml 链接
result["shtml_links"] = [l for l in result["all_links"] if ".shtml" in l["href"]]

# 4. 表格数据
result["tables"] = []
for table in soup.find_all("table"):
    table_data = []
    for tr in table.find_all("tr"):
        row = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        table_data.append(row)
    if table_data:
        result["tables"].append(table_data)

# 5. 所有 div 内容 (找开奖相关)
result["key_divs"] = []
for div in soup.find_all("div"):
    text = div.get_text(strip=True)
    cls = div.get("class", [])
    id_ = div.get("id", "")
    if text and 5 < len(text) < 500:
        result["key_divs"].append({
            "class": cls,
            "id": id_,
            "text": text[:200]
        })

# 6. script 内容
result["scripts"] = []
for script in soup.find_all("script"):
    src = script.get("src", "")
    text = script.get_text(strip=True)
    if text:
        result["scripts"].append({"src": src, "content": text[:500]})

# 7. 查找包含数字的链接和文本（可能是期号+号码）
result["number_patterns"] = []
# 找所有包含7位数字的文本
for elem in soup.find_all(string=re.compile(r'\d{7}')):
    parent = elem.parent
    text = parent.get_text(strip=True)
    href = ""
    if parent.name == "a" and parent.get("href"):
        href = parent["href"]
    elif parent.find_parent("a"):
        href = parent.find_parent("a").get("href", "")
    result["number_patterns"].append({"text": text[:100], "href": href})

# 保存结果到 JSON
output_path = "cache/kjgg_parsed.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"Result saved to: {output_path}")
print(f"shtml links: {len(result['shtml_links'])}")
print(f"tables: {len(result['tables'])}")
print(f"number patterns: {len(result['number_patterns'])}")
