#!./cgi_runner.sh

import cgi, html
import base
import home_page_list

#cgi header
print("Content-type: text/html\n")

base.header(title='Add a new board to HGCAL Test')
base.top()

# calls this function for the form
home_page_list.add_module_form()
base.bottom()

