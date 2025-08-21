#!./cgi_runner.sh

import cgi, html
import base
import add_test_functions
import os
import connect
from connect import connect_admin

base_url = connect.get_base_url()

print("Location: summary.py\n\n")
#cgi header
print("Content-type: text/html\n")

form = cgi.FieldStorage()
person_id = base.cleanCGInumber(form.getvalue("person_id"))
test_type = base.cleanCGInumber(form.getvalue("test_type"))
bc = html.escape(form.getvalue("full_id"))
success = base.cleanCGInumber(form.getvalue("success"))
comments = form.getvalue("comments")
password = html.escape(form.getvalue("password"))

if comments:
    comments = html.escape(comments)

base.header(title='Add Test')
base.top()

try:
    db = connect_admin(password)
    cur = db.cursor()

    # adds the test and returns the test id
    test_id=add_test_functions.add_test(person_id, test_type, bc, success, comments)

    # decodes attached file and sends it to the Attachments table
    if test_id:
        for itest in [1]:
            afile = form['attach%d'%(itest)]
            if (afile.name):
                adesc= form.getvalue("attachdesc%d"%(itest))
                if adesc:
                    adesc = html.escape(adesc)
                acomment= form.getvalue("attachcomment%d"%(itest))
                if acomment:
                    acomment = html.escape(acomment)
                add_test_functions.add_test_attachment(test_id,afile,adesc,acomment)
            elif (afile.filename):
                adesc= form.getvalue("attachdesc%d"%(itest))
                if adesc:
                    adesc = html.escape(adesc)
                acomment= form.getvalue("attachcomment%d"%(itest))
                if acomment:
                    acomment = html.escape(acomment)
                add_test_functions.add_test_attachment_gui(test_id,afile,adesc,acomment)

except Exception as e:
    print("Administrative access denied")
    
base.bottom()
