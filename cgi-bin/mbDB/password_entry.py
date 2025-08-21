#!./cgi_runner.sh

import cgi, html
import base
import home_page_list
import add_test_functions


#cgi header
print("Content-type: text/html\n")

form = cgi.FieldStorage()
url = form.getvalue("url")

base.header(title='Admin Access')
base.top()

# form to input admin password to access a page that needs admin password
# the next page is encoded in the variable url
print('<form action="password_entry2.py" method="post" enctype="multipart/form-data">')
print('<input type="hidden" name="url" value="%s">'%url)
print("<div class='row'>")
print('<div class = "col-md-6 pt-4 ps-4 mx-2 my-2">')
print('<h2>Admin Access<h2>')
print("</div>")
print("</div>")

print("<div class='row'>")
print('<div class = "col-md-2 pt-2 ps-5 mx-2 my-2">')
print("<label for='password'>Password</label>")
print("<input type='password' name='password'>")
print("</div>")

print('<div class = "col-md-12 ps-5 mx-2">')
print('<input type="submit" value="Sign In">')
print("</div>")
print("</div>")
print("</form>")

print("<div class='row pt-4 my-2'>")

base.bottom()
