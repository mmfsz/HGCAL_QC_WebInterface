#!./cgi_runner.sh

import cgi, html
import cgitb
cgitb.enable()
import base
#import module_functions
import connect
import os
import tempfile

print("Content-type: text/html\n")
base_url = connect.get_base_url()

form = cgi.FieldStorage()
bc = html.escape(form.getvalue("full_id"))

base.header(title='Change Board Location')
base.top()

# creates form to change board location
# runs change_board_location2.py with the form info on submit
print('<form action="change_board_location2.py" method="post" enctype="multipart/form-data">')
print('<INPUT TYPE="hidden" name="full_id" value="%s">' % (bc))
print('<div class="row">')
print('<div class="col-md-12 pt-4 ps-5 mx-2 my-2">')
print('<h2>Change Board Location %s</h2>' %bc)
print('</div>')
print('</div>')
print('<div class="row">')
print('<div class = "col-md-5 ps-5 pt-2 mx-2 my-2">')
print('<input type="text" name="location" placeholder="Location">')
print('</div>')
print('</div>')
print("<div class='row'>")
print('<div class = "col-md-3 pt-2 ps-5 mx-2 my-2">')
print("<label for='password'>Admin Password</label>")
print("<input type='password' name='password'>")
print("</div>")
print("</div>")
print('<div class="row">')
print('<div class="col-md-6 pt-2 ps-5 mx-2 my-2">')
print('<input type="submit" class="btn btn-dark" value="Update Location">')
print('</div>')
print('</div>')
print('</form>')

base.bottom()
