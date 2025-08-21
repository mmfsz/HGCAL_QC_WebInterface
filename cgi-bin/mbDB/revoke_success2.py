#!./cgi_runner.sh

import cgi, html
import cgitb
import base
import module_functions
import connect
from connect import connect_admin

cgitb.enable()

base_url = connect.get_base_url()

print("Location: %s/summary.py\n\n"%(base_url))
#cgi header
print("Content-type: text/html\n")

form = cgi.FieldStorage()
test_id = base.cleanCGInumber(form.getvalue("test_id"))
comments = form.getvalue("revokeComments")
person_id = form.getvalue("person_id")
password = form.getvalue("password")

if comments:
    comments = html.escape(comments)

base.header(title='Revoke Success')
base.top()

try:
    db = connect_admin(password)
    cur = db.cursor()

    module_functions.revoke_success(test_id, comments, person_id)
except:
    print("Administrative access denied")

base.bottom()


