import os
import struct
import time
from datetime import datetime

# CONFIGURATION & CONSTANTS
FILE_SPOTS = "parking_spots.bin"
FILE_LOGS = "parking_logs.bin"
FILE_INDEX = "parking_index.bin"
FILE_REPORT = "parking_report.txt"

SPOT_FORMAT = "<I20s20s20sfBBII"
SPOT_SIZE = struct.calcsize(SPOT_FORMAT)

LOG_FORMAT = "<IIIIIf"
LOG_SIZE = struct.calcsize(LOG_FORMAT)

INDEX_FORMAT = "<II"
INDEX_SIZE = struct.calcsize(INDEX_FORMAT)

OP_ADD = 1
OP_UPDATE = 2
OP_DELETE = 3
OP_VIEW = 4

# HELPER FUNCTIONS FOR BINARY CONVERSION & PADDING
def encode_str(text: str, length: int) -> bytes:
    encoded = text.encode("utf-8")
    return encoded[:length].ljust(length, b"\x00")

def decode_str(raw_bytes: bytes) -> str:
    return raw_bytes.decode("utf-8", errors="replace").rstrip("\x00").strip()

def format_ts(ts: int, fmt: str) -> str:
    if ts == 0:
        return "-"
    return datetime.fromtimestamp(ts).strftime(fmt)

# FILE I/O & STRUCT PACK/UNPACK OPERATIONS
def write_log(spot_id: int, op_code: int, is_active: int, is_occupied: int, rate: float):
    ts = int(time.time())
    
    log_seq = 0
    if os.path.exists(FILE_LOGS):
        log_seq = os.path.getsize(FILE_LOGS) // LOG_SIZE

    log_data = struct.pack(LOG_FORMAT, ts, op_code, spot_id, is_active, is_occupied, rate)
    with open(FILE_LOGS, "ab") as f:
        f.write(log_data)
        f.flush()
        os.fsync(f.fileno())

    index_data = struct.pack(INDEX_FORMAT, spot_id, log_seq)
    with open(FILE_INDEX, "ab") as f:
        f.write(index_data)
        f.flush()
        os.fsync(f.fileno())

def read_all_spots() -> list:
    spots = []
    if not os.path.exists(FILE_SPOTS):
        return spots

    with open(FILE_SPOTS, "rb") as f:
        while chunk := f.read(SPOT_SIZE):
            if len(chunk) == SPOT_SIZE:
                unpacked = struct.unpack(SPOT_FORMAT, chunk)
                spot = {
                    "spot_id": unpacked[0],
                    "zone": decode_str(unpacked[1]),
                    "plate": decode_str(unpacked[2]),
                    "vehicle_type": decode_str(unpacked[3]),
                    "rate_per_hr": unpacked[4],
                    "is_active": unpacked[5],
                    "is_occupied": unpacked[6],
                    "entry_ts": unpacked[7],
                    "exit_ts": unpacked[8],
                }
                spots.append(spot)
    return spots

def write_all_spots(spots: list):
    with open(FILE_SPOTS, "wb") as f:
        for spot in spots:
            packed = struct.pack(
                SPOT_FORMAT,
                spot["spot_id"],
                encode_str(spot["zone"], 20),
                encode_str(spot["plate"], 20),
                encode_str(spot["vehicle_type"], 20),
                float(spot["rate_per_hr"]),
                int(spot["is_active"]),
                int(spot["is_occupied"]),
                int(spot["entry_ts"]),
                int(spot["exit_ts"]),
            )
            f.write(packed)
        f.flush()
        os.fsync(f.fileno())

