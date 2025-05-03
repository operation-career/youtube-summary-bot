import os
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

# 定数（スプレッドシート情報）
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1vi_7UZg0LlyCymS1yVC4gs7DXroVoD8nbpyBoOBTjok/edit?gid=0"
SHEET_NAME = "動画一覧"
COLUMN_URL = "動画URL"
COLUMN_TRANSCRIPT = "字幕/文字起こし"
COLUMN_SUMMARY = "要約"

# OpenAI APIキーの設定
openai.api_key = os.getenv("OPENAI_API_KEY")

# Google Sheets API認証
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "/etc/secrets/credentials.json"
credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
gc = gspread.authorize(credentials)

# スプレッドシートとシートの読み込み
spreadsheet = gc.open_by_url(SPREADSHEET_URL)
worksheet = spreadsheet.worksheet(SHEET_NAME)

# データ取得
values = worksheet.get_all_values()
header = values[0]
rows = values[1:]

# ヘッダーの列番号を取得
video_url_col = header.index(COLUMN_URL)
transcript_col = header.index(COLUMN_TRANSCRIPT)
summary_col = header.index(COLUMN_SUMMARY)

for i, row in enumerate(rows):
    video_url = row[video_url_col].strip()
    transcript = row[transcript_col].strip()
    summary = row[summary_col].strip()

    # YouTubeのVideo ID抽出
    if "v=" in video_url:
        video_id = video_url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in video_url:
        video_id = video_url.split("youtu.be/")[-1].split("?")[0]
    else:
        video_id = ""

    # 字幕取得
    if not transcript and video_id:
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["ja", "en"])
            full_text = " ".join([entry['text'] for entry in transcript_list])
        except (TranscriptsDisabled, NoTranscriptFound):
            full_text = "(文字起こしが無効または取得できませんでした)"
        worksheet.update_cell(i + 2, transcript_col + 1, full_text)

    # 要約生成
    if not summary and transcript and "取得できませんでした" not in transcript:
        prompt = f"次のYouTube動画の文字起こしを300文字以内で要約してください：\n{transcript[:4000]}"
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=300
            )
            generated_summary = response.choices[0].message.content.strip()
        except Exception as e:
            generated_summary = f"(要約エラー: {str(e)})"
        worksheet.update_cell(i + 2, summary_col + 1, generated_summary)
