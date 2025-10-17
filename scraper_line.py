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

def send_line_message(message, max_retries=3):
    """
    LINE通知を送信する（429エラー時にはリトライ処理を実行）
    """
    if not LINE_ACCESS_TOKEN or not LINE_USER_ID:
        print("⚠️ LINEのトークンまたはユーザーIDが設定されていません")
        return
    
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    
    # LINEの1メッセージは最大2000文字。それを超える場合は分割
    if len(message) > 2000:
        messages = [message[i:i + 2000] for i in range(0, len(message), 2000)]
    else:
        messages = [message]

    # メッセージごとの送信処理
    for msg in messages:
        data = {"to": LINE_USER_ID, "messages": [{"type": "text", "text": msg}]}
        
        for attempt in range(max_retries):
            res = requests.post(url, headers=headers, json=data)
            status_code = res.status_code
            print(f"📤 LINE送信 (試行 {attempt + 1}/{max_retries}): {status_code}")
            
            if status_code == 200:
                # 成功
                break
            elif status_code == 429:
                # 429 Too Many Requests の場合
                # 待機時間を長くして再試行
                wait_time = 5 * (attempt + 1)
                print(f"🚨 429 Too Many Requests. {wait_time}秒待機して再試行します...")
                time.sleep(wait_time)
            elif status_code in (400, 401, 403):
                # 致命的なエラー（認証失敗、不正なリクエストなど）
                print(f"❌ 致命的なエラー {status_code}。再試行を中止します。レスポンス: {res.text}")
                break
            else:
                # その他のエラー（500系など）
                wait_time = 2 * (attempt + 1)
                print(f"⚠️ エラー {status_code}。{wait_time}秒待機して再試行します。")
                time.sleep(wait_time)
        else:
            # max_retries回試行しても成功しなかった場合
            print(f"💥 LINE通知が {max_retries} 回失敗しました。処理をスキップします。")


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
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/128.0.0.0 Safari/537.36")

    # 既存のChromeパス検索ロジックは維持
    possible_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium"
    ]
    chrome_path = next((p for p in possible_paths if os.path.exists(p)), None)
    if chrome_path:
        options.binary_location = chrome_path
    else:
        # ChromeDriverManagerを使用してWebDriverを自動でダウンロード・設定
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
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
    print(f"✅ {len(items)} 件取得: {url}")
    return items


# ----------------------------
# メイン処理
# ----------------------------
if __name__ == "__main__":
    favorites = json.load(open("favorites.json", "r", encoding="utf-8"))
    latest_items = {}
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
            # ★ 変更点: 新着件数とカテゴリ名のみをメッセージに追加
            message_lines.append(f"🎉 新着あり！【{name}】に {count} 件の新着商品があります。")
            message_lines.append("") # 区切り

    # 最新データを保存
    with open("latest_items.json", "w", encoding="utf-8") as f:
        json.dump(latest_items, f, ensure_ascii=False, indent=2)

    # LINE通知
    if message_lines:
        # メッセージをまとめて通知
        final_message = "--- 新着通知 ---\n" + "\n".join(message_lines).strip()
        send_line_message(final_message)
        print("✅ 新着を通知しました。")
    else:
        print("🕊 新着なし。")

    print("完了 ✅")
