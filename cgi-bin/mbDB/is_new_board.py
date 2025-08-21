#!./cgi_runner.sh

import cgi, html
import base
import add_test_functions
import os


print("Content-type: text/html\n")

base.header(title='is_new_board')
base.top()


form = cgi.FieldStorage()

if form.getvalue('full_id'):
    full_id = html.escape(form.getvalue('full_id'))


    is_new_board_bool, check_id = add_test_functions.is_new_board(full_id)

    # tells GUI where to look
    print('Begin')

    print(is_new_board_bool)

    print('End')
    print(check_id)


else:
    print ("NO SERIAL SENT")


base.bottom()

