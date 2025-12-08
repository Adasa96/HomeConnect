import sqlite3
from pathlib import Path

db=Path('db.sqlite3')
print('db_exists', db.exists())
if not db.exists():
    raise SystemExit('No db.sqlite3')
con=sqlite3.connect(str(db))
cur=con.cursor()
print('tables:')
for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print('-', row[0])
print('\nSample counts:')
for t in ('accounts_user','accounts_service','services_serviceprovider','services_servicerequest','connectmpesa_paymentrequest'):
    try:
        r=cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        print(f'{t}:',r)
    except Exception as e:
        print(f'{t}: ERROR ({e})')
con.close()
