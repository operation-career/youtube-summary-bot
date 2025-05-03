import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from urllib.parse import urlparse, parse_qs

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

# ヘッダーの列番号取得（動画URLのみ）
try:
    video_url_col = header.index("動画URL")
except ValueError:
    raise ValueError("❌ '動画URL' 列が見つかりません。スプレッドシートを確認してください。")

# 全行に対して処理（文字起こしや要約の処理は一切しない）
for i, row in enumerate(rows):
    video_url = row[video_url_col].strip()

    # 動画ID抽出
    try:
        video_id = parse_qs(urlparse(video_url).query).get("v", [""])[0]
    except Exception:
        video_id = ""

    if not video_id:
        print(f"⚠ 動画URLが不正なためスキップ（{i+2}行目）")
        continue

    # デバッグ出力：将来の処理追加ポイント
    print(f"✅ 動画ID取得成功：{video_id}（{i+2}行目）")

print("🎉 完了：動画URLの抽出だけを実施しました。")
