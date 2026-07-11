import os
import re
import requests
from datetime import datetime, timezone, timedelta

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

THAI_MONTHS = ["มกราคม","กุมภาพันธ์","มีนาคม","เมษายน","พฤษภาคม","มิถุนายน","กรกฎาคม","สิงหาคม","กันยายน","ตุลาคม","พฤศจิกายน","ธันวาคม"]
now_thai = datetime.now(timezone.utc) + timedelta(hours=7)
THAI_DATE = f"{now_thai.day} {THAI_MONTHS[now_thai.month - 1]} {now_thai.year + 543}"

def get_news():
    if not GEMINI_API_KEY: 
        return "NO_NEW_NEWS"
    prompt = f"""วันนี้คือวันที่ {THAI_DATE} จงสรุปข่าวเด่นหรือความเคลื่อนไหวเชิงกลยุทธ์ล่าสุดของโรงพยาบาลเอกชนไทย (BDMS, BH, BCH, CHG) มา 1 ข่าวเด่น
โดยให้ผลลัพธ์ตอบกลับมาเป็นบล็อก HTML โครงสร้างตามนี้เป๊ะๆ เท่านั้น (ห้ามมีคำนำ ห้ามมี markdown บรรทัดเดียวจบ):
<div class="alert gold"><div><strong>[ชื่อ รพ.]: [หัวข้อข่าว]</strong> — [รายละเอียดเนื้อหาข่าวภาษาไทยสั้นๆ 1 ประโยค]</div></div>
หากไม่มีข่าวใหม่ที่สำคัญเลย ให้ตอบกลับสั้นๆ ว่า: NO_NEW_NEWS"""
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"googleSearch": {}}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024}
    }
    try:
        res = requests.post(GEMINI_URL, json=payload, timeout=35).json()
        return res['candidates'][0]['content']['parts'][0]['text'].strip()
    except: 
        return "NO_NEW_NEWS"

def main():
    with open("index.html", "r", encoding="utf-8") as f: 
        content = f.read()
        
    # ป้องกันไฟล์ว่างหรือพัง (Safe Guard)
    if not content or "</html>" not in content:
        print("❌ โครงสร้างไฟล์ไม่สมบูรณ์ ยกเลิกการบันทึก")
        return
    
    # อัปเดตวันที่ทั้ง 2 จุดหลัก
    content = re.sub(r'(<div class="date-badge" id="reportDate">)[^<]*(</div>)', rf'\g<1>{THAI_DATE}\g<2>', content)
    content = re.sub(r'(<div class="sec-title" id="referenceSection">📚 แหล่งอ้างอิง \(เข้าถึง )[^)]*(\)</div>)', rf'\g<1>{THAI_DATE}\g<2>', content)
    
    news = get_news()
    if news and "NO_NEW_NEWS" not in news and "<div" in news:
        clean_news = news.replace("```html", "").replace("```", "").strip()
        # ทำการแทรกข่าวสารใหม่ไว้ใต้ตัวมาร์กเกอร์โดยตรง
        marker = ""
        if marker in content:
            content = content.replace(marker, f"{marker}\n    {clean_news}")
            print("📰 เพิ่มข่าวอัปเดตเรียบร้อย")
            
    with open("index.html", "w", encoding="utf-8") as f: 
        f.write(content)
    print("✅ ระบบอัปเดตวันที่และโครงสร้างเสร็จสมบูรณ์")

if __name__ == "__main__": 
    main()
