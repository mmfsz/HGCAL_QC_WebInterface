#!./cgi_runner.sh

import cgi, html
import base
from connect import connect


print("Content-type: text/html\n")

base.header(title='Update Location')
base.top()

db = connect(1)
cur = db.cursor()

form = cgi.FieldStorage()

if form.getvalue('full_id'):
    full_id = html.escape(form.getvalue('full_id'))
    loc = html.escape(form.getvalue('location'))

    try:
        # updates the location of the board in the database
        cur.execute('update Board set location="%s" where full_id="%s"' %(loc, full_id))
        db.commit()

        # tells GUI where to look
        print('Begin')

        print('Location Updated.')

        print('End')
    except:
        print('Begin')

        print('An Error Occured when updating the location.')

        print('End')
        


else:
    print ("NO SERIAL SENT")


base.bottom()

