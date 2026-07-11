"""
Thai Hospital CI Dashboard — Daily Auto-Update Script
แก้ไขระบบค้นหาตำแหน่ง Marker และอัปเดตวันที่ทั้งสองจุดให้สอดคล้องกันอย่างถาวร
"""

import os
import re
import requests
from google import genai
from google.genai import types
from datetime import datetime, timezone, timedelta

# ── ตั้งค่าสิทธิ์ความปลอดภัย ──────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

THAI_MONTHS = [
    "มกราคม","กุมภาพันธ์","มีนาคม","เมษายน","พฤษภาคม","มิถุนายน",
    "กรกฎาคม","สิงหาคม","กันยายน","ตุลาคม","พฤศจิกายน","ธันวาคม"
]
now_utc = datetime.now(timezone.utc)
now_thai = now_utc + timedelta(hours=7)
THAI_DATE = f"{now_thai.day} {THAI_MONTHS[now_thai.month - 1]} {now_thai.year + 543}"
DATE_ISO = now_thai.strftime("%Y-%m-%d")


def call_gemini(prompt: str) -> str:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=2048
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        raise e


def research_news() -> str:
    prompt = f"""วันนี้คือ {THAI_DATE}
คุณเป็น Senior Healthcare CI Analyst สรุปความเคลื่อนไหวของโรงพยาบาลเอกชนไทย (BDMS, BH, BCH, CHG, Vimut) 
ให้ข้อมูลความรู้ของคุณสรุปข่าวหรือแนวโน้มการแข่งขันเด่นๆ 1 ประเด็นเป็น HTML block ดังนี้เท่านั้น:

<div class="alert gold">
<div><strong>[ชื่อ รพ.]: [หัวข้อข่าว]</strong> — [เนื้อหาภาษาไทยเชิงลึกสั้นๆ 1 ประเด็น]</div>
</div>

หากไม่มีข่าวใหญ่เป็นพิเศษในวันนี้ ให้ตอบคำว่า: NO_NEW_NEWS"""
    return call_gemini(prompt)


def update_html(news_html: str) -> None:
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. อัปเดตวันที่ badge หลักหัวเว็บ
    content = re.sub(
        r'(<div class="date-badge" id="reportDate">)[^<]*(</div>)',
        rf'\g<1>{THAI_DATE}\g<2>',
        content
    )

    # 2. อัปเดตวันที่ตรงส่วนแหล่งอ้างอิงให้เปลี่ยนอัตโนมัติตามกัน
    content = re.sub(
        r'(<div class="sec-title">📚 แหล่งอ้างอิง \(เข้าถึง )[^)]*(\)</div>)',
        rf'\g<1>{THAI_DATE}\g<2>',
        content
    )

    # 3. แทรกข่าวสารประจำวันลงใต้ Marker อย่างปลอดภัย
    if news_html and "NO_NEW_NEWS" not in news_html.upper() and '<div class="alert' in news_html:
        new_block = (
            f'\n  \n'
            f'  <div style="font-size:0.8rem;font-weight:700;color:var(--muted);'
            f'margin:20px 0 10px;border-left:3px solid var(--accent);padding-left:10px">'
            f'อัปเดตประจำวัน — {THAI_DATE}</div>\n'
            f'  {news_html.strip()}\n'
        )
        
        marker = ''
        if marker in content:
            content = content.replace(marker, marker + new_block)
            print("📰 แทรกข้อมูลข่าวสารชิ้นใหม่เรียบร้อยแล้ว")
        else:
            print("❌ ไม่พบตำแหน่ง Marker ในไฟล์หน้ากากเว็บ")
    else:
        print("ℹ️ ปรับปรุงเฉพาะส่วนของวันที่เรียบร้อย (วันนี้ไม่มีประเด็นเร่งด่วนเพิ่มเติม)")

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)


def main():
    if not GEMINI_API_KEY:
        raise ValueError("API Key missing")
    news_html = research_news()
    update_html(news_html)
    print("✅ ระบบอัปเดตข้อมูลเสร็จสิ้นเรียบร้อยแล้ว")


if __name__ == "__main__":
    main()
