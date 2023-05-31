import sqlite3
import openpyxl
conn = sqlite3.connect('data.db')
c = conn.cursor()
workbook = openpyxl.load_workbook('tags.xlsx')
worksheet = workbook.active
for row in worksheet.rows:
    name = row[0].value
    conn.execute(f'''INSERT INTO tags (name) VALUES ('{name}');''')
conn.commit()
