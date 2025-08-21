#!./cgi_runner.sh

import cgi, html
import cgitb; cgitb.enable()
import base
import home_page_list
import add_test_functions


#cgi header
print("Content-type: text/html\n")

base.header(title='Board Registration')
base.top()

add_test_functions.register_boards_form()

base.bottom()
