"""
Thai Hospital CI Dashboard — Daily Auto-Update Script
ระบบป้องกันไฟล์เสียหาย (Safe Guard) และรองรับการอัปเดตวันที่ควบคู่แบบถาวร
"""

import os
import re
import json
import requests
from datetime import datetime, timezone, timedelta

# ── ตั้งค่าเชื่อมต่อระบบ ──────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent?key=" + GEMINI_API_KEY
)

THAI_MONTHS = [
    "มกราคม","กุมภาพันธ์","มีนาคม","เมษายน","พฤษภาคม","มิถุนายน",
    "กรกฎาคม","สิงหาคม","กันยายน","ตุลาคม","พฤศจิกายน","ดึกราคม"
]
now_utc = datetime.now(timezone.utc)
now_thai = now_utc + timedelta(hours=7)
THAI_DATE = f"{now_thai.day} {THAI_MONTHS[now_thai.month - 1]} {now_thai.year + 543}"
DATE_ISO = now_thai.strftime("%Y-%m-%d")


def call_gemini(prompt: str) -> str:
    """เรียกใช้งานผ่าน REST API ดั้งเดิม ป้องกันปัญหาระบบเวอร์ชันไลบรารีไม่ตรงกัน"""
    if not GEMINI_API_KEY:
        print("⚠️ ไม่พบคีย์ระบบความปลอดภัย ปรับปรุงเฉพาะส่วนโครงสร้างวันที่")
        return "NO_NEW_NEWS"
        
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1024}
    }
    try:
        response = requests.post(GEMINI_URL, json=payload, timeout=30)
        res_json = response.json()
        return res_json['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        print(f"⚠️ การเรียกรับข้อมูลขัดข้อง: {e}")
        return "NO_NEW_NEWS"


def research_news() -> str:
    prompt = f"""วันนี้คือ {THAI_DATE} สรุปความเคลื่อนไหวของโรงพยาบาลเอกชนไทย (BDMS, BH, BCH) มา 1 ข่าวเด่น เป็น HTML รูปแบบนี้เท่านั้น:
<div class="alert gold"><div><strong>[ชื่อ รพ.]: [หัวข้อ]</strong> — [เนื้อหาภาษาไทย 1 ประโยค]</div></div>
หากไม่มีข่าวใหม่ ให้ตอบสั้นๆ: NO_NEW_NEWS"""
    return call_gemini(prompt)


def update_html(news_html: str) -> None:
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()

    # ตรวจสอบโครงสร้างพื้นฐาน (Safe Guard) — ถ้าไฟล์ว่างหรือโดนลบ สคริปต์จะไม่ทำงานต่อเพื่อความปลอดภัย
    if not content or "</html>" not in content:
        print("❌ ข้อผิดพลาด: โครงสร้างไฟล์ index.html ไม่สมบูรณ์ ระบบยกเลิกการเขียนทับเพื่อความปลอดภัย")
        return

    # 1. ปรับปรุงวันที่หัวเว็บหลัก
    content = re.sub(
        r'(<div class="date-badge" id="reportDate">)[^<]*(</div>)',
        rf'\g<1>{THAI_DATE}\g<2>',
        content
    )

    # 2. ปรับปรุงวันที่เข้าถึงของส่วนแหล่งอ้างอิงผ่าน ID เจาะจง
    content = re.sub(
        r'(<div class="sec-title" id="referenceSection">📚 แหล่งอ้างอิง \(เข้าถึง )[^)]*(\)</div>)',
        rf'\g<1>{THAI_DATE}\g<2>',
        content
    )

    # 3. แทรกข่าวสารลงตำแหน่งมาร์กเกอร์
    if news_html and "NO_NEW_NEWS" not in news_html.upper() and '<div class="alert' in news_html:
        new_block = (
            f'\n  \n'
            f'  <div style="font-size:0.8rem;font-weight:700;color:var(--muted);margin:20px 0 10px;border-left:3px solid var(--accent);padding-left:10px">'
            f'ข่าวใหม่ประจำวัน — {THAI_DATE}</div>\n'
            f'  {news_html.strip()}\n'
        )
        
        marker = ''
        if marker in content:
            content = content.replace(marker, marker + new_block)
            print("📰 เพิ่มสรุปข้อมูลข่าวประจำวันสำเร็จ")
        else:
            print("⚠️ ไม่พบตำแหน่งตัววางข่าวสารข้อมูลหลัก")

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)


def main():
    print(f"🚀 เริ่มกระบวนการตรวจสอบข้อมูล — {THAI_DATE}")
    news_html = research_news()
    update_html(news_html)
    print("✅ การจัดระเบียบโครงสร้างข้อมูลเสร็จสิ้นเรียบร้อย")


if __name__ == "__main__":
    main()
