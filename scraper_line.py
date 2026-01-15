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
TARGET_URL = "https://www.2ndstreet.jp/search?..." 

def send_discord_notify(message):
    if not DISCORD_WEBHOOK_URL:
        print("Discord Webhook URL is not set.")
        return
    data = {"content": message}
    requests.post(DISCORD_WEBHOOK_URL, json=data)

def get_current_count():
    try:
        # User-Agentを設定してブラウザのふりをする
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(TARGET_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")

        # ★重要: 件数が書かれている場所を取得
        # 2ndStreetの場合、通常 <span class="srchNum">123</span> のような箇所か、
        # ヘッダーテキスト内の「全 123件」などを探します。
        # ※ 実際のHTMLに合わせてクラス名は調整してください
        
        # 例: ページ内の「件」を含むテキストを探して数字を抽出する汎用的な方法
        # 特定のクラスがわかっている場合は soup.select_one('.className').text などが良いです
        body_text = soup.body.get_text()
        
        # 正規表現で「全 XXX 件」や「XXX件」の数字を探す
        # サイトによって表記が違うため、実際に取得できるテキストに合わせて調整が必要です
        # ここでは簡易的に「数字 + 件」のパターンで最初の数字を取得します
        match = re.search(r'([\d,]+)\s*件', body_text)
        
        if match:
            # カンマを除去して数値化 (例: "1,200" -> 1200)
            return int(match.group(1).replace(',', ''))
        else:
            print("件数が見つかりませんでした。")
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
