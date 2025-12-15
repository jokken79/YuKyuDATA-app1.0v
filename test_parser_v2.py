from excel_service import parse_excel_file
import sys

FILE_PATH = r"D:\YuKyuDATA-app\有給休暇管理.xlsm"

try:
    print("--- START PARSE ---")
    data = parse_excel_file(FILE_PATH)
    print(f"--- RESULT COUNT: {len(data)} ---")
    
    if len(data) > 0:
        print(f"First Record: {data[0]}")
        print(f"Last Record: {data[-1]}")
    else:
        print("NO DATA FOUND")
        
except Exception as e:
    print(f"BIG ERROR: {e}")
