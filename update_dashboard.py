"""
Thai Hospital CI Dashboard — Daily Auto-Update Script
ใช้ Google Gemini API (Free Tier) ค้นหาข่าวและอัปเดต index.html
รันผ่าน GitHub Actions ทุกวัน 08:00 น. เวลาไทย (01:00 UTC)
"""

import os
import re
import json
import requests
from datetime import datetime, timezone, timedelta

# ── ตั้งค่า ──────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent?key=" + GEMINI_API_KEY
)

# วันที่ไทย
THAI_MONTHS = [
    "มกราคม","กุมภาพันธ์","มีนาคม","เมษายน","พฤษภาคม","มิถุนายน",
    "กรกฎาคม","สิงหาคม","กันยายน","ตุลาคม","พฤศจิกายน","ธันวาคม"
]
now_utc = datetime.now(timezone.utc)
now_thai = now_utc + timedelta(hours=7)
THAI_DATE = f"{now_thai.day} {THAI_MONTHS[now_thai.month - 1]} {now_thai.year + 543}"
DATE_ISO = now_thai.strftime("%Y-%m-%d")


def call_gemini(prompt: str) -> str:
    """เรียก Gemini API พร้อม Google Search Grounding"""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search_retrieval": {}}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2048
        }
    }
    headers = {"Content-Type": "application/json"}
    resp = requests.post(GEMINI_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        return ""


def research_news() -> str:
    """ค้นหาข่าวโรงพยาบาลเอกชนไทยล่าสุด"""
    prompt = f"""วันนี้คือ {THAI_DATE}

คุณเป็น Senior Healthcare CI Analyst ด้านโรงพยาบาลเอกชนไทย

ค้นหาข่าวล่าสุด 48 ชั่วโมงที่ผ่านมา สำหรับโรงพยาบาลเหล่านี้:
BDMS, Bumrungrad International, BCH (Bangkok Chain Hospital), CHG (Chularat Hospital),
Samitivej, Phyathai, Paolo, BNH, Vibhavadi (VIBHA), Vimut (Pruksa Holding)

ค้นหาโดยครอบคลุม: การขยายสาขา, การลงทุน, เทคโนโลยี AI/Robotic, Wellness/Longevity,
Medical Tourism, ผลประกอบการ, ความร่วมมือ, รางวัล, การรับรองมาตรฐาน

สำหรับแต่ละข่าวที่พบ ให้ตอบกลับเป็น HTML block ดังนี้ (ห้ามใส่ข้อความอื่น):

<div class="alert [COLOR]">
<div class="alert-icon">[EMOJI]</div>
<div><strong>[ชื่อ รพ.]: [หัวข้อข่าวภาษาไทย]</strong> — [สรุป 1-2 ประโยคภาษาไทย ระบุข้อเท็จจริง ไม่แต่งเติม] (ที่มา: [ชื่อสำนักข่าว])</div>
</div>

กฎสี:
- red = ข่าวเชิงลบ / ผลประกอบการลดลง / วิกฤต
- gold = การลงทุน / กลยุทธ์ใหม่ / M&A
- blue = ความร่วมมือ / พันธมิตร / นวัตกรรม
- green = เปิดสาขาใหม่ / ขยายบริการ / รางวัล

กฎ emoji: 🔴=red, 💰=gold, 🤝=blue, 🏥=green

ถ้าไม่พบข่าวใหม่เลย ให้ตอบเพียง: NO_NEW_NEWS

ห้ามแต่งข่าว ห้ามใส่ข้อมูลที่ไม่แน่ใจโดยไม่ระบุแหล่งที่มา"""

    return call_gemini(prompt)


def update_html(news_html: str) -> None:
    """อ่าน index.html, อัปเดตวันที่ + ข่าวใหม่, บันทึก"""
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. อัปเดตวันที่ใน header badge
    content = re.sub(
        r'(<div class="date-badge" id="reportDate">)[^<]*(</div>)',
        rf'\g<1>{THAI_DATE}\g<2>',
        content
    )

    # 2. เพิ่มข่าวใหม่ (ถ้ามี)
    if news_html and news_html.upper() != "NO_NEW_NEWS" and '<div class="alert' in news_html:
        new_block = (
            f'\n  <!-- NEWS {DATE_ISO} -->\n'
            f'  <div style="font-size:0.8rem;font-weight:700;color:var(--muted);'
            f'text-transform:uppercase;letter-spacing:0.8px;margin:20px 0 10px;'
            f'border-left:3px solid var(--accent);padding-left:10px">'
            f'ข่าวใหม่ — {THAI_DATE}</div>\n'
            f'  {news_html.strip()}\n'
        )
        # แทรกหลัง section title "สัญญาณสำคัญประจำงวด"
        marker = '<div class="sec-title"><span class="icon">🔔</span>'
        idx = content.find(marker)
        if idx != -1:
            # หาจุดสิ้นสุดของ div นั้น
            end = content.find("</div>", idx)
            if end != -1:
                insert_at = end + 6
                content = content[:insert_at] + new_block + content[insert_at:]
                print(f"📰 เพิ่มข่าวใหม่เรียบร้อย")
    else:
        print("ℹ️  ไม่พบข่าวใหม่วันนี้ — อัปเดตเฉพาะวันที่")

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)


def main():
    print(f"🚀 เริ่ม CI Dashboard Update — {THAI_DATE}")

    if not GEMINI_API_KEY:
        raise ValueError("ไม่พบ GEMINI_API_KEY — กรุณาตั้งค่า GitHub Secret")

    print("🔍 กำลังค้นหาข่าวล่าสุด...")
    news_html = research_news()

    print("📝 กำลังอัปเดต index.html...")
    update_html(news_html)

    print(f"✅ เสร็จสิ้น — {THAI_DATE}")


if __name__ == "__main__":
    main()
