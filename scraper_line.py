import requests
from bs4 import BeautifulSoup
import os
import re
import sys

# Discord設定
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# 保存用ファイル名（件数だけを記録するテキストファイル）
COUNT_FILE = "latest_count.txt"

# ターゲットのURL（ご自身の検索条件のURLを入れてください）
TARGET_URL = "https://www.2ndstreet.jp/search?keyword=&selected_category=&brand%5B%5D=001269&brand%5B%5D=000871&brand%5B%5D=002098&brand%5B%5D=006204&brand%5B%5D=000567&brand%5B%5D=000269&brand%5B%5D=004814&brand%5B%5D=003655&brand%5B%5D=006633&brand%5B%5D=000131&minPrice=&maxPrice=100000&sortBy=arrival&category=910001&td_seg=tds279974" 

def send_discord_notify(message):
    if not DISCORD_WEBHOOK_URL:
        print("Discord Webhook URL is not set.")
        return
    data = {"content": message}
    requests.post(DISCORD_WEBHOOK_URL, json=data)

def get_current_count():
    try:
        # User-Agentを設定（必須）
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(TARGET_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")

        # ★変更点: 画像の構造に合わせてピンポイントで取得
        # <div id="ecResultNum"> の中の <span> タグを取得
        target_span = soup.select_one('#ecResultNum span')
        
        if target_span:
            # テキストを取得 (例: "22,352")
            text_num = target_span.get_text().strip()
            
            # カンマを除去して数値化
            return int(text_num.replace(',', ''))
        else:
            print("件数表示(ecResultNum)が見つかりませんでした。")
            return None

    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def main():
    # 1. 現在の件数を取得
    current_count = get_current_count()
    if current_count is None:
        return

    print(f"現在の件数: {current_count}")

    # 2. 前回の件数を読み込み
    last_count = 0
    if os.path.exists(COUNT_FILE):
        with open(COUNT_FILE, "r") as f:
            try:
                content = f.read().strip()
                if content:
                    last_count = int(content)
            except ValueError:
                last_count = 0
    
    print(f"前回の件数: {last_count}")

    # 3. 比較ロジック: 現在の件数が前回より多ければ通知
    if current_count > last_count:
        diff = current_count - last_count
        msg = f"🔔 **新着アイテムがあります！**\n在庫が {last_count}件 → {current_count}件 に増えました（+{diff}件）\n{TARGET_URL}"
        print("通知を送信します...")
        send_discord_notify(msg)
    elif current_count < last_count:
        print(f"在庫が減りました ({last_count} -> {current_count})。通知はしません。")
    else:
        print("件数に変化はありません。")

    # 4. 最新の件数をファイルに保存
    # (増えたときだけでなく、減ったときも次回のために更新しておく必要があります)
    with open(COUNT_FILE, "w") as f:
        f.write(str(current_count))

if __name__ == "__main__":
    main()
