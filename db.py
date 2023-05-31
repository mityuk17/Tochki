import sqlite3


def start():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    admin INTEGER,
    age INTEGER,
    sex TEXT,
    active_tags TEXT
    );''')
    c.execute('''CREATE TABLE IF NOT EXISTS tags(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
    );''')
    c.execute('''CREATE TABLE IF NOT EXISTS events(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    thumbnail_url TEXT,
    date TEXT,
    location TEXT,
    coordinates TEXT,
    tags TEXT,
    age TEXT,
    status TEXT
    );''')
    conn.commit()


async def get_user(user_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM users WHERE user_id = {user_id};''')
    data = c.fetchall()
    if not data:
        return False
    user = data[0]
    user = {
        'user_id': user[0],
        'admin': bool(user[1]),
        'age': user[2],
        'sex': user[3],
        'active_tags': list(map(int, user[4].split()))
    }
    conn.close()
    return user


async def get_tags():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM tags;''')
    return c.fetchall()


async def get_events():
    result = list()
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM events WHERE status = 'active';''')
    data = c.fetchall()
    for row in data:
        event = {
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'thumbnail_url': row[3],
            'date': row[4],
            'location': row[5],
            'coordinates': list(map(float, row[6].split())),
            'tags': list(map(int, row[7].split())),
            'age': list(map(int, row[8].split('-'))),
            'status': row[9]
        }
        result.append(event)
    return result


async def get_events_by_tag(tag_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM events WHERE status = 'active';''')
    data = c.fetchall()
    result = list()
    for row in data:
        if tag_id in list(map(int, row[7].split())):
            event = {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'thumbnail_url': row[3],
                'date': row[4],
                'location': row[5],
                'coordin    ates': list(map(float, row[6].split())),
                'tags': list(map(int, row[7].split())),
                'age': list(map(int, row[8].split('-'))),
                'status': row[9]
            }
            result.append(event)
    return result


async def get_event_by_id(event_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM events WHERE id = {event_id};''')
    row = c.fetchall()[0]
    event = {
        'id': row[0],
        'name': row[1],
        'description': row[2],
        'thumbnail_url': row[3],
        'date': row[4],
        'location': row[5],
        'coordinates': list(map(float, row[6].split())),
        'tags': list(map(int, row[7].split())),
        'age': list(map(int, row[8].split('-'))),
        'status': row[9]
    }
    return event



async def create_user(user: dict):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''INSERT INTO users (user_id, admin, age, sex, active_tags) VALUES (
    {user.get('user_id')},
    {int(user.get('admin'))},
    {user.get('age')},
    '{user.get('sex')}',
    '{user.get('active_tags')}'
);''')
    conn.commit()


async def check_user_exists(user_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM users WHERE user_id = {user_id};''')
    if c.fetchall():
        return True
    else:
        return False


async def change_age(user_id: int, new_age: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''UPDATE users SET age ={new_age} WHERE user_id = {user_id};''')
    conn.commit()


async def change_sex(user_id: int, new_sex: str):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''UPDATE users SET sex = '{new_sex}' WHERE user_id = {user_id};''')
    conn.commit()


async def change_active_tags(user_id: int, new_tags):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    print(new_tags)
    c.execute(f'''UPDATE users SET active_tags ='{new_tags}' WHERE user_id = {user_id};''')
    conn.commit()


async def create_new_tag(name):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''INSERT INTO tags (name) VALUES ('{name}');''')
    conn.commit()


async def create_event(event: dict):
    ...


async def drop_event(event_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''UPDATE events SET status = 'old' WHERE event_id={event_id}''')
    conn.commit()