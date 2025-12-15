
import sqlite3
import pandas as pd

conn = sqlite3.connect('d:/YuKyuDATA-app/yukyu.db')
df = pd.read_sql_query("SELECT * FROM employees", conn)
print(f"Total records: {len(df)}")
print(f"Unique employee numbers: {df['employee_num'].nunique()}")
print(f"Years found: {df['year'].unique()}")

# Check for duplicates or specific year counts
print("\nCounts by Year:")
print(df.groupby('year').size())

# Peek at the data
print("\nSample Data:")
print(df.head())

# Check for potential duplicates by name or weird employee numbers
print("\nDuplicate Employee Numbers in same year:")
duplicates = df[df.duplicated(subset=['employee_num', 'year'], keep=False)]
print(duplicates)

conn.close()
