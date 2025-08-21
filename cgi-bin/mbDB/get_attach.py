#!./cgi_runner.sh

import cgi, html
import base
from connect import connect
import settings
import os.path
import sys
import json

db=connect(0)
cur=db.cursor()


if __name__ == "__main__": 
    form = cgi.FieldStorage()
    attach_id = base.cleanCGInumber(form.getvalue('attach_id'))

    # gets attachment data from DB
    if(attach_id != 0):
        cur.execute("SELECT test_id, attachmime, originalname, attach FROM Attachments WHERE attach_id=%d" % (attach_id));

    # checks to make sure there is attachment data received
    try:
        thevals=cur.fetchall()
        # grabs attached data
        f = thevals[0][3]
        # checks if there is an attachment
        if not f:
            print("Content-type: text/html\n")
            base.header("Attachment Request Error")
            base.top(True)
            print("<h1>Attachment not found</h1>")
            base.bottom()        
        else:
            # decodes the attachment and displays it
            try:
                x = json.dumps(json.loads(f.decode("utf-8")), indent=1)
                print('Content-type: %s \n\n' % (thevals[0][1]))
                print(x)
            #except json.decoder.JSONDecodeError as e:
            except Exception as e:
                print("Content-type: text/html\n")
                base.header("Attachment Request Error")
                base.top()
                print('<div class="col-md-6 ps-4 pt-4 mx-2 my-2">')
                print(e)
                print(f.decode("utf-8"))
                print('</div>')
                base.bottom()        
    except:    
        print("Content-type: text/html\n")
        base.header("Attachment Request Error")
        base.top()
        print('<div class="col-md-6 ps-4 pt-4 mx-2 my-2">')
        print("<h1>Attachment not available</h1>")
        print('</div>')
        base.bottom()
        
    cur.close()

def run(attach_id):
    # gets attachment data from DB
    if(attach_id != 0):
        cur.execute("SELECT test_id, attachmime, originalname, attach FROM Attachments WHERE attach_id=%d" % (attach_id));

    # checks to make sure there is attachment data received
    if not cur.with_rows:
        print('<!doctype html>')
        print('<html lang="en">')
        print('<head>')
        print('<title> Attachment not available </title>')
        print('</head>')
        print('<body>')
        print("<h1>Attachment not available</h1>")
        print('</body>')
        print('</html>')
    else:    
        thevals=cur.fetchall()
        # grabs attached data
        f = thevals[0][3]
        # checks if there is an attachment
        if not f:
            print('<!doctype html>')
            print('<html lang="en">')
            print('<head>')
            print('<title> Attachment Request Error </title>')
            print('</head>')
            print('<body>')
            print("<h1>Attachment not found</h1>")
            print('</body>')
            print('</html>')
        else:
            print('<!doctype html>')
            print('<html lang="en">')
            print('<head>')
            print('<title> Attachment </title>')
            print('</head>')
            print('<body>')
            print('<pre>')
            print(json.dumps(json.loads(f.decode("utf-8")), indent=1))
            print('</pre>')
            print('</body>')
            print('</html>')

# writes a file for the attachment
def save(attach_id):
    db=connect(0)
    cur=db.cursor()

    cur.execute("SELECT test_id, attachmime, originalname FROM Attachments WHERE attach_id=%d" % (attach_id));

    if not cur.with_rows:
        print("<h1>Attachment not available</h1>")
    else:    
        thevals=cur.fetchall();
        attpath=settings.getAttachmentPathFor(thevals[0][0],attach_id)
        if not os.path.isfile(attpath):
            print("<h1>Attachment not found</h1>")
        else:
            statinfo = os.stat(attpath)
            sys.stdout.write(file(attpath,"rb").read() )
    cur.close()

