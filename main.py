from flask import Flask, request, abort
import os

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,FollowEvent
)

app = Flask(__name__)

#環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

alcTable = {'ビール': 0.05,'ハイボール':0.05,'酎ハイ':0.07,'ワイン':0.12,'ウイスキー':0.4}

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


def calcAlcAmount(alcKey,liquorAmount):
    return alcTable[alcKey]*liquorAmount*0.8

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    alcKey = event.message.text.split(':')[0]
    liquorAmount = int(event.message.text.split(':')[1])
    alcAmount = calcAlcAmount(alcKey,liquorAmount)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=str(alcAmount)))

@handler.add(FollowEvent)
def handle_follow(event):
   line_bot_api.reply_message(
       event.reply_token,
       TextSendMessage(text='友達追加ありがとう 接種アルコール量を計算するにはお酒:飲んだ量を入力してね'))

if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)