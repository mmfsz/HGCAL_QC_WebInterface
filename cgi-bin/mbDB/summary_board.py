#!./cgi_runner.sh

import cgi, html
import base
from connect import connect
import module_functions
import sys
import numpy as np

#cgi header
print("Content-type: text/html\n")

# gets type_id from previous page
form = cgi.FieldStorage()
type_id = form.getvalue('type_id')
base.header(title='Summary')
base.top()

db = connect(0)
cur = db.cursor()

print('<div class="row">')
print('<div class="col-md-5 ps-4 pt-4 mx-2 my-2"><h2>Test Summary</h2></div>')
print('<div class="col-md-2 ps-4 pt-4 my-2">')
print('<a href="summary.py">')
print('<button type="button" class="btn btn-dark text-light">Back to Subtype List</button>')
print('</a>')
print('</div>')
print('</div>')
print('<div class="row">')
print('<div class="col-md-12">')
print('<div class="col-md-11 ps-5 py-4my-2"><table class="table table-hover">')
print('<thead class="table-dark">')
print('<tr>')
print('<th> Full ID </th>')
print('<th> Tests</th>')
print('</tr>')
print('</thead>')
print('<tbody>')

s = type_id

cur.execute('select full_id from Board where type_id="%s"' % s)
li = []
for l in cur.fetchall():
    li.append(l[0])
serial_numbers = np.unique(li).tolist()

cur.execute('select type_id from Board_type where type_sn="%s"' % s)
type_id = cur.fetchall()[0][0]

for sn in serial_numbers:
    # same structure as home page, now with a variable to see if that test has been run
    cur.execute('select test_type_id from Type_test_stitch where type_id=%s' % type_id)

    names = []
    outcomes = {}
    run = {}
    ids = {}
    for t in cur.fetchall():
        cur.execute('select name from Test_Type where test_type=%s' % t[0])
        n = cur.fetchall()[0][0]
        names.append(n)
        ids[n] = t[0]
        outcomes[n] = False
        run[n] = False

    print('<tr>')
    cur.execute('select board_id from Board where full_id="%s"' % sn)
    board_id = cur.fetchall()[0][0]
    cur.execute('select test_type_id, successful, day from Test where board_id=%s order by day desc, test_id desc' % board_id)
    temp = cur.fetchall()
    prev_ids = []
    for t in temp:
        if t[0] not in prev_ids:
            cur.execute('select name from Test_Type where test_type=%s' % t[0])
            name = cur.fetchall()[0][0]
            if t[1] == 1:
                outcomes[name] = True
            run[name] = True
        prev_ids.append(t[0])
    
    # only difference is that all tests are printed out
    print('<td> <a href=module.py?board_id=%(id)s&full_id=%(serial)s> %(serial)s </a></td>' %{'serial':sn, 'id':s})
    print('<td><ul>')
    for n in names: 
        # if the test was successful it's printed green 
        if outcomes[n] == True and run[n] == True:
            print('<li class="list-group-item-success">%s' % n)
        # if test was done and didn't pass, red with a link to add a test of that type
        elif outcomes[n] == False and run[n] == True:
            print('<li class="list-group-item-danger"> <a href="add_test.py?full_id=%(serial_num)s&board_id=%(board_id)s&suggested=%(test_type_id)s">%(name)s</a>' %{'board_id':s, 'serial_num':sn, 'test_type_id':ids[n], 'name':n})
        # if no test has been run, gray with a link
        else:
            print('<li class="list-group-item-dark"> <a href="add_test.py?full_id=%(serial_num)s&board_id=%(board_id)s&suggested=%(test_type_id)s">%(name)s</a>' %{'board_id':s, 'serial_num':sn, 'test_type_id':ids[n], 'name':n})
    
    print('</ul></td>') 

    print('</tr>')
print('</tbody></table></div></div>')


base.bottom()