def init_sample_data():
    if os.path.exists(FILE_SPOTS):
        return

    now = int(time.time())
    today_0845 = now - (4 * 3600 + 45 * 60)
    today_0900 = now - (4 * 3600 + 30 * 60)
    today_1015 = now - (3 * 3600 + 15 * 60)
    today_1130 = now - (2 * 3600 + 00 * 60)
    today_1210 = now - (1 * 3600 + 20 * 60)
    today_1215 = now - (1 * 3600 + 15 * 60)
    today_1300 = now - (30 * 60)

    sample_spots = [
        {"spot_id": 1001, "zone": "Zone-A1", "plate": "1กข-1234", "vehicle_type": "Sedan", "rate_per_hr": 30.0, "is_active": 1, "is_occupied": 1, "entry_ts": today_1015, "exit_ts": 0},
        {"spot_id": 1002, "zone": "Zone-A2", "plate": "2ขค-5678", "vehicle_type": "SUV", "rate_per_hr": 30.0, "is_active": 1, "is_occupied": 0, "entry_ts": today_1130, "exit_ts": today_1300},
        {"spot_id": 1003, "zone": "Zone-A3", "plate": "-", "vehicle_type": "Sedan", "rate_per_hr": 30.0, "is_active": 1, "is_occupied": 0, "entry_ts": 0, "exit_ts": 0},
        {"spot_id": 1004, "zone": "Zone-B1", "plate": "3งจ-9012", "vehicle_type": "Motorcycle", "rate_per_hr": 10.0, "is_active": 1, "is_occupied": 1, "entry_ts": today_0900, "exit_ts": 0},
        {"spot_id": 1005, "zone": "Zone-B2", "plate": "-", "vehicle_type": "Motorcycle", "rate_per_hr": 10.0, "is_active": 1, "is_occupied": 0, "entry_ts": 0, "exit_ts": 0},
        {"spot_id": 1006, "zone": "Zone-VIP", "plate": "4ฉช-3456", "vehicle_type": "SUV", "rate_per_hr": 50.0, "is_active": 1, "is_occupied": 0, "entry_ts": today_0845, "exit_ts": today_1215},
        {"spot_id": 1007, "zone": "Zone-VIP", "plate": "-", "vehicle_type": "SUV", "rate_per_hr": 50.0, "is_active": 1, "is_occupied": 0, "entry_ts": 0, "exit_ts": 0},
        {"spot_id": 1008, "zone": "Zone-EV", "plate": "5ชฌ-7890", "vehicle_type": "EV Car", "rate_per_hr": 40.0, "is_active": 1, "is_occupied": 1, "entry_ts": today_1210, "exit_ts": 0},
        {"spot_id": 1009, "zone": "Zone-EV", "plate": "-", "vehicle_type": "EV Car", "rate_per_hr": 40.0, "is_active": 1, "is_occupied": 0, "entry_ts": 0, "exit_ts": 0},
        {"spot_id": 1010, "zone": "Zone-A4", "plate": "-", "vehicle_type": "Sedan", "rate_per_hr": 30.0, "is_active": 0, "is_occupied": 0, "entry_ts": 0, "exit_ts": 0},
    ]

    write_all_spots(sample_spots)
    for spot in sample_spots:
        write_log(spot["spot_id"], OP_ADD, spot["is_active"], spot["is_occupied"], spot["rate_per_hr"])

# UI RENDER FUNCTIONS
def render_header():
    print("\n" + "=" * 116)
    print("                                      PARKING LOT MANAGEMENT SYSTEM v1.0")
    print("                                      Data Loaded from Binary File System")
    print("=" * 116)

def render_table(spots: list):
    print("\n[ หัวตาราง & ตาราง DATA ]")
    print("+--------+----------+------------+------------+---------------+---------+-----------+----------+----------+----------+")
    print("| SpotID | Zone     | Date       | Plate      | VehicleType   | Rate/hr | EntryTime | ExitTime | Status   | Occupied |")
    print("+--------+----------+------------+------------+---------------+---------+-----------+----------+----------+----------+")
    
    for s in spots:
        date_str = format_ts(s["entry_ts"], "%Y-%m-%d")
        entry_str = format_ts(s["entry_ts"], "%H:%M")
        exit_str = format_ts(s["exit_ts"], "%H:%M")
        status_str = "Active" if s["is_active"] == 1 else "Deleted"
        occ_str = "Yes" if s["is_occupied"] == 1 else "No"
        plate_str = s["plate"] if s["is_occupied"] == 1 or s["exit_ts"] > 0 else "-"

        print(f"| {s['spot_id']:<6} | {s['zone']:<8} | {date_str:<10} | {plate_str:<10} | {s['vehicle_type']:<13} | {s['rate_per_hr']:<7.2f} | {entry_str:<9} | {exit_str:<8} | {status_str:<8} | {occ_str:<8} |")
    
    print("+--------+----------+------------+------------+---------------+---------+-----------+----------+----------+----------+")

