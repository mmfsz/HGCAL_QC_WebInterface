#!./cgi_runner.sh

import cgi
import base
import settings
import os.path
import sys
import json
import connect
import base64

db=connect.connect(0)
cur=db.cursor()

# writes image through cgi instead of a direct hyperlink, better security

form = cgi.FieldStorage()
if form.getvalue('board_id') == 'logo.png':
    fp = '../../static/files/logo.png'
else:
    board_id = base.cleanCGInumber(form.getvalue('board_id'))
    view = form.getvalue('view')

    cur.execute('select image_name, date from Board_images where board_id=%s and view="%s" order by date desc' % (board_id, view))
    image_name = cur.fetchall()[0][0]

    img_dir = connect.get_image_location()
    fp = img_dir + str(image_name)

#assuming everything is a PNG...
sys.stdout.write("Content-Type: image/png\n")


with open(fp, 'rb') as img_file:
    encoded_img = img_file.read()
    sys.stdout.write("Content-Length: %d\n\n"%(len(encoded_img)))
    sys.stdout.flush()
    sys.stdout.buffer.write(encoded_img)
