#!./cgi_runner.sh

import cgi, html
import base
import home_page_list

#cgi header
print("Content-type: text/html\n")

# gets board info
form = cgi.FieldStorage()
full_id = html.escape(form.getvalue('full_id'))
board_id = base.cleanCGInumber(form.getvalue('board_id'))

base.header(title='Add extra information about board')
base.top()

# sends board info here
home_page_list.add_board_info_form(full_id, board_id)

base.bottom()

