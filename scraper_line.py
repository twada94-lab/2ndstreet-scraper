import os
import json
import time
import requests
# 他のimportは省略

# ----------------------------
# Discord Webhook 設定
# ----------------------------
# GitHub Secretsで設定したシークレット名 (例: DISCORD_WEBHOOK_URL) に合わせる
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
            # Discordもレート制限があるが、LINEより緩やか。リトライ処理は維持。
            wait_time = 5 * (attempt + 1) # 5秒、10秒、15秒と待機
            print(f"🚨 429 Too Many Requests. {wait_time}秒待機して再試行します...")
            time.sleep(wait_time)
        elif status_code in (400, 404):
            # Webhook URLが無効、またはリクエスト形式が不正
            print(f"❌ 致命的なエラー {status_code}。URLまたはデータ形式を確認してください。")
            break
        else:
            wait_time = 2 * (attempt + 1)
            print(f"⚠️ エラー {status_code}。{wait_time}秒待機して再試行します。")
            time.sleep(wait_time)
    else:
        print(f"💥 Discord通知が {max_retries} 回失敗しました。処理をスキップします。")

# ----------------------------
# メイン処理の変更
# ----------------------------
if __name__ == "__main__":
    # ... (スクレイピングと新着判定のロジックは省略、変更なし) ...

    # LINE通知だった箇所をDiscord通知に変更
    if message_lines:
        final_message = "--- 2ndStreet 新着通知 ---\n" + "\n".join(message_lines).strip()
        send_discord_message(final_message) # 関数名を変更
        print("✅ 新着を通知しました。")
    else:
        print("🕊 新着なし。")

    print("完了 ✅")
