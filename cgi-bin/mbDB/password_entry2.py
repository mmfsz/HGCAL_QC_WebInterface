#!./cgi_runner.sh

import cgi, html
import base
import home_page_list
import add_test_functions
import hashlib
import connect
import connect_admin

try: 
    base_url = connect.get_base_url()

    form = cgi.FieldStorage()
    url = form.getvalue("url")
    password = form.getvalue("password")

    db = connect_admin(password)
    # decodes password and checks if it's correct
    if db:
        print("Location: %s/%s\n\n" % (base_url,url))

        print("Content-type: text/html\n")

        base.header(title='Access Granted')
        base.top()

        print("<div class='row'>")
        print('<div class = "col-md-6 pt-4 ps-4 mx-2 my-2">')
        print('<h2>Access Granted</h2>')
        print("</div>")
        print("</div>")

        base.bottom()

    else:
        print("Content-type: text/html\n")
        
        base.header(title='Access Denied')
        base.top()

        print("<div class='row'>")
        print('<div class = "col-md-6 pt-4 ps-4 mx-2 my-2">')
        print('<h2>Access Denied</h2>')
        print("</div>")
        print("</div>")

        base.bottom()

except Exception as e:
    print("content-type: text/html\n")
    print(e)
