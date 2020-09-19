from flask import Flask, request, abort
import os

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,FollowEvent,
    QuickReply, QuickReplyButton,MessageAction
)

app = Flask(__name__)

#環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

alcTable = {'ビール': 0.05,'ハイボール':0.05,'酎ハイ':0.07,'白ワイン':0.13,'赤ワイン':0.14,'ウイスキー':0.4}
userWeight = 60

@app.route("/")
def hello_world():
    return "hello_world"

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    recievedMessageText = event.message.text
    
    if ':' in recievedMessageText:
        alcKey,liquorAmount = recievedMessageText.split(':')
        if (alcKey in alcTable.keys()) and (liquorAmount.isdigit):
            alcAmount = round(alcTable[alcKey]*int(liquorAmount)*0.8,1)
            #resolutionTime = alcAmount / (userWeight*0.1)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=str(alcAmount)))
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="入力形式が間違ってますよ")
            )

@handler.add(FollowEvent)
def handle_follow(event):
    line_bot_api.reply_message(
       event.reply_token,
       TextSendMessage(text='友達追加ありがとう!接種アルコール量を計算するにはお酒:飲んだ量を入力してね. ビール、ウイスキー、赤ワイン、白ワイン、酎ハイ、ハイボールなら計算できます。'))
    weightList = ["40kgくらい","50kgくらい","60kgくらい","70kgくらい","80kgくらい"]
    items = [QuickReplyButton(action=MessageAction(label=f"{weight}",text=f"{weight}です")) for weight in weightList]
    messages = TextSendMessage(text="体重はどれくらいですか？",
                               quick_reply=QuickReply(items=items))
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=messages)
    )

if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)

