import sqlite3
import openpyxl
conn = sqlite3.connect('data.db')
c = conn.cursor()
workbook = openpyxl.load_workbook('events.xlsx')
worksheet = workbook.active
for row in worksheet.rows:
    name = row[0].value
    description = row[1].value
    url = row[2].value
    date = row[3].value
    location = row[4].value
    coordinates = row[5].value
    tags = row[6].value
    age = row[7].value
    conn.execute(f'''INSERT INTO events (name, description, thumbnail_url, date, location, coordinates, tags, age, status) VALUES ('{name}', '{description}', '{url}', '{date}', '{location}', '{coordinates}', '{tags}', '{age}', 'active');''')
conn.commit()
