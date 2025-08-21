#!./cgi_runner.sh

import module_functions
import cgi, html
import base
from connect import connect_admin

#cgi header
print("Content-type: text/html\n")

form = cgi.FieldStorage()
bc = html.escape(form.getvalue("full_id"))
location = html.escape(form.getvalue("location"))
password = form.getvalue('password')

base.header(title='Change Board Location')
base.top()
try:
    db = connect_admin(password)
    cur = db.cursor()
    try:
        module_functions.change_board_location(str(bc), location)
    except Exception as e:
        print("Issue updating board location")
        print(e)
except:
    print('Administrative Access Denied.')

base.bottom()
