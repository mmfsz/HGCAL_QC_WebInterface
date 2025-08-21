#!./cgi_runner.sh

import cgi
import base
import settings
import os.path
import sys
import json
import connect
import base64
import csv
import cgitb; cgitb.enable()

db=connect.connect(1)
cur=db.cursor()

form = cgi.FieldStorage()

print("Content-type: text/html\n")

base.header(title='Board Registration Submission')
base.top()

try:
    person_id = base.cleanCGInumber(form.getvalue('person_id'))
    csv_file = form.getvalue('boards')

except:
    print('<div class="row">')
    print('<div class="col-md-12 pt-4 ps-5 mx-2 my-2">')
    print('<h3>Issue getting form, try uploading again </h3>')
    print('</div>')
    print('</div>')

serial_numbers = csv_file.decode('utf-8')

cur.execute('select test_type from Test_Type where name="Registered"')
reg_test_type_id = cur.fetchall()[0][0]

upload = True
for i, sn in enumerate(serial_numbers.strip().split('\n')):
    cur.execute('select board_id from Board where full_id="%s"' % sn)
    try:
        board_id = cur.fetchall()[0][0]
    except:
        print('<div class="row">')
        print('<div class="col-md-12 pt-4 ps-5 mx-2 my-2">')
        print("<h3>No board with serial number {}</h3>".format(sn))
        print('</div>')
        print('</div>')
        upload = False
        continue
    sql = "INSERT INTO Test (person_id, test_type_id, board_id, successful, comments, day) VALUES (%s,%s,%s,%s,%s,NOW())"
    values = (person_id, reg_test_type_id, board_id, 1, "")
    cur.execute(sql, values)

db.commit()

if upload:
    print('<div class="row">')
    print('<div class="col-md-12 pt-4 ps-5 mx-2 my-2">')
    print('<h3>Boards registered successfully!</h3>')
    print('</div>')
    print('</div>')

base.bottom()
