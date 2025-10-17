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
# Discord Webhook 設定
# ----------------------------
# GitHub Secretsで設定したシークレット名 DISCORD_WEBHOOK_URL に合わせる
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

def send_discord_message(message, max_retries=3):
    """
    Discord Webhookに通知を送信する（失敗時にはリトライ処理を実行）
    """
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ Discord Webhook URLが設定されていません")
        return
    
    url = DISCORD_WEBHOOK_URL
    headers = {"Content-Type": "application/json"}
    
    # Discordのメッセージ形式 (テキストのみ)
    data = {"content": message} 

    for attempt in range(max_retries):
        res = requests.post(url, headers=headers, json=data)
        status_code = res.status_code
        
        # Discord Webhookは通常 204 No Content が成功レスポンス
        if status_code in (200, 204):
            print(f"📤 Discord送信 (試行 {attempt + 1}/{max_retries}): 成功 (Status: {status_code})")
            break
        elif status_code == 429:
            # 429 Too Many Requests の場合、リトライ処理
            wait_time = 5 * (attempt + 1)
            print(f"🚨 429 Too Many Requests. {wait_time}秒待機して再試行します...")
            time.sleep(wait_time)
        elif status_code in (400, 404):
            # Webhook URLが無効、またはリクエスト形式が不正
            print(f"❌ 致命的なエラー {status_code}。URLまたはデータ形式を確認してください。レスポンス: {res.text}")
            break
        else:
            wait_time = 2 * (attempt + 1)
            print(f"⚠️ エラー {status_code}。{wait_time}秒待機して再試行します。")
            time.sleep(wait_time)
    else:
        print(f"💥 Discord通知が {max_retries} 回失敗しました。処理をスキップします。")

# ----------------------------
# Chrome設定 (必須)
# ----------------------------
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/128.0.0.0 Safari/537.36")

    possible_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium"
    ]
    chrome_path = next((p for p in possible_paths if os.path.exists(p)), None)
    if chrome_path:
        options.binary_location = chrome_path
    
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# ----------------------------
# スクレイピング処理 (必須)
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
    print(f"✅ {len(items)} 件取得: {url}")
    return items

# ----------------------------
# メイン処理
# ----------------------------
if __name__ == "__main__":
    favorites = json.load(open("favorites.json", "r", encoding="utf-8"))
    latest_items = {}
    
    # ✅ 修正済み: message_lines の初期化
    message_lines = [] 

    # 前回データをロード
    old_data = {}
    if os.path.exists("latest_items.json"):
        try:
            old_data = json.load(open("latest_items.json", "r", encoding="utf-8"))
        except json.JSONDecodeError:
            print("⚠️ latest_items.json が壊れていたため初期化します。")
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
            count = len(new_entries)
            # 新着件数とカテゴリ名のみをメッセージに追加（URLは含めない）
            message_lines.append(f"🎉 新着あり！【{name}】に {count} 件の新着商品があります。")
            message_lines.append("") # 区切り

    # 最新データを保存
    with open("latest_items.json", "w", encoding="utf-8") as f:
        json.dump(latest_items, f, ensure_ascii=False, indent=2)

    # Discord通知
    if message_lines:
        final_message = "--- 2ndStreet 新着通知 ---\n" + "\n".join(message_lines).strip()
        send_discord_message(final_message) 
        print("✅ 新着を通知しました。")
    else:
        print("🕊 新着なし。")

    print("完了 ✅")
