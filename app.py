import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, JoinEvent

app = Flask(__name__)

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

# --- 核心邏輯：當機器人被邀入群組時 ---
@handler.add(JoinEvent)
def handle_join(event):
    group_id = event.source.group_id
    
    try:
        # 取得人數 (這裡做了修復，不管是數字還是物件都能處理)
        summary = line_bot_api.get_group_members_count(group_id)
        
        if isinstance(summary, int):
            member_count = summary
        else:
            member_count = summary.count
            
        # 回報訊息
        reply_text = f"報告！審計機器人已進駐。\n本群組 ID: {group_id}\n目前人數: {member_count} 人"
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
        print(f"Join Group: {group_id}, Count: {member_count}")
        
    except Exception as e:
        print(f"Error getting count: {e}")
        # 如果出錯，至少回報一下 ID，方便除錯
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"已進駐，但讀取人數失敗。\nID: {group_id}")
        )

if __name__ == "__main__":
    app.run()
