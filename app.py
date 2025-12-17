import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, JoinEvent

app = Flask(__name__)

# 從環境變數讀取鑰匙 (等一下在 Render 設定)
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

# --- 重頭戲：當機器人加入群組時觸發 ---
@handler.add(JoinEvent)
def handle_join(event):
    # 1. 抓出群組 ID
    group_id = event.source.group_id
    
    # 2. 立刻向 LINE 查詢該群組目前人數
    try:
        summary = line_bot_api.get_group_members_count(group_id)
        member_count = summary.count
        
        # 3. 在群組內回報 (或是你可以只選擇存到後台不說話)
        reply_text = f"報告！審計機器人已進駐。\n本群組 ID: {group_id}\n目前人數: {member_count} 人"
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
        # 這裡未來可以加入寫入 Google Sheet 的程式碼
        print(f"Join Group: {group_id}, Count: {member_count}")
        
    except Exception as e:
        print(f"Error getting count: {e}")

if __name__ == "__main__":
    app.run()
