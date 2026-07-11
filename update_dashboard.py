"""
Thai Hospital CI Dashboard — Daily Auto-Update Script
ระบบเสถียรความปลอดภัยสูง รองรับ Google Search Grounding ค้นหาข้อมูลล่าสุดรายวัน
"""

import os
import re
import json
import requests
from datetime import datetime, timezone, timedelta

# ── ตั้งค่าสิทธิ์ความปลอดภัยและการเชื่อมต่อ ──────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent?key=" + GEMINI_API_KEY
)

THAI_MONTHS = [
    "มกราคม","กุมภาพันธ์","มีนาคม","เมษายน","พฤษภาคม","มิถุนายน",
    "กรกฎาคม","สิงหาคม","กันยายน","ตุลาคม","พฤศจิกายน","ธันวาคม"
]
now_utc = datetime.now(timezone.utc)
now_thai = now_utc + timedelta(hours=7)
THAI_DATE = f"{now_thai.day} {THAI_MONTHS[now_thai.month - 1]} {now_thai.year + 543}"
DATE_ISO = now_thai.strftime("%Y-%m-%d")


def call_gemini_with_search(prompt: str) -> str:
    """เรียกใช้งาน Gemini API พร้อมเปิดใช้งาน Google Search สำหรับค้นหาข่าวสารปัจจุบัน"""
    if not GEMINI_API_KEY:
        print("⚠️ ไม่พบคีย์ระบบความปลอดภัย ปรับปรุงเฉพาะส่วนโครงสร้างวันที่")
        return "NO_NEW_NEWS"
        
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"googleSearch": {}}],  # เปิดการค้นหาข้อมูลจริงบน Google
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2048
        }
    }
    
    try:
        response = requests.post(GEMINI_URL, json=payload, timeout=45)
        res_json = response.json()
        return res_json['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        print(f"⚠️ การเรียกรับข้อมูลผ่าน AI ขัดข้อง: {e}")
        return "NO_NEW_NEWS"


def research_news() -> str:
    prompt = f"""วันนี้คือวันที่ {THAI_DATE}
คุณเป็น Senior Healthcare CI Analyst ด้านโรงพยาบาลเอกชนไทย

จงค้นหาข่าวสาร ความเคลื่อนไหวเชิงกลยุทธ์ ข้อมูลการลงทุน หรือรายงานผลประกอบการล่าสุดในตลาดไทยของกลุ่มโรงพยาบาลต่อไปนี้:
BDMS, Bumrungrad (BH), BCH (Bangkok Chain Hospital), CHG (Chularat Hospital), Vibhavadi (VIBHA), Vimut

สรุปประเด็นข่าวที่น่าสนใจและสำคัญที่สุดที่พบออกมาเป็น HTML block ตามรูปแบบด้านล่างนี้ต่อกัน (ห้ามมีคำเกริ่นนำ หรือข้อความ markdown อื่นใด ให้ส่งเฉพาะแท็ก div ออกมาเท่านั้น):

<div class="alert gold">
<div class="alert-icon">💰</div>
<div><strong>[ชื่อ รพ.]: [หัวข้อข่าวภาษาไทย]</strong> — [เนื้อหาข่าวสารเชิงลึกและข้อเท็จจริงสั้น ๆ 1-2 ประโยค] (ที่มา: ข้อมูลล่าสุดประจำงวด)</div>
</div>

หากไม่มีข่าวสารใหม่ที่สำคัญเลยจริง ๆ ให้ตอบคำว่า: NO_NEW_NEWS"""
    return call_gemini_with_search(prompt)


def update_html(news_html: str) -> None:
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()

    # ตัวล็อกนิรภัย (Safe Guard) — ถ้าไฟล์โครงสร้างพังหรือว่างเปล่า จะไม่บันทึกทับเด็ดขาด
    if not content or "</html>" not in content:
        print("❌ ข้อผิดพลาด: โครงสร้างไฟล์ index.html ไม่สมบูรณ์ ระบบยกเลิกการเขียนทับเพื่อความปลอดภัย")
        return

    # 1. ปรับปรุงวันที่อัปเดตบนหัวเว็บหลัก
    content = re.sub(
        r'(<div class="date-badge" id="reportDate">)[^<]*(</div>)',
        rf'\g<1>{THAI_DATE}\g<2>',
        content
    )

    # 2. ปรับปรุงวันที่เข้าถึงของส่วนแหล่งอ้างอิงผ่าน ID
    content = re.sub(
        r'(<div class="sec-title" id="referenceSection">📚 แหล่งอ้างอิง \(เข้าถึง )[^)]*(\)</div>)',
        rf'\g<1>{THAI_DATE}\g<2>',
        content
    )

    # 3. แทรกบล็อกข่าวสารประจำวันลงตำแหน่งมาร์กเกอร์
    if news_html and "NO_NEW_NEWS" not in news_html.upper() and '<div class="alert' in news_html:
        # ตัดคำแปลกปลอมที่ AI อาจแถมมาออกเพื่อความชัวร์
        clean_html = news_html.replace("```html", "").replace("```", "").strip()
        
        new_block = (
            f'\n  \n'
            f'  <div style="font-size:0.85rem;font-weight:700;color:var(--muted);margin:20px 0 10px;border-left:3px solid var(--accent);padding-left:10px">'
            f'📰 ข่าวสารอัปเดตประจำวัน — {THAI_DATE}</div>\n'
            f'  {clean_html}\n'
        )
        
        marker = ''
        if marker in content:
            content = content.replace(marker, marker + new_block)
            print("📰 เพิ่มสรุปข้อมูลข่าวประจำวันลงหน้าเว็บสำเร็จ")
        else:
            print("⚠️ ไม่พบตำแหน่งตัววางข่าวสารข้อมูลหลัก (Marker)")
    else:
        print("ℹ️ วันนี้ไม่มีข่าวสารเพิ่มเติมพิเศษ — ปรับปรุงเฉพาะส่วนของวันที่เรียบร้อย")

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)


def main():
    print(f"🚀 เริ่มกระบวนการตรวจสอบข้อมูลอัตโนมัติ — {THAI_DATE}")
    news_html = research_news()
    update_html(news_html)
    print("✅ การจัดระเบียบโครงสร้างข้อมูลเสร็จสิ้นเรียบร้อย")


if __name__ == "__main__":
    main()
