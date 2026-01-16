import cloudscraper
from bs4 import BeautifulSoup
import os
import time
import random
import requests

# 環境変数
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
COUNT_FILE = "latest_count.txt"
# ★ ここに検索結果のURLを貼り付けてください
TARGET_URL = "https://www.2ndstreet.jp/search?..." 

def get_current_count():
    # ブラウザのふりをするスキャナーを作成
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    try:
        # 念のため実行直後に少し待機(3〜7秒)
        time.sleep(random.uniform(3, 7))
        
        response = scraper.get(TARGET_URL, timeout=30)
        
        if response.status_code == 403:
            print("❌ アクセスが拒否されました(403)。しばらく時間を置く必要があります。")
            return None
            
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 指定されたID(#ecResultNum)内のspanを取得
        target_span = soup.select_one('#ecResultNum span')
        
        if target_span:
            text_num = target_span.get_text().strip().replace(',', '')
            return int(text_num)
        else:
            print("❌ 件数表示要素が見つかりませんでした。")
            return None

    except Exception as e:
        print(f"❌ エラー発生: {e}")
        return None

def main():
    current_count = get_current_count()
    
    if current_count is None:
        return

    # 前回の数値を読み込み
    last_count = 0
    if os.path.exists(COUNT_FILE):
        with open(COUNT_FILE, "r") as f:
            try:
                last_count = int(f.read().strip())
            except:
                last_count = 0

    print(f"前回: {last_count}件 / 今回: {current_count}件")

    # 増加した場合のみDiscord通知
    if current_count > last_count:
        diff = current_count - last_count
        msg = f"🔔 **新着アイテム入荷！**\n在庫が {last_count}件 → {current_count}件 に増加（+{diff}件）\n{TARGET_URL}"
        if DISCORD_WEBHOOK_URL:
            requests.post(DISCORD_WEBHOOK_URL, json={"content": msg})
    
    # 数値を保存
    with open(COUNT_FILE, "w") as f:
        f.write(str(current_count))

if __name__ == "__main__":
    main()
