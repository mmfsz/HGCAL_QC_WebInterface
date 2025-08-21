#!./cgi_runner.sh

import cgi, html
import base
import module_functions
import os

#cgi header
print("Content-type: text/json\n")

#base.header(title='Get Previous Test Results')
#base.top()

form = cgi.FieldStorage()

if form.getvalue('lpgbt_id'):
    lpgbt_id = html.escape(form.getvalue('lpgbt_id'))

    module_functions.get_sn_from_lpgbt_id(lpgbt_id)

else:
    print('No LPGBT ID sent.')
#base.bottom()
