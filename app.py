import os
import requests
import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, JoinEvent

app = Flask(__name__)

# --- 設定區 (已填入你的 GAS 網址) ---
GAS_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzUIjJ6CO3KqG8zediAlwXFEyGOek5pZBUjIx9evYESWdjXu-N3kEpAuVcPfAjVTRT-LQ/exec" 
# --------------------------------

# 從環境變數讀取金鑰
line_bot_api = LineBotApi(os.environ.get('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('CHANNEL_SECRET'))

@app.route("/", methods=['GET'])
def home():
    return "Line Bot is Running!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# --- 當機器人加入群組時觸發 ---
@handler.add(JoinEvent)
def handle_join(event):
    group_id = event.source.group_id
    
    try:
        # 1. 取得人數 (相容性處理)
        summary = line_bot_api.get_group_members_count(group_id)
        if isinstance(summary, int):
            count = summary
        else:
            count = summary.count
            
        # 2. 嘗試取得群組名稱 (這行不一定每次成功，看權限)
        group_name = "未知群組"
        try:
            group_summary = line_bot_api.get_group_summary(group_id)
            group_name = group_summary.group_name
        except:
            pass # 如果抓不到名稱就用預設值，不影響後續流程

        # 3. 【關鍵動作】發送 POST 請求給你的 Google Sheet
        try:
            payload = {'groupId': group_id, 'groupName': group_name}
            # 這行就是把資料丟去給 GAS 秘書
            requests.post(GAS_WEB_APP_URL, json=payload)
            print(f"已自動歸檔至 Sheet: {group_name} ({group_id})")
        except Exception as e:
            print(f"寫入 Sheet 失敗: {e}")

        # 4. 在群組內回報
        reply_text = f"行動商城已進駐。\n本群組 ID: {group_id}\n目前人數: {count} 人\n(資料已自動建檔)"
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
        
    except Exception as e:
        print(f"Error: {e}")
        # 出錯還是要讓你知道 ID
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"發生錯誤，但 ID 為: {group_id}")
        )

if __name__ == "__main__":
    app.run()
