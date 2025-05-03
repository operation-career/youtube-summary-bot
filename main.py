import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

# Google Sheets API設定
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "/etc/secrets/credentials.json"
credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
gc = gspread.authorize(credentials)

# スプレッドシートとワークシートを開く
spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1vi_7UZg0LlyCymS1yVC4gs7DXroVoD8nbpyBoOBTjok/edit?usp=sharing")
worksheet = spreadsheet.worksheet("動画一覧")

# 全行取得
values = worksheet.get_all_values()
header = values[0]
rows = values[1:]

# ヘッダーの列番号取得
try:
    video_url_col = header.index("動画URL")
    summary_col = header.index("要約")  # 無視する列（削除可）
    transcript_col = header.index("字幕/文字起こし")  # 無視する列（削除可）
except ValueError:
    # 列が存在しない場合でも無視して進む
    video_url_col = -1
    summary_col = -1
    transcript_col = -1

# 全行に対して処理（ただし要約や文字起こしはしない）
for i, row in enumerate(rows):
    video_url = row[video_url_col] if video_url_col != -1 else ""

    # 動画ID抽出
    try:
        video_id = parse_qs(urlparse(video_url).query).get("v", [""])[0]
    except Exception:
        video_id = ""

    if not video_id:
        continue  # video_idが取得できなければスキップ

    # 今後の用途：ここに別処理を書く（例：動画タイトル取得など）
    print(f"動画ID取得成功：{video_id}（行 {i + 2}）")

print("✅ 実行完了（要約と文字起こしは無視）")