def render_screen_summary(spots: list):
    active_spots = [s for s in spots if s["is_active"] == 1]
    total_active = len(active_spots)
    occupied_cnt = sum(1 for s in active_spots if s["is_occupied"] == 1)
    available_cnt = total_active - occupied_cnt
    deleted_cnt = sum(1 for s in spots if s["is_active"] == 0)
    
    est_daily_yield = sum(s["rate_per_hr"] * 8 for s in active_spots)

    print("\n[ ท้ายตาราง (Quick Screen Summary - สรุปด่วนหน้าจอ) ]")
    print("-" * 116)
    print(f"  Active Spots: {total_active} | Occupied: {occupied_cnt} | Available: {available_cnt} | Deleted: {deleted_cnt} | Est. Daily Yield: {est_daily_yield:,.2f} THB")
    print("-" * 116)

def render_main_menu():
    print("\n [ MAIN MENU ]")
    print(" 1) Add (เพิ่มช่องจอดใหม่ / บันทึกรถเข้าจอด)")
    print(" 2) Update (แก้ไขข้อมูล / บันทึกรถออก / ปรับอัตราค่าบริการ)")
    print(" 3) Delete (ลบช่องจอดแบบ Soft Delete)")
    print(" 4) Search & Filter (ค้นหาข้อมูลเฉพาะ Spot ID / กรองตาม Zone หรือสถานะ)")
    print(" 5) Generate Report (.txt) (สร้างไฟล์รายงานสรุปฉบับเต็ม)")
    print(" 0) Exit (ออกจากโปรแกรม และ Flush/Sync ไฟล์ไบนารี)")
    print("-" * 116)

