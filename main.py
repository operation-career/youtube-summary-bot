from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

# === OpenAIのAPIキーを設定 ===
openai.api_key = os.getenv("OPENAI_API_KEY")

# === Google Sheets認証 ===
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(credentials)

# === 対象スプレッドシートとシート名 ===
spreadsheet = client.open('YouTube新台収集一覧')
sheet = spreadsheet.worksheet('動画一覧')

# === YouTubeの字幕取得 + 要約 ===
def summarize_video(video_url, row_idx):
    try:
        video_id = re.search(r"v=([a-zA-Z0-9_-]{11})", video_url).group(1)
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ja'])
        text = ' '.join([entry['text'] for entry in transcript_list])

        # ChatGPTで要約
        summary = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "以下のYouTube字幕を3〜5行で簡潔に要約してください。"},
                {"role": "user", "content": text}
            ],
            max_tokens=500
        )['choices'][0]['message']['content']

        # シートに書き込み（G列：文字起こし、H列：要約）
        sheet.update_cell(row_idx, 7, text[:4000])  # 字幕（最大4000字）
        sheet.update_cell(row_idx, 8, summary)

        print(f"[成功] {video_url}")
    except TranscriptsDisabled:
        print(f"[字幕なし] {video_url}")
        sheet.update_cell(row_idx, 7, '字幕なし')
        sheet.update_cell(row_idx, 8, '要約不可')

# === 全行走査して処理（未処理のみ） ===
def run_all():
    all_rows = sheet.get_all_values()
    for i, row in enumerate(all_rows[1:], start=2):  # ヘッダー行を除く
        if row[6] in ['', '（あとで字幕取得）']:
            summarize_video(row[3], i)

if __name__ == "__main__":
    run_all()
