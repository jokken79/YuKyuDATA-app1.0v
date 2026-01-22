import pandas as pd
import sys

file_path = r"E:\CosasParaAppsJp\有給休暇管理.xlsm"
sheet_name = "作業者データ　有給"

try:
    # Read with header discovery (might be in row 1 or 2)
    # Trying various headers
    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', header=None)
    
    print("Top rows of raw data:")
    print(df.head(10).to_string())
    
    # Analyze where the header is
    # Usually row 0 or 1.
    
except Exception as e:
    print(f"Error parsing Excel: {e}")
