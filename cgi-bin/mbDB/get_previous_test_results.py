#!./cgi_runner.sh

import cgi, html
import base
import add_test_functions
import os

#cgi header
print("Content-type: text/html\n")

base.header(title='Get Previous Test Results')
base.top()

form = cgi.FieldStorage()

if form.getvalue('full_id'):
    full_id = html.escape(form.getvalue('full_id'))

    add_test_functions.get_previous_test_results(full_id)

else:
    print('No serial number sent.')
base.bottom()
