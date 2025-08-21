#!./cgi_runner.sh

import cgi, html
import cgitb
import base
import module_functions
import os
import connect

cgitb.enable()

base_url = connect.get_base_url()

# rerouts page
print("Location: summary.py\n\n")
#cgi header
print("Content-type: text/html\n")

form = cgi.FieldStorage()
full_id = html.escape(form.getvalue("full_id"))
board_id = base.cleanCGInumber(form.getvalue("board_id"))
comments = html.escape(form.getvalue("comments"))
password = form.getvalue('password')

base.header(title='Add Board Info')
base.top()

# sends board info here to be sent to DB
module_functions.add_board_info(board_id, str(full_id), comments, password)

base.bottom()