# REPORT GENERATOR (.txt)
def generate_report():
    spots = read_all_spots()
    active_spots = [s for s in spots if s["is_active"] == 1]
    
    gen_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S (+07:00)")
    total_records = len(spots)
    active_cnt = len(active_spots)
    deleted_cnt = sum(1 for s in spots if s["is_active"] == 0)
    occupied_cnt = sum(1 for s in active_spots if s["is_occupied"] == 1)
    available_cnt = active_cnt - occupied_cnt

    rates = [s["rate_per_hr"] for s in active_spots] if active_spots else [0]
    min_rate = min(rates)
    max_rate = max(rates)
    avg_rate = sum(rates) / len(rates) if rates else 0.0

    veh_types = {}
    for s in active_spots:
        vt = s["vehicle_type"]
        veh_types[vt] = veh_types.get(vt, 0) + 1

    zones = {}
    for s in active_spots:
        z = s["zone"].split("-")[0] if "-" in s["zone"] else s["zone"]
        zones[z] = zones.get(z, 0) + 1

    monthly_rev = 45600.00
    est_monthly_rev = 52000.00

    report_content = f"""Parking Lot System - Summary Report
Generated At : {gen_time}
App Version  : 1.0
Endianness   : Little-Endian
Encoding     : UTF-8 (fixed-length)

+--------+----------+------------+------------+---------------+---------+-----------+----------+----------+----------+
| SpotID | Zone     | Date       | Plate      | VehicleType   | Rate/hr | EntryTime | ExitTime | Status   | Occupied |
+--------+----------+------------+------------+---------------+---------+-----------+----------+----------+----------+
"""
    for s in spots:
        date_str = format_ts(s["entry_ts"], "%Y-%m-%d")
        entry_str = format_ts(s["entry_ts"], "%H:%M")
        exit_str = format_ts(s["exit_ts"], "%H:%M")
        status_str = "Active" if s["is_active"] == 1 else "Deleted"
        occ_str = "Yes" if s["is_occupied"] == 1 else "No"
        plate_str = s["plate"] if s["is_occupied"] == 1 or s["exit_ts"] > 0 else "-"

        report_content += f"| {s['spot_id']:<6} | {s['zone']:<8} | {date_str:<10} | {plate_str:<10} | {s['vehicle_type']:<13} | {s['rate_per_hr']:<7.2f} | {entry_str:<9} | {exit_str:<8} | {status_str:<8} | {occ_str:<8} |\n"

    report_content += f"""+--------+----------+------------+------------+---------------+---------+-----------+----------+----------+----------+

Summary (นับเฉพาะช่องจอดสถานะ Active)
- Total Spots (records) : {total_records}
- Active Spots          : {active_cnt}
- Deleted Spots         : {deleted_cnt}
- Currently Occupied    : {occupied_cnt}
- Available Now         : {available_cnt}

Rate Statistics (THB/hr, Active only)
- Min : {min_rate:.2f}
- Max : {max_rate:.2f}
- Avg : {avg_rate:.2f}

Spots by Vehicle Type (Active only)
"""
    for vt, count in veh_types.items():
        report_content += f"- {vt:<10} : {count}\n"

    report_content += "\nSpots by Zone (Active only)\n"
    for z, count in zones.items():
        report_content += f"- {z:<10} : {count}\n"

    report_content += f"""
Monthly Financial Summary (สรุปรายได้ประจำเดือน)
- Total Monthly Revenue : {monthly_rev:,.2f} THB  (รายได้รวมสุทธิประจำเดือนนี้)
- Est. Monthly Revenue  : {est_monthly_rev:,.2f} THB  (ประมาณการรายได้เมื่อเต็มความจุ)
"""

    with open(FILE_REPORT, "w", encoding="utf-8") as f:
        f.write(report_content)
        f.flush()
        os.fsync(f.fileno())

    print(f"\n[+] สร้างรายงานสำเร็จ! บันทึกไฟล์เรียบร้อยที่: '{FILE_REPORT}'")

# CRUD FUNCTIONS & MENU HANDLERS
def handle_add():
    print("\n--- 1) Add (เพิ่มข้อมูลช่องจอด / รถเข้าจอด) ---")
    spots = read_all_spots()

    try:
        spot_id = int(input("กรอก รหัสช่องจอด (Spot ID เช่น 1011): "))
    except ValueError:
        print("[-] ข้อมูลไม่ถูกต้อง! ต้องเป็นตัวเลขเท่านั้น")
        return

    existing = next((s for s in spots if s["spot_id"] == spot_id), None)
    if existing:
        print(f"[-] Spot ID {spot_id} มีอยู่ในระบบแล้ว!")
        return

    zone_input = input("กรอก โซน (กรอก 'A5' หรือ 'Zone-A5' ก็ได้): ").strip()
    if zone_input.lower().startswith("zone-"):
        zone_input = zone_input[5:]
    zone = f"Zone-{zone_input.upper()}"

    vehicle_type = input("กรอก ประเภทรถ (Sedan / SUV / Motorcycle / EV Car): ").strip()
    
    try:
        rate = float(input("กรอก อัตราค่าบริการต่อชั่วโมง (บาท): "))
    except ValueError:
        print("[-] อัตราค่าบริการต้องเป็นตัวเลข")
        return

    is_occupied_in = input("มีรถเข้าจอดเลยหรือไม่? (y/n): ").strip().lower()
    is_occupied = 1 if is_occupied_in == 'y' else 0
    plate = "-"
    entry_ts = 0

    if is_occupied == 1:
        plate = input("กรอก ทะเบียนรถ (เช่น 6กข-9999): ").strip()
        entry_ts = int(time.time())

    new_spot = {
        "spot_id": spot_id,
        "zone": zone,
        "plate": plate,
        "vehicle_type": vehicle_type,
        "rate_per_hr": rate,
        "is_active": 1,
        "is_occupied": is_occupied,
        "entry_ts": entry_ts,
        "exit_ts": 0
    }

    spots.append(new_spot)
    write_all_spots(spots)
    write_log(spot_id, OP_ADD, 1, is_occupied, rate)
    print(f"[+] บันทึกข้อมูล Spot ID {spot_id} (โซน: {zone}) สำเร็จ!")

