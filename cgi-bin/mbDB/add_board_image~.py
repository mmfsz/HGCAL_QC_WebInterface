#!./cgi_runner.sh

import cgi, html
import cgitb
cgitb.enable()
import base
import module_functions
import connect
import os
import base64

# this is used to upload images from the GUI
print("Content-type: text/html\n")
base_url = connect.get_base_url()

form = cgi.FieldStorage()
full = html.escape(form.getvalue("full_id"))
fileitem = html.escape(form.getvalue("image"))
view = html.escape(form.getvalue("view"))

# GUI encodes image in base64 so it can be sent over http
fileitems = base64.b64decode(fileitem)

try:
    module_functions.add_board_image(str(full), fileitems, view)
except Exception as e:
    print("Issue uploading")
    print(e)
