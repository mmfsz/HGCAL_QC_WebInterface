#!./cgi_runner.sh

import cgi, html
import cgitb
import base
import home_page_list
import module_functions
from connect import connect

cgitb.enable()

#cgi header
print("Content-type: text/html\n")


form = cgi.FieldStorage()
test_id = base.cleanCGInumber(form.getvalue('test_id'))
base.header(title='Revoke Test')
base.top()

module_functions.add_revoke(test_id)

base.bottom()
