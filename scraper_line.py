import requests
from bs4 import BeautifulSoup
import os
import time

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
COUNT_FILE = "latest_count.txt"
TARGET_URL = "https://www.2ndstreet.jp/search?..." # あなたのURL

def get_current_count():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Referer": "https://www.2ndstreet.jp/"
    }
    try:
        # 少し待機を入れる（アクセスをバラけさせる）
        time.sleep(2)
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        
        # 403が出た場合にエラー内容を表示
        if response.status_code == 403:
            print("❌ アクセスがブロックされました(403)。頻度を下げる必要があります。")
            return None
            
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        target_span = soup.select_one('#ecResultNum span')
        
        if target_span:
            return int(target_span.get_text().strip().replace(',', ''))
    except Exception as e:
        print(f"❌ エラー発生: {e}")
    return None

def main():
    current_count = get_current_count()
    
    # 取得失敗時はファイルを作らずに終了
    if current_count is None:
        # Gitエラーを防ぐため、ファイルがなければ空で作っておく
        if not os.path.exists(COUNT_FILE):
            with open(COUNT_FILE, "w") as f:
                f.write("0")
        return

    # 前回の数値読み込み
    last_count = 0
    if os.path.exists(COUNT_FILE):
        with open(COUNT_FILE, "r") as f:
            try:
                last_count = int(f.read().strip())
            except: last_count = 0

    if current_count > last_count:
        msg = f"🔔 新着あり！ {last_count} -> {current_count}\n{TARGET_URL}"
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg})
    
    # ファイルを更新
    with open(COUNT_FILE, "w") as f:
        f.write(str(current_count))
    print(f"成功: 現在 {current_count}件")

if __name__ == "__main__":
    main()
