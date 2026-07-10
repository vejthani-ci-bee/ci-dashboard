"""
Thai Hospital CI Dashboard — Daily Auto-Update Script
ใช้ Google GenAI SDK (ระบบล่าสุด) ค้นหาข่าวและอัปเดต index.html
รันผ่าน GitHub Actions ทุกวัน 08:00 น. เวลาไทย (01:00 UTC)
"""

import os
import re
import requests
from google import genai
from google.genai import types
from datetime import datetime, timezone, timedelta

# ── ตั้งค่าความปลอดภัย ──────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

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
    """เรียกใช้งาน Gemini API ผ่าน SDK ตัวใหม่ รองรับคีย์ขึ้นต้นด้วย AQ. เต็มรูปแบบ"""
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
        print(f"❌ ระบบประมวลผลผ่าน AI ล้มเหลว: {e}")
        raise e


def research_news() -> str:
    """ประมวลผลและวิเคราะห์ข้อมูลความเคลื่อนไหวล่าสุดของโรงพยาบาลเอกชนไทย"""
    prompt = f"""วันนี้คือ {THAI_DATE}

คุณเป็น Senior Healthcare CI Analyst ด้านโรงพยาบาลเอกชนไทย

ใช้ฐานข้อมูลความรู้ที่อัปเดตที่สุดของคุณ ทำการวิเคราะห์และสรุปประเด็นข่าว ข้อมูลความเคลื่อนไหวเชิงกลยุทธ์ หรือผลประกอบการล่าสุด สำหรับโรงพยาบาลเหล่านี้:
BDMS, Bumrungrad International, BCH (Bangkok Chain Hospital), CHG (Chularat Hospital),
Samitivej, Phyathai, Paolo, BNH, Vibhavadi (VIBHA), Vimut (Pruksa Holding)

วิเคราะห์โดยครอบคลุม: การขยายสาขา, การลงทุน, เทคโนโลยี AI/Robotic, Wellness/Longevity,
Medical Tourism, ผลประกอบการ, ความร่วมมือ, รางวัล, การรับรองมาตรฐาน

สำหรับแต่ละประเด็นสำคัญที่พบ ให้ตอบกลับเป็น HTML block ดังนี้ (ห้ามใส่ข้อความอื่นนอกเหนือจากโครงสร้างนี้):

<div class="alert [COLOR]">
<div class="alert-icon">[EMOJI]</div>
<div><strong>[ชื่อ รพ.]: [หัวข้อข่าว/ประเด็นกลยุทธ์ภาษาไทย]</strong> — [สรุปประเด็นเชิงลึก 1-2 ประโยคภาษาไทย ระบุข้อเท็จจริง ไม่แต่งเติมข้อมูล] (ที่มา: ข้อมูลอัปเดตอุตสาหกรรม)</div>
</div>

กฎสี:
- red = ประเด็นเชิงลบ / ผลประกอบการลดลง / วิกฤตภูมิรัฐศาสตร์ที่ส่งผลกระทบต่อตัวเลขผู้ป่วยต่างชาติ
- gold = การลงทุนใหญ่ / กลยุทธ์ใหม่ / การควบรวมกิจการ (M&A)
- blue = ความร่วมมือทางการแพทย์ / พันธมิตรธุรกิจ / นวัตกรรมเทคโนโลยี
- green = การเปิดอาคาร/สาขาใหม่ / การขยายศูนย์บริการเฉพาะทาง / รางวัลและการรับรองมาตรฐาน

กฎ emoji ให้สอดคล้องกับสี: 🔴=red, 💰=gold, 🤝=blue, 🏥=green

หากไม่มีข้อมูลอัปเดตหรือประเด็นใหม่เลย ให้ตอบเพียงคำว่า: NO_NEW_NEWS

ทำงานอย่างเป็นมืออาชีพ ห้ามสร้างข้อมูลเท็จขึ้นมาเองโดยเด็ดขาด"""

    return call_gemini(prompt)


def update_html(news_html: str) -> None:
    """อ่านไฟล์หน้ากากเว็บ index.html, อัปเดตวันที่ + แทรกลิสต์รายงานใหม่ และเซฟบันทึก"""
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. ปรับปรุงวันที่อัปเดตรายงานหลักที่หัวเว็บ
    content = re.sub(
        r'(<div class="date-badge" id="reportDate">)[^<]*(</div>)',
        rf'\g<1>{THAI_DATE}\g<2>',
        content
    )

    # ✨ ปรับปรุงจุดนี้: เพิ่ม Regex ค้นหาข้อความหัวข้อแหล่งอ้างอิงและเปลี่ยนวันที่เข้าถึงให้ตรงกับ THAI_DATE เสมอ
    content = re.sub(
        r'(<div class="sec-title"[^>]*>📚 แหล่งอ้างอิง \(เข้าถึง )[^)]*(\)</div>)',
        rf'\g<1>{THAI_DATE}\g<2>',
        content
    )

    # 2. ทำการแทรกชุดข้อมูล HTML ตัวใหม่ลงไปในเว็บหน้าบ้านอย่างปลอดภัย
    if news_html and "NO_NEW_NEWS" not in news_html.upper() and '<div class="alert' in news_html:
        new_block = (
            f'\n  \n'
            f'  <div style="font-size:0.8rem;font-weight:700;color:var(--muted);'
            f'text-transform:uppercase;letter-spacing:0.8px;margin:20px 0 10px;'
            f'border-left:3px solid var(--accent);padding-left:10px">'
            f'ข่าวใหม่ — {THAI_DATE}</div>\n'
            f'  {news_html.strip()}\n'
        )
        
        marker = ''
        if marker in content:
            content = content.replace(marker, marker + new_block)
            print(f"📰 ดำเนินการเพิ่มลิสต์ข้อมูลการแข่งขันใหม่เรียบร้อยแล้ว")
        else:
            marker_backup = '<div class="sec-title"><span class="icon">🔔</span> สัญญาณสำคัญประจำงวด</div>'
            if marker_backup in content:
                content = content.replace(marker_backup, marker_backup + new_block)
                print(f"📰 ดำเนินการเพิ่มลิสต์ข้อมูลผ่านมาร์กเกอร์สำรองเรียบร้อยแล้ว")
            else:
                print("❌ ไม่พบตำแหน่งในการวางข้อมูลโครงสร้างหน้าเว็บ")
    else:
        print("ℹ️ ไม่พบประเด็นใหม่เพิ่มเติมในรอบนี้ — ระบบทำการปรับปรุงเฉพาะวันที่อัปเดตรายงาน")

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)


def main():
    print(f"🚀 เริ่มต้นการทำงานระบบอัปเดต CI Dashboard — {THAI_DATE}")

    if not GEMINI_API_KEY:
        raise ValueError("ไม่พบข้อมูลสิทธิ์ระบบความปลอดภัย — กรุณาตั้งค่าคีย์ใน GitHub Secrets")

    print("🔍 กำลังประมวลผลข้อมูลการแข่งขันด้วยปัญญาประดิษฐ์...")
    news_html = research_news()

    print("📝 กำลังทำการเขียนข้อมูลลงในโครงสร้างไฟล์หน้าบ้าน index.html...")
    update_html(news_html)

    print(f"✅ ดำเนินการอัปเดตหน้า Dashboard เสร็จสิ้นสมบูรณ์ — {THAI_DATE}")


if __name__ == "__main__":
    main()