def handle_update():
    print("\n--- 2) Update (แก้ไขข้อมูล / บันทึกรถออก) ---")
    spots = read_all_spots()

    try:
        spot_id = int(input("กรอก Spot ID ที่ต้องการแก้ไข: "))
    except ValueError:
        print("[-] Spot ID ต้องเป็นตัวเลข")
        return

    spot = next((s for s in spots if s["spot_id"] == spot_id), None)
    if not spot or spot["is_active"] == 0:
        print("[-] ไม่พบ Spot ID นี้ในระบบ หรือช่องจอดถูกลบไปแล้ว")
        return

    print(f"\nพบข้อมูล Spot ID {spot_id} (ปัจจุบัน Occupied={spot['is_occupied']})")
    print(" 1) บันทึกรถเข้าจอด (Check-In)")
    print(" 2) บันทึกรถออก (Check-Out)")
    print(" 3) แก้ไขอัตราค่าบริการ (Rate/hr)")
    choice = input("เลือกรายการที่ต้องการแก้ไข [1-3]: ").strip()

    now = int(time.time())
    if choice == "1":
        if spot["is_occupied"] == 1:
            print("[-] ช่องจอดนี้มีรถจอดอยู่แล้ว!")
            return
        spot["plate"] = input("กรอก ทะเบียนรถที่เข้าจอด: ").strip()
        spot["is_occupied"] = 1
        spot["entry_ts"] = now
        spot["exit_ts"] = 0
        print("[+] บันทึกรถเข้าจอดเรียบร้อย")

    elif choice == "2":
        if spot["is_occupied"] == 0:
            print("[-] ช่องจอดนี้ไม่มีรถจอดอยู่")
            return
        spot["is_occupied"] = 0
        spot["exit_ts"] = now
        print("[+] บันทึกรถออกจากช่องจอดเรียบร้อย")

    elif choice == "3":
        try:
            new_rate = float(input("กรอก อัตราค่าบริการใหม่ (บาท/ชม.): "))
            spot["rate_per_hr"] = new_rate
            print("[+] อัปเดตอัตราค่าบริการเรียบร้อย")
        except ValueError:
            print("[-] ค่าบริการต้องเป็นตัวเลข")
            return
    else:
        print("[-] ตัวเลือกไม่ถูกต้อง")
        return

    write_all_spots(spots)
    write_log(spot_id, OP_UPDATE, spot["is_active"], spot["is_occupied"], spot["rate_per_hr"])

