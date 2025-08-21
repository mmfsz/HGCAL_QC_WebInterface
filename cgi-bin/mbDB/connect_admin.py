#!./cgi_runner.sh

from connect import connect, connect_admin
import base
import cgi, html
import cgitb
cgitb.enable()

#cgi header
print("Content-type: text/html\n")

form = cgi.FieldStorage()

# admin connection for the GUI, to reach the admin tools page
base.header(title='Try Admin Connection')
base.top()
try:
    password = html.escape(form.getvalue("password"))
except Exception as e:
    print(e)

db = connect_admin(password)
if db:
    print('Begin')
    print('Success')
    print('End')
else:
    print('Begin')
    print("Failed to make DB connection. Wrong admin password")
    print('End')


base.bottom()
