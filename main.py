import os
import re
import requests

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv(verbose=True)
# トークン設定
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# 反応するチャンネルのID（環境変数から取得）
TARGET_CHANNEL_ID = os.environ.get("TARGET_CHANNEL_ID")

# Dify API設定
DIFY_API_KEY = os.environ.get("DIFY_API_KEY")
DIFY_API_URL = "https://api.dify.ai/v1/workflows/run"


# arXiv URLを検出する関数
def extract_arxiv_url(text):
    pattern = r"(https://arxiv\.org/abs/\d+\.\d+)"
    match = re.search(pattern, text)
    return match.group(1) if match else None


# Dify APIにリクエストを送信する関数
def send_to_dify(arxiv_url):
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "inputs": {"arxiv_url": arxiv_url},
        "response_mode": "blocking",
        "user": "slack-bot"
    }
    response = requests.post(DIFY_API_URL, headers=headers, json=data)
    return response.json()


# 全てのメッセージを取得するためのイベントハンドラ
@app.message("")
def handle_message(message, say):
    input_text = message["text"]
    thread_ts = message.get("thread_ts")
    channel = message["channel"]

    print("Message - input_text: ", input_text)
    print("Message - thread_ts: ", thread_ts)
    print("Message - channel: ", channel)

    # 特定のチャンネルのメッセージにのみ反応
    if channel == TARGET_CHANNEL_ID:
        # arXiv URLが含まれているか確認
        arxiv_url = extract_arxiv_url(input_text)
        if arxiv_url:
            # Dify APIにリクエストを送信
            dify_response = send_to_dify(arxiv_url)

            # レスポンスからテキストを抽出
            response_text = dify_response.get("data", {}).get("outputs", {}).get("text", "応答を取得できませんでした。")

            # Slackに通知
            res_text = f"arXiv URLを検出しました: {arxiv_url}\n\n解析結果:\n{response_text}"
            if thread_ts is not None:
                say(text=res_text, thread_ts=thread_ts, channel=channel)
            else:
                say(text=res_text, channel=channel)
        else:
            print("No arXiv URL detected in the message")
    else:
        print(f"Message received in non-target channel: {channel}")


# アプリ起動
if __name__ == "__main__":
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()
