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

    # ✨ จุดที่เพิ่มใหม่: บังคับอัปเดตวันที่ของฝั่งแหล่งอ้างอิงให้เปลี่ยนตามวันปัจจุบันด้วยอัตโนมัติ
    content = re.sub(
        r'(<div class="sec-title"[^>]*>📚 แหล่งอ้างอิง \(เข้าถึง )[^)]*(\)</div>)',
        rf'\g<1>{THAI_DATE}\g<2>',
        content
    )

    # 2. ทำการแทรกชุดข้อมูล HTML ตัวใหม่ลงไปในเว็บหน้าบ้านอย่างปลอดภัย
    if news_html and "NO_NEW_NEWS" not in news_html.upper() and '<div class="alert' in news_html:
        new_block = (
            f'\n  <!-- NEWS {DATE_ISO} -->\n'
            f'  <div style="font-size:0.8rem;font-weight:700;color:var(--muted);'
            f'text-transform:uppercase;letter-spacing:0.8px;margin:20px 0 10px;'
            f'border-left:3px solid var(--accent);padding-left:10px">'
            f'ข่าวใหม่ — {THAI_DATE}</div>\n'
            f'  {news_html.strip()}\n'
        )
        
        marker = '<!-- ALERT: KEY HEADLINES -->'
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
