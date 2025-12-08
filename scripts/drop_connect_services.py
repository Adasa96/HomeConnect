import sqlite3
conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS connect_services")
conn.commit()
print('Dropped connect_services (if it existed)')
conn.close()
