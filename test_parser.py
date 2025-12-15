from excel_service import parse_excel_file
import json

FILE_PATH = r"D:\YuKyuDATA-app\有給休暇管理.xlsm"

try:
    data = parse_excel_file(FILE_PATH)
    print(f"Successfully returned {len(data)} records.")
    if len(data) > 0:
        print("Sample Record:", data[0])
    else:
        print("Returned 0 records.")
        
except Exception as e:
    print(f"Error: {e}")
