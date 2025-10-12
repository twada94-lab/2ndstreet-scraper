import os
import json
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# ----------------------------
# LINE 設定
# ----------------------------
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")

def send_line_message(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    data = {"to": LINE_USER_ID, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=data)


# ----------------------------
# Chrome設定
# ----------------------------
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    chrome_path = os.getenv("CHROME_BIN", "/usr/bin/chromium-browser")
    if not os.path.exists(chrome_path):
        for path in ["/usr/bin/google-chrome", "/usr/bin/chromium"]:
            if os.path.exists(path):
                chrome_path = path
                break
    options.binary_location = chrome_path

    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


# ----------------------------
# スクレイピング処理
# ----------------------------
def get_items(url):
    driver = get_driver()
    driver.get(url)
    time.sleep(8)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    items = []
    for li in soup.select("ul.itemCardList li"):
        name = li.select_one(".itemCard_name")
        link = li.select_one("a[href^='/goods/detail/']")
        if not (name and link):
            continue
        items.append({
            "name": name.get_text(strip=True),
            "url": "https://www.2ndstreet.jp" + link.get("href")
        })
    return items


# ----------------------------
# 新着チェック
# ----------------------------
def load_previous(fav_name):
    file = f"data_{fav_name}.json"
    return json.load(open(file, "r", encoding="utf-8")) if os.path.exists(file) else []

def save_current(fav_name, items):
    file = f"data_{fav_name}.json"
    with open(file, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def detect_new(new, old):
    old_urls = {i["url"] for i in old}
    return [i for i in new if i["url"] not in old_urls]


# ----------------------------
# メイン処理
# ----------------------------
if __name__ == "__main__":
    favorites = json.load(open("favorites.json", "r", encoding="utf-8"))

    for fav in favorites:
        name = fav["name"]
        url = fav["url"]
        print(f"🔍 {name} をチェック中...")

        new_items = get_items(url)
        old_items = load_previous(name)
        new_entries = detect_new(new_items, old_items)

        if new_entries:
            message = f"🎉 {name} に新着商品があります！\n\n"
            message += "\n\n".join([
                f"{item['name']}\n{item['url']}"
                for item in new_entries[:5]
            ])
            send_line_message(message)
            print(f"✅ {len(new_entries)} 件の新着を通知しました。")
            save_current(name, new_items)
        else:
            print(f"🕊 {name} に新着なし。")

    print("完了 ✅")
