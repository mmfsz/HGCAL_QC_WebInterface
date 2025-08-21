#!./cgi_runner.sh

import cgi, html
import cgitb; cgitb.enable()
import base
import board_check_functions
import os
from connect import connect, get_base_url, connect_admin

base_url = get_base_url()
db = connect(1)
cur = db.cursor()

#cgi header
print("Content-type: text/html\n")

# grabs the information from the form and calls board_checkout() to enter info into the DB
form = cgi.FieldStorage()
try:
    full = form.getvalue('full_id')
    cur.execute('select board_id from Board where full_id="%s"' % full)
    board_id = cur.fetchall()[0][0]
except:
    board_id = base.cleanCGInumber(form.getvalue("board_id"))
try:
    person_id = base.cleanCGInumber(form.getvalue("person_id"))
    print(person_id)
except:
    person_id = form.getvalue('person_id')
    cur.execute('select person_id from People where person_name="%s"' % person_id)
    try:
        person_id = cur.fetchall()[0][0]
    except:
        raise Exception("This user does not exist in the Testing Database.")
        
try:
    comments = form.getvalue("comments")
except:
    location = form.getvalue("location")
    comments = "Shipped to " + location

if not comments:
    location = form.getvalue("location")
    comments = "Shipped to " + location

base.header(title='Board Check Out')
base.top()

# requires a password only if doing this from the webpage
if form.getvalue('webpage'):
    try:
        admin = connect_admin(form.getvalue('password'))
        cursor = admin.cursor()
        board_check_functions.board_checkout(board_id, person_id, comments)
    except:
        print("Administrative Access Denied.")
else:
    board_check_functions.board_checkout(board_id, person_id, comments)

base.bottom()
