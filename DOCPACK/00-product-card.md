---
title: Book Location Intelligence (book-directory-scraping) — Product Card
doc_id: CARD-book-directory-scraping
doc_type: product-card
verdict: showcase
version: 0.1
date: 2026-10-08
status: ร่างเพื่อพิจารณา
owner: Product owner (Book Dev)
---

# Book Location Intelligence (book-directory-scraping) — Product Card

## 1. สรุปคุณค่าในหนึ่งประโยค

ช่วยคนที่กำลังเลือกทำเลเปิดธุรกิจเล็กเทียบจำนวนและประเภทร้านค้ารอบจุดหนึ่งในหลายรัศมี แล้วได้ scorecard พร้อมหลักฐานและช่องว่างข้อมูลที่ระบุชัด

## 2. ปัญหาและผู้ใช้เป้าหมาย

- ปัญหา: การเลือกทำเลร้าน (กาแฟ ซักผ้า ความงาม ฯลฯ) มักอาศัยความรู้สึก ไม่มีข้อมูลคู่แข่งรอบทำเล
- ผู้ใช้: เจ้าของธุรกิจเล็ก/ผู้ศึกษาทำเล **[ต้องยืนยัน]** ว่ามีผู้ใช้จริง

## 3. สิ่งที่ทำได้จริงตอนนี้

- โมดูล `location_intelligence`: analysis, providers, report → JSON contract + Markdown report (coverage, expiry, evidence IDs, scorecard)
- โหมด fixture (`fixtures/bangkapi_sample.json`) และโหมด live Google Places (New) แบบ opt-in พร้อม `--max-requests` (ค่าเริ่ม 25), retry จำกัด, ไม่ log key
- ชื่อ repo เป็น "directory scraping" แต่โค้ดจริงคือ location analysis — ไม่มี Yellow Pages scraper

## 4. หลักฐานสถานะ

| รายการ | ค่า (ตรวจจาก repository) |
|---|---|
| Stack | Python |
| Commits | 16 (แรก 2026-07-09 → ล่าสุด 2026-10-01) |
| Source | 12 ไฟล์ / 1,574 บรรทัด |
| Tests | 5 ไฟล์ |
| CI | 1 workflow |
| Deploy config | ไม่มี |
| Live URL | ไม่มี |
| README | 103 บรรทัด (`book-directory-scraping`) |
| โครงสร้างซ้ำ (template family) | 1 repo ที่มี structure signature เดียวกัน |

## 5. คุณค่าและจุดต่าง

- จุดต่าง: บอกตรง ๆ ว่า score ไม่ใช่ยอดขายพยากรณ์ และเก็บ demand evidence ที่ขาดไว้ชัด
- มุมรายได้: รายงานทำเลแบบจ่ายต่อครั้งสำหรับ SME ไทย **[สมมติฐาน]**

## 6. ช่องว่างสำคัญ

- ไม่มี demand data (ประชากร, traffic) จึงยังตอบได้แค่ฝั่ง supply
- โหมด live มีค่าใช้จ่าย Google Places ต่อ request
- ไม่มี UI ให้ผู้ใช้ที่ไม่ใช่นักพัฒนา

## 7. คำตัดสิน

**`showcase`** — โค้ดสะอาดและแนวคิดมีประโยชน์ แต่ยังไม่ครบเป็นผลิตภัณฑ์ (ขาด demand) จะเป็น `invest` ถ้าทำรายงานทำเลให้ผู้ใช้จริง 3 รายแล้วมีคนยอมจ่าย

## 8. ขั้นต่อไป

1. เปลี่ยนชื่อ/README ให้ตรงกับสิ่งที่ทำ (location intelligence)
2. ทดลองทำรายงานหนึ่งทำเลจริงกับธุรกิจที่รู้จักแล้วเก็บ feedback

## การอนุมัติ

| บทบาท | สถานะ | วันที่ | ลงนาม |
|---|---|---|---|
| Product owner (Book Dev) | รอพิจารณา | — | ________ |

## แหล่งข้อมูล

- `README.md`
- `PRODUCT.md`
- `location_intelligence/analysis.py`
- `location_intelligence/providers.py`
- `scripts/run_location_analysis.py`
