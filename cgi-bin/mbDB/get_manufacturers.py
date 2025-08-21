#!./cgi_runner.sh

import cgi, html
import base
import add_test_functions
import os
from connect import connect

print("Content-type: text/html\n")

base.header(title='Get Manufacturers')
base.top()

db = connect(0)
cur = db.cursor()

cur.execute('select name from Manufacturers')
makers = cur.fetchall()

print('Begin')
for m in makers:
    print(m[0])
print('End')


base.bottom()

