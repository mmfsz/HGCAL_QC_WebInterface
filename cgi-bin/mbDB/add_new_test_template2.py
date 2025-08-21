#!./cgi_runner.sh

import cgi, html
import base
import add_test_functions
import os
import connect

base_url = connect.get_base_url()

#print("Location: summary.py\n\n")
#cgi header
print("Content-type: text/html\n")

form = cgi.FieldStorage()
test_name = html.escape(form.getvalue("test_name"))
required = base.cleanCGInumber(form.getvalue("required"))
test_desc_short = html.escape(form.getvalue("test_desc_short"))
test_desc_long = html.escape(form.getvalue("test_desc_long"))
password = html.escape(form.getvalue("password"))
relative_order = base.cleanCGInumber(form.getvalue("relative_order"))

base.header(title='Add New Test Template')
base.top()

# adds the new test to the database
test_id=add_test_functions.add_new_test(test_name, required, test_desc_short, test_desc_long, password, relative_order)
    
base.bottom()
