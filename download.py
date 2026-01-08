import requests
import json
import time
import os

TOKEN = os.environ.get("TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
FILE_NAME = "slack_full_export.json"

headers = {"Authorization": f"Bearer {TOKEN}"}

def get_replies(channel_id, thread_ts):
    """スレッド内の全返信を取得する"""
    url = "https://slack.com/api/conversations.replies"
    replies = []
    cursor = None
    
    while True:
        params = {"channel": channel_id, "ts": thread_ts}
        if cursor:
            params["cursor"] = cursor
        
        res = requests.get(url, headers=headers, params=params).json()
        if not res.get("ok"): break
        
        # 最初の1件は親メッセージなので、2件目以降（返信）を追加
        msgs = res.get("messages", [])
        if not cursor:
            replies.extend(msgs[1:]) 
        else:
            replies.extend(msgs)
            
        cursor = res.get("response_metadata", {}).get("next_cursor")
        if not cursor: break
        time.sleep(1)
        
    return replies

def fetch_everything(channel_id):
    url = "https://slack.com/api/conversations.history"
    all_data = []
    cursor = None

    while True:
        params = {"channel": channel_id, "limit": 100}
        if cursor:
            params["cursor"] = cursor
            
        res = requests.get(url, headers=headers, params=params).json()
        if not res.get("ok"):
            print(f"Error: {res.get('error')}")
            break

        messages = res.get("messages", [])
        for msg in messages:
            all_data.append(msg)
            
            # スレッドが存在し、かつ自分が親である場合（reply_count > 0）
            if "thread_ts" in msg and msg.get("reply_count", 0) > 0:
                print(f"  -> スレッド取得中: {msg['ts']}")
                replies = get_replies(channel_id, msg["thread_ts"])
                all_data.extend(replies)

        print(f"{len(all_data)} 件のメッセージ（スレッド込）を保持...")
        
        cursor = res.get("response_metadata", {}).get("next_cursor")
        if not cursor: break
        time.sleep(1)

    return all_data

# 実行
full_messages = fetch_everything(CHANNEL_ID)
with open(FILE_NAME, "w", encoding="utf-8") as f:
    json.dump(full_messages, f, ensure_ascii=False, indent=4)

print(f"完了！合計 {len(full_messages)} 件保存しました。")
