import os
import openai
import gspread
import re
from oauth2client.service_account import ServiceAccountCredentials
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

# ✅ OpenAI APIキーの読み込み
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Google Sheets APIの設定
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "/etc/secrets/credentials.json"
credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
gc = gspread.authorize(credentials)

# ✅ 対象のスプレッドシートを開く
spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1vi_7UZg0LlyCymS1yVC4gs7DXroVoD8nbpyBoOBTjok/edit?gid=0")
worksheet = spreadsheet.worksheet("動画一覧")

# ✅ シートの内容を取得
values = worksheet.get_all_values()
header = values[0]
rows = values[1:]

# ✅ 列番号取得（列名のミス対策としてstrip()で空白除去）
url_col = header.index("動画URL")
transcript_col = header.index("字幕/文字起こし")
summary_col = header.index("要約")

# ✅ 動画URLから動画IDを抽出する関数
def extract_video_id(url):
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

# ✅ 各行処理
for i, row in enumerate(rows):
    video_url = row[url_col].strip()
    transcript = row[transcript_col].strip()
    summary = row[summary_col].strip()

    video_id = extract_video_id(video_url)

    if not video_id:
        worksheet.update_cell(i + 2, transcript_col + 1, "(動画IDが抽出できませんでした)")
        continue

    if not transcript:
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["ja", "en"])
            full_text = " ".join([entry['text'] for entry in transcript_list])
        except (TranscriptsDisabled, NoTranscriptFound):
            full_text = "(文字起こしが無効または取得できませんでした)"

        worksheet.update_cell(i + 2, transcript_col + 1, full_text)

    if not summary and transcript and transcript != "(文字起こしが無効または取得できませんでした)":
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
