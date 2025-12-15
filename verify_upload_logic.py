
import os
import sys
from excel_service import parse_genzai_sheet, parse_ukeoi_sheet

FILE_PATH = "d:/YuKyuDATA-app/【新】社員台帳(UNS)T　2022.04.05～.xlsm"

def verify():
    if not os.path.exists(FILE_PATH):
        print(f"File not found: {FILE_PATH}")
        return

    print(f"Testing parsing of: {FILE_PATH}")
    
    # Test Genzai
    try:
        genzai_data = parse_genzai_sheet(FILE_PATH)
        zeros = [d for d in genzai_data if d['name'] == '0' or d['employee_num'] == '0' or d['name'] == 'Unknown']
        print(f"Genzai Total: {len(genzai_data)}")
        print(f"Genzai '0' or 'Unknown' Rows: {len(zeros)}")
        if zeros:
            print("FAILED: Found invalid rows in Genzai!")
            for z in zeros:
                print(z)
        else:
            print("SUCCESS: Genzai data is clean.")
    except Exception as e:
        print(f"Genzai Parse Error: {e}")

    # Test Ukeoi
    try:
        ukeoi_data = parse_ukeoi_sheet(FILE_PATH)
        zeros = [d for d in ukeoi_data if d['name'] == '0' or d['employee_num'] == '0' or d['name'] == 'Unknown']
        print(f"Ukeoi Total: {len(ukeoi_data)}")
        print(f"Ukeoi '0' or 'Unknown' Rows: {len(zeros)}")
        if zeros:
            print("FAILED: Found invalid rows in Ukeoi!")
        else:
            print("SUCCESS: Ukeoi data is clean.")
    except Exception as e:
        print(f"Ukeoi Parse Error: {e}")

if __name__ == "__main__":
    verify()
