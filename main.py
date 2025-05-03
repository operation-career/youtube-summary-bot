import os
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

# ✅ OpenAI APIキーの読み込み（Renderの環境変数から）
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Google Sheets APIの設定（RenderのSecret File経由）
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "/etc/secrets/credentials.json"
credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
gc = gspread.authorize(credentials)

# ✅ 対象のスプレッドシートを開く（open_by_keyを使用）
spreadsheet_id = "1vi_7UZg0LlyCymS1yVC4gs7DXroVoD8nbpyBoOBTjok"
spreadsheet = gc.open_by_key(spreadsheet_id)
worksheet = spreadsheet.worksheet("リスト")

# ✅ シートの内容を取得
values = worksheet.get_all_values()
header = values[0]
rows = values[1:]

# ✅ 見出しに「動画ID」「文字起こし」「要約」がある前提で列番号取得
video_id_col = header.index("動画ID")
transcript_col = header.index("文字起こし")
summary_col = header.index("要約")

# ✅ 各行に対して処理
for i, row in enumerate(rows):
    video_id = row[video_id_col].strip()
    transcript = row[transcript_col].strip()
    summary = row[summary_col].strip()

    # 文字起こし未取得の行
    if not transcript:
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["ja", "en"])
            full_text = " ".join([entry['text'] for entry in transcript_list])
        except (TranscriptsDisabled, NoTranscriptFound):
            full_text = "(文字起こしが無効または取得できませんでした)"
        worksheet.update_cell(i + 2, transcript_col + 1, full_text)

    # 要約未取得の行
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
