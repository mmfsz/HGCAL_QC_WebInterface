#!./cgi_runner.sh

import cgi, html
import cgitb
import base
import sys
import pandas as pd
import numpy as np
from connect import connect

cgitb.enable()
db = connect(0)
cur = db.cursor()

#cgi header
print("Content-type: text/html\n")

base.header(title='Testers')
base.top()

print('<div class="row">')
print('<div class="col-md-8 ps-4 pt-4 mx-2 my-2"><h2>Tester Summary</h2></div>')
print('<div class="col-md-3 pt-2 ps-2">')
print('<br>')
print('<a href="password_entry.py?url=add_tester.py">')
print('<button type="button" class="btn btn-dark text-light">Add New Tester</button>')
print('</a>')
print('</div>')
print('</div>')

# same idea as the board summary, just with people
cur.execute('select person_id from Test')
temp = cur.fetchall()
person_ids = []
for t in temp:
    person_ids.append(t[0])
people = np.unique(person_ids).tolist()

print('<div class="row">')
print('<div class="col-md-12 ps-5 py-2 mx-2 my-2">')
print('<h4>Select a Tester</h4>')
print('<ul>')
for p in people:
    # for some reason there's a test in the DB with a person_id of 0
    # no entry in the People table with a person_id of 0
    # might need to be removed in the future
    if p != 0:
        cur.execute('select person_name from People where person_id=%s' % p)
        name = cur.fetchall()[0][0]
        print('<li><a href="tester_summary2.py?person_id=%(id)s">%(name)s</a>' % {'name': name, 'id': p})
print('</ul>')
print('</div>')
print('</div>')

base.bottom()
