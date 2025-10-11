from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import time
import os
import json
import shutil  # Chrome実行ファイル検出用

# --------------------------------------
# LINE設定
# --------------------------------------
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN", "48MZBofEnL2CTS8ciE1Z6Jb9bIs/Yt+SK/SJ4lTqh3J20ec2xH90MkdQ60+uvF+/RSaIuQQOaQVK0+YUOMcMTrsq5K/ILBPkX1vi9W0ZBOpJ556ZWlUeV2GW0zSCSdyZKLTwrtySzt8dXXWs62TzfQdB04t89/1O/w1cDnyilFU=")
LINE_USER_ID = os.getenv("LINE_USER_ID", "U54af60e7c9fa2e22dab3b148b5188d8c")


def send_line_message(message):
    """LINEに通知を送る関数"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    body = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    res = requests.post(url, headers=headers, json=body)
    print("LINE通知結果:", res.status_code, res.text)


# --------------------------------------
# スクレイピング設定
# --------------------------------------
URL = "https://www.2ndstreet.jp/search?keyword=%E3%83%95%E3%83%A9%E3%82%A4%E3%83%88%E3%82%B8%E3%83%A3%E3%82%B1%E3%83%83%E3%83%88&sortBy=arrival"
DATA_FILE = "latest_items.json"


def get_items(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/118.0.5993.118 Safari/537.36"
    )

    # ✅ Render環境で存在するChromeパスを自動検出
    possible_paths = [
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium"
    ]
    for path in possible_paths:
        if shutil.which(path):
            options.binary_location = path
            break
    else:
        raise FileNotFoundError("Chrome 実行ファイルが見つかりません")

    # ✅ ChromeDriver起動
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.get(url)
    time.sleep(8)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # デバッグ保存
    with open("debug.html", "w", encoding="utf-8") as f:
        f.write(soup.prettify())

    driver.quit()

    items = []
    for li in soup.select("ul.itemCardList li"):
        brand = li.select_one(".itemCard_brand")
        name = li.select_one(".itemCard_name")
        price = li.select_one(".itemCard_price")
        link = li.select_one("a[href^='/goods/detail/']")
        if not (name and link):
            continue
        items.append({
            "brand": brand.get_text(strip=True) if brand else "",
            "name": name.get_text(strip=True),
            "price": price.get_text(strip=True) if price else "",
            "url": "https://www.2ndstreet.jp" + link.get("href")
        })
    return items


def load_previous_items():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_items(items):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def detect_new_items(new_items, old_items):
    old_urls = {item["url"] for item in old_items}
    return [item for item in new_items if item["url"] not in old_urls]


if __name__ == "__main__":
    print("スクレイピング開始...")
    new_items = get_items(URL)
    old_items = load_previous_items()
    new_entries = detect_new_items(new_items, old_items)

    if new_entries:
        print(f"新着 {len(new_entries)} 件を検出！LINE通知を送信します。")
        message = "\n".join([f"{i['brand']} {i['name']}\n{i['price']}\n{i['url']}" for i in new_entries[:3]])
        send_line_message(f"新着商品がありました！\n\n{message}")
        save_items(new_items)
    else:
        print("新着商品はありません。")
