#!./cgi_runner.sh

import cgi, html
import cgitb; cgitb.enable()
import base
import home_page_list
import board_check_functions 


#cgi header
print("Content-type: text/html\n")

form = cgi.FieldStorage()

# this page can be accessed from a link that autofills the barcode
# or it can be accessed normally, this checks which one it is
try:
    bc = html.escape(form.getvalue("full_id"))
    board_id = base.cleanCGInumber(form.getvalue("board_id"))
except:
    bc = None
    board_id = None

base.header(title='Board Check In')
base.top()

if bc:
    board_check_functions.board_checkin_form_sn(bc)
else:
    board_check_functions.board_checkin_form_sn("")

base.bottom()
