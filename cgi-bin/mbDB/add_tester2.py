#!./cgi_runner.sh

import cgi, html
import base
import add_test_functions
import os
import connect
import sys

base_url = connect.get_base_url()

#cgi header
print("Content-type: text/html\n")

form = cgi.FieldStorage()
person_name = html.escape(form.getvalue("person_name"))
password = html.escape(form.getvalue("password"))

base.header(title='Add Tester')
base.top()


print(person_name)
add_test_functions.add_tester(person_name, password)

base.bottom()
