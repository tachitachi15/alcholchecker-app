from flask import Flask, request, abort
import os
import psycopg2

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,FollowEvent,UnfollowEvent
)

app = Flask(__name__)

#環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]
DATABASE_URL = os.environ.get("YOUR_DATABASE_URL")

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

alcTable = {'ビール': 0.05,'ハイボール':0.05,'酎ハイ':0.07,'白ワイン':0.13,'赤ワイン':0.14,'ウイスキー':0.4}

def get_connection():
    return psycopg2.connect(DATABASE_URL)

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
    userId = event.source.userId
    #ユーザーの重さ情報登録
    if 'kg' in recievedMessageText: #ここはクイックリプライの応答を受け取るようにしたい
        userWeight = int(recievedMessageText.split('kg'))
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO weighttable (userId,userWeight) VALUES ({0},{1})".format(userId,userWeight))


    if ':' in recievedMessageText:
        alcKey,liquorAmount = recievedMessageText.split(':')
        if (alcKey in alcTable.keys()) and (liquorAmount.isdigit):
            alcAmount = round(alcTable[alcKey]*int(liquorAmount)*0.8,1)
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT userWeight FROM weighttable WHERE userId = '{}'".format(userId))
                    row = cur.fetchone()
                    userWeight = row[0]
            resolutionTime = round(alcAmount / (userWeight*0.1),1) 
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="接種アルコール量は"+str(alcAmount)+'gです.分解には約'+str(resolutionTime)+'時間かかります'))
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="対応していないお酒かお酒の量の書き方が間違っています")
            )
    
        

@handler.add(FollowEvent)
def handle_follow(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="お酒の種類:飲んだ量(ml)を教えてくれると、アルコールの摂取量と分解にかかる時間を計算します。")
    )
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="まず計算に必要なので体重を教えてください") #クイックリプライ使いたい
    )

@handler.add(UnfollowEvent)
def handle_unfollow(event):
    #データベースからユーザーIDと体重データ削除
    userId = event.source.userId
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.exe("DELETE FROM weighttable WHERE userId = '{}'".format(userId))
 
if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)

