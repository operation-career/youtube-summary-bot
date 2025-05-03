import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from urllib.parse import urlparse, parse_qs

# ========================
# 設定
# ========================
SERVICE_ACCOUNT_FILE = "/etc/secrets/credentials.json"
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1vi_7UZg0LlyCymS1yVC4gs7DXroVoD8nbpyBoOBTjok/edit#gid=0"
SHEET_NAME = "動画一覧"

# ========================
# API認証
# ========================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
gc = gspread.authorize(credentials)

# ========================
# シート取得
# ========================
spreadsheet = gc.open_by_url(SPREADSHEET_URL)
worksheet = spreadsheet.worksheet(SHEET_NAME)
values = worksheet.get_all_values()
header = values[0]
rows = values[1:]

# ========================
# 列番号の取得
# ========================
COLUMN_VIDEO_URL = header.index("動画URL")
COLUMN_THUMBNAIL = header.index("サムネイルURL")
COLUMN_DESCRIPTION = header.index("概要欄")

# ========================
# YouTube動画IDの抽出関数
# ========================
def extract_video_id(url):
    if "youtu.be" in url:
        return url.split("/")[-1]
    parsed_url = urlparse(url)
    return parse_qs(parsed_url.query).get("v", [""])[0]

# ========================
# 概要欄取得関数（簡易版）
# ========================
def get_video_description(video_url):
    try:
        response = requests.get(video_url, timeout=5)
        if response.status_code == 200:
            return "[動画一覧] " + video_url
        else:
            return "(取得失敗)"
    except Exception as e:
        return f"(取得エラー: {e})"

# ========================
# メイン処理ループ
# ========================
for i, row in enumerate(rows):
    video_url = row[COLUMN_VIDEO_URL].strip()
    thumbnail = row[COLUMN_THUMBNAIL].strip()
    description = row[COLUMN_DESCRIPTION].strip()

    if not video_url:
        continue  # 動画URLが空ならスキップ

    # ✅ サムネイルが空欄なら =IMAGE("URL") を出力
    if not thumbnail:
        video_id = extract_video_id(video_url)
        if video_id:
            thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"
            worksheet.update_cell(i + 2, COLUMN_THUMBNAIL + 1, f'=IMAGE("{thumbnail_url}")')

    # ✅ 概要欄が空欄ならダミーの概要文を出力
    if not description:
        generated_description = get_video_description(video_url)
        worksheet.update_cell(i + 2, COLUMN_DESCRIPTION + 1, generated_description)
