#!./cgi_runner.sh

import cgi, html
import base
from connect import connect
import module_functions
import sys

db = connect(0)
cur = db.cursor()
         
#cgi header
print("Content-type: text/html\n")

base.header(title='Checkin Summary')
base.top()

# grabs all the data from check_in and orders it by date
cur.execute('select board_id,checkin_date,person_id,comment,checkin_id from Check_In order by checkin_date desc')
fetch = cur.fetchall()

# sets up the table and header
print('<div class="row">')
print('<div class="col-md-5 ps-4 pt-4 mx-2 my-2"><h2>Check In Summary</h2></div>')
print('</div>')
print('<div class="row">')
print('<div class="col-md-12">')
print('<div class="col-md-11 ps-5 py-4my-2"><table class="table table-hover">')
print('<thead class="table-dark">')
print('<tr>')
print('<th> Full ID </th>')
print('<th> Check In Date </th>')
print('<th> Person </th>')
print('<th> Comment </th>')
print('<th> Checked Out? </th>')
print('</tr>')
print('</thead>')
print('<tbody>')
# iterates over all the rows in check_in
for d in fetch:
    if d[0] == 0:
        continue
    print('<tr>')
    # gets the serial number from the board_id
    cur.execute('select full_id from Board where board_id=%s' % d[0])
    sn = cur.fetchall()[0][0]
    # links module.py for the serial number
    print('<td> <a href=module.py?board_id=%(id)s&full_id=%(serial)s> %(serial)s </a></td>' %{'serial':sn, 'id':d[0]})
    # adds date
    print('<td> %s </td>' % d[1])
    # gets person name from id
    cur.execute('select person_name from People where person_id=%s' % d[2])
    print('<td> %s </td>' % cur.fetchall()[0][0])
    # adds comment
    print('<td> %s </td>' % d[3])
    # checks if the board has been checked out
    # if so, adds the time it was checked out
    cur.execute('select checkout_date from Check_Out where board_id=%s' % d[0])
    try:
        date = cur.fetchall()[0][0]
    except:
        date = None
    if date:
        print('<td> %s </td>' % date)
    else:
        print('<td> Board has not been shipped </td>')
    print('</tr>')


print('</tbody></table></div></div>')

base.bottom()