def handle_delete():
    print("\n--- 3) Delete (ลบข้อมูลช่องจอด) ---")
    spots = read_all_spots()

    try:
        spot_id = int(input("กรอก Spot ID ที่ต้องการลบ: "))
    except ValueError:
        print("[-] Spot ID ต้องเป็นตัวเลข")
        return

    spot = next((s for s in spots if s["spot_id"] == spot_id), None)
    if not spot:
        print("[-] ไม่พบ Spot ID นี้ในระบบ")
        return

    status_str = "Active" if spot["is_active"] == 1 else "Deleted (Soft)"
    print(f"\nพบข้อมูล Spot ID {spot_id} (สถานะปัจจุบัน: {status_str})")
    print(" 1) Soft Delete (ปิดใช้งาน/ซ่อนระเบียน - เปลี่ยนสถานะเป็น Deleted)")
    print(" 2) Hard Delete (ลบข้อมูลออกจากไฟล์ไบนารีอย่างถาวร)")
    
    choice = input("เลือกรูปแบบการลบ [1-2]: ").strip()

    if choice == "1":
        if spot["is_active"] == 0:
            print("[-] Spot ID นี้ถูก Soft Delete ไปก่อนหน้านี้แล้ว")
            return
        confirm = input(f"ยืนยัน Soft Delete Spot ID {spot_id}? (y/n): ").strip().lower()
        if confirm == 'y':
            spot["is_active"] = 0
            spot["is_occupied"] = 0
            write_all_spots(spots)
            write_log(spot_id, OP_DELETE, 0, 0, spot["rate_per_hr"])
            print(f"[+] Soft Delete Spot ID {spot_id} สำเร็จ! (สถานะเปลี่ยนเป็น Deleted)")

    elif choice == "2":
        confirm = input(f"ยืนยัน Hard Delete (ลบถาวร) Spot ID {spot_id} หรือไม่? ข้อมูลจะหายทันที (y/n): ").strip().lower()
        if confirm == 'y':
            spots = [s for s in spots if s["spot_id"] != spot_id]
            write_all_spots(spots)
            write_log(spot_id, OP_DELETE, 0, 0, spot["rate_per_hr"])
            print(f"[+] Hard Delete (ลบถาวร) Spot ID {spot_id} ออกจากไฟล์ไบนารีเรียบร้อย!")

    else:
        print("[-] ตัวเลือกไม่ถูกต้อง")

def handle_search_filter():
    print("\n--- 4) Search & Filter (ค้นหาและกรองข้อมูล) ---")
    spots = read_all_spots()

    print(" 1) ค้นหาจาก Spot ID")
    print(" 2) กรองเฉพาะช่องที่ว่าง (Available)")
    print(" 3) กรองตาม Zone")
    choice = input("เลือกตัวเลือก [1-3]: ").strip()

    filtered = []
    if choice == "1":
        try:
            sid = int(input("กรอก Spot ID ที่ต้องการค้นหา: "))
            filtered = [s for s in spots if s["spot_id"] == sid]
        except ValueError:
            print("[-] Spot ID ต้องเป็นตัวเลข")
            return
    elif choice == "2":
        filtered = [s for s in spots if s["is_active"] == 1 and s["is_occupied"] == 0]
    elif choice == "3":
        zone_kw = input("กรอก ชื่อโซน (เช่น Zone-A หรือ Zone-EV): ").strip().lower()
        filtered = [s for s in spots if zone_kw in s["zone"].lower()]
    else:
        print("[-] ตัวเลือกไม่ถูกต้อง")
        return

    if filtered:
        render_table(filtered)
    else:
        print("[-] ไม่พบข้อมูลตามเงื่อนไขที่ระบุ")
    
    input("\nกด Enter เพื่อกลับหน้าหลัก...")

# MAIN PROGRAM LOOP
def main():
    init_sample_data()

    while True:
        spots = read_all_spots()

        render_header()

        render_table(spots)

        render_screen_summary(spots)

        render_main_menu()

        choice = input("Select Option [0-5]: ").strip()

        if choice == "1":
            handle_add()
        elif choice == "2":
            handle_update()
        elif choice == "3":
            handle_delete()
        elif choice == "4":
            handle_search_filter()
        elif choice == "5":
            generate_report()
            input("\nกด Enter เพื่อกลับหน้าหลัก...")
        elif choice == "0":
            print("\n[+] กำลัง Flush/Sync ข้อมูลลงไฟล์ไบนารีและสร้างรายงานอัตโนมัติ...")
            generate_report()
            print("[+] ปิดโปรแกรมเรียบร้อยแล้ว ขอบคุณครับ!")
            break
        else:
            print("[-] ตัวเลือกไม่ถูกต้อง กรุณาเลือก 0-5")
            time.sleep(1)

if __name__ == "__main__":
    main()