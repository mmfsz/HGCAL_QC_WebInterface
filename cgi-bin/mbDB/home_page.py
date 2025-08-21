#!./cgi_runner.sh
import cgi, html
import cgitb
import base
import home_page_list
import sys

cgitb.enable()
#cgi header
print("content-type: text/html\n\n")

base.header(title='Motherboard Test Home Page')
base.top()

print('<div class="row">')
print('<div class="col-md-12 pt-4 ps-5 mx-2 my-2">')
print('</div>')
print('</div>')
home_page_list.render_list_tests()

base.bottom()
