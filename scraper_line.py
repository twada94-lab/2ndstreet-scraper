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
    if not LINE_ACCESS_TOKEN or not LINE_USER_ID:
        print("⚠️ LINEのトークンまたはユーザーIDが設定されていません")
        return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    data = {"to": LINE_USER_ID, "messages": [{"type": "text", "text": message}]}
    res = requests.post(url, headers=headers, json=data)
    print("📤 LINE送信:", res.status_code)


# ----------------------------
# Chrome設定（Mac対応）
# ----------------------------
def get_driver():
    options = Options()
    options.add_argument("--headless")  # 画面非表示
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/128.0.0.0 Safari/537.36")

    # macOS の Chrome 実行パス候補
    possible_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium"
    ]

    chrome_path = next((p for p in possible_paths if os.path.exists(p)), None)
    if chrome_path:
        options.binary_location = chrome_path
    else:
        raise FileNotFoundError("Google Chrome が見つかりません。インストールしてください。")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


# ----------------------------
# スクレイピング処理（Selenium）
# ----------------------------
def get_items(url):
    driver = get_driver()
    driver.get(url)
    time.sleep(8)  # ページが完全に読み込まれるのを待つ

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

    print(f"✅ {len(items)} 件取得: {url}")
    return items


# ----------------------------
# メイン処理
# ----------------------------
if __name__ == "__main__":
    favorites = json.load(open("favorites.json", "r", encoding="utf-8"))
    latest_items = {}
    message_lines = []

    if os.path.exists("latest_items.json"):
        old_data = json.load(open("latest_items.json", "r", encoding="utf-8"))
    else:
        old_data = {}

    for fav in favorites:
        name = fav["name"]
        url = fav["url"]
        print(f"🔍 {name} をチェック中...")

        new_items = get_items(url)
        latest_items[name] = new_items

        old_urls = {i["url"] for i in old_data.get(name, [])}
        new_entries = [i for i in new_items if i["url"] not in old_urls]

        if new_entries:
            message_lines.append(f"🎉 {name} に新着商品があります！")
            for item in new_entries[:5]:
                message_lines.append(f"{item['name']}\n{item['url']}")
            message_lines.append("")  # 区切り

    # 最新データを保存
    with open("latest_items.json", "w", encoding="utf-8") as f:
        json.dump(latest_items, f, ensure_ascii=False, indent=2)

    # LINE通知
    if message_lines:
        send_line_message("\n".join(message_lines))
        print("✅ 新着を通知しました。")
    else:
        print("🕊 新着なし。")

    print("完了 ✅")
