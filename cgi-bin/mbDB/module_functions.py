#!./cgi_runner.sh -B
from connect import *
import sys
import os
from get_attach import save
import home_page_list
import pandas as pd
import numpy as np
import mariadb
import datetime
from datetime import datetime as dt
import uuid
import cgi, html
import json

sys.path.insert(0, '../../hgcal-label-info/label-authority/')
import label_authority as la

#SERVER_NAME

db = connect(0)
cur = db.cursor()


def Portage_fetch(test_type_id, board_sn):
    # gets board id from the serial number
    cur.execute('select board_id from Board where full_id="%s"' % board_sn)
    board_id = cur.fetchall()[0][0]
    # gets list of names, keeps duplicates
    cur.execute('select person_id,day from Test where board_id=%(b)s and test_type_id=%(t)s order by day desc, test_id desc' %{'b':board_id, 't':test_type_id})
    person_id = cur.fetchall()
    person_name = []
    for p in person_id:
        cur.execute('select person_name from People where person_id="%s"' % p[0])
        person_name.append(cur.fetchall()[0][0])
    # gets list of datetime strings
    cur.execute('select day from Test where test_type_id=%(t)s and board_id=%(b)s order by day desc, test_id desc' %{'b':board_id, 't':test_type_id})
    date = cur.fetchall()
    # gets list of outcomes
    cur.execute('select successful,day from Test where test_type_id=%(t)s and board_id=%(b)s order by day desc, test_id desc' %{'b':board_id, 't':test_type_id})
    successful = cur.fetchall()
    # gets list of comments
    cur.execute('select comments,day from Test where test_type_id=%(t)s and board_id=%(b)s order by day desc, test_id desc' %{'b':board_id, 't':test_type_id})
    comments = cur.fetchall()

    # gets list of test ids
    cur.execute('select test_id,day from Test where test_type_id=%(t)s and board_id=%(b)s order by day desc, test_id desc' %{'b':board_id, 't':test_type_id})
    test_id = []
    for t in cur.fetchall():
        test_id.append(t[0])
    return person_name, date, successful, comments, test_id


def Portage_fetch_attach(test_id):
    # gets attachment data for the test id
    # orders by attach id in case there's more than 1 attachment
    cur.execute('select attach_id, attachmime, attachdesc, originalname from Attachments where test_id=%s order by attach_id' % test_id)
    return cur.fetchall()

def add_test_tab(barcode, board_id):

    # adds header
    print('<div class="row">')
    print('<div class="col-md-5 pt-4 ps-5 mx-2 my-2">')
    print('<h2>Test Info for %s</h2>' % barcode)
    print('</div>')
    print('</div>')
    
    decoded = la.decode(barcode)
    major = la.getMajorType(decoded.major_type_code)
    sub = major.getSubtypeByCode(decoded.subtype_code)
    schema = la.getMajorType(decoded.major_type_code).getSubtypeByCode(decoded.subtype_code).serial_schema
    sn = schema.encode(decoded.field_values)
    #sn = decoded.field_values['SerialNumber'].value
    print('<div class="row">')
    print('<div class="col-md-3 pt-4 ps-5 mx-2 my-2">')
    print('<h4>')
    print('Major Type: %s' % major.name)
    print('</h4>')
    print('</div>')
    print('<div class="col-md-3 pt-4 ps-5 mx-2 my-2">')
    print('<h4>')
    print('Sub Type: %s' % sub.name)
    print('</h4>')
    print('</div>')
    print('<div class="col-md-3 pt-4 ps-5 mx-2 my-2">')
    print('<h4>')
    print('Serial Number: %s' % sn)
    print('</h4>')
    print('</div>')
    print('</div>')
    # adds buttons
    print('<div class="row">')
    print('<div class="col-md-2 ps-5 pt-2 my-2">')
    print('<a href="add_test.py?board_id=%(id)d&full_id=%(full_id)s">' %{'full_id':barcode, 'id':board_id})
    print('<button class="btn btn-dark"> Add New Test Results</button>')
    print('</a>')
    print('</div>')
    print('<div class="col-md-2 ps-5 pt-2 my-2">')
    print('<a href="add_board_info.py?board_id=%(id)d&full_id=%(full_id)s">' %{'full_id':barcode, 'id':board_id})
    print('<button class="btn btn-dark"> Add Board Info </button>')
    print('</a>')
    print('</div>')
    print('<div class="col-md-2 ps-5 pt-2 my-2">')
    print('<a href="board_checkout.py?full_id=%(full_id)s">' %{'full_id':barcode})
    print('<button class="btn btn-dark"> Checkout Board </button>')
    print('</a>')
    print('</div>')
    print('<div class="col-md-2 ps-5 pt-2 my-2">')
    print('<a href="add_board_image.py?board_id=%(id)d&full_id=%(full_id)s">' %{'full_id':barcode, 'id':board_id})
    print('<button class="btn btn-dark"> Add Board Image </button>')
    print('</a>')
    print('</div>')
    print('<div class="col-md-2 ps-5 pt-2 my-2">')
    print('<a href="change_board_location.py?board_id=?board_id=%(id)d&full_id=%(full_id)s">' %{'full_id':barcode, 'id':board_id})
    print('<button class="btn btn-dark"> Update Location </button>')
    print('</a>')
    print('</div>')
    print('<div class="col-md-2 ps-5 pt-2 my-2">')
    print('<a href="board_grade.py?board_id=?board_id=%(id)d&full_id=%(full_id)s">' %{'full_id':barcode, 'id':board_id})
    print('<button class="btn btn-dark"> Grade Board </button>')
    print('</a>')
    print('</div>')
    print('</div>')



def ePortageTest(test_type_id, board_sn, test_name):
    # displays test info for each test type, is called for each type individually
    # gets info for test
    person_name, date, successful, comments, test_id = Portage_fetch(test_type_id, board_sn) 
    # separates each test name with a line
    print('<hr>')
    print('<div class="row">')
    print('<div class="col-md-12 px-5 pt-2 mx-2 my-2">')
    print('<h3> %(name)s </h3>' %{ "name":test_name})
    # break before data
    print('<br>')

    # iterates over test ids
    for i in range(len(test_id)):
        n = i+1

        if i == 0:
            # displays the first test 
            print('<table class="table table-bordered table-hover table-active">')
            print('<tbody>')
            print('<tr>')
            print('<th>Name</th>')
            print('<th>Date</th>')
            print('<th colspan=2>Successful?</th>')
            print('</tr>')
            print('<tr>')
            print('<td> %(pname)s </td>' %{ "pname":person_name[i]})
            # the datetime object in the DB is a string, this converts it to a datetime object from string in a nicer format
            print('<td> %(when)s </td>' %{ "when":date[i][0].strftime('%c')})
            # checks if the test was successful
            if successful[i][0] == 1:
                print('<td align=left; class="table-success"> Yes </td>')
                print("<td align=right style='{ background-color: yellow; }' ><a href='revoke_success.py?test_id=%(id)s'>Revoke</a></td>" %{ "id":test_id[i]})

            else:
                print('<td colspan=2; class="table-danger">No</td>')
            print('</tr>')
            print('<tr>')
            print('<td><b>Comments:</b></td>' )
            print('<td colspan=3> %(comm)s </td>' %{ "comm":comments[i][0]})
            print('</tr>')
            # gets attachment(s)
            attachments=Portage_fetch_attach(test_id[i])
            try:
                for afile in attachments:
                    # links attachment
                    print('<tr><td>Attachment: <a href="get_attach.py?attach_id=%s">%s</a><td colspan=2><i>%s</i>' % (afile[0],afile[3],afile[2]))
            except:
                print('<tr><td>Attachment: No attachment<td colspan=3><i>None</i>' % (afile[0],afile[3],afile[2]))
            print('</tr>')
            print('</tbody>')
            print('</table>')
                    
            if len(test_id) > 1:
                print('<a class="btn btn-dark" role="button" data-bs-toggle="collapse" href="#moretests%s" aria-expanded="false" aria-controls="moretests%s">' % (test_type_id, test_type_id))
                print('Show More Tests')
                print('</a>')

                print('<div class="collapse" id="moretests%s">' % test_type_id)

        # hides the others in a dropdown menu
        if i != 0:
            print('<table class="table table-bordered table-hover table-active">')
            print('<tbody>')
            print('<tr>')
            print('<th>Name</th>')
            print('<th>Date</th>')
            print('<th colspan=2>Successful?</th>')
            print('</tr>')
            print('<tr>')
            print('<td> %(pname)s </td>' %{ "pname":person_name[i]})
            # the datetime object in the DB is a string, this converts it to a datetime object from string in a nicer format
            print('<td> %(when)s </td>' %{ "when":date[i][0].strftime('%c')})
            # checks if the test was successful
            if successful[i][0] == 1:
                print('<td align=left> Yes </td>')
                print("<td align=right style='{ background-color: yellow; }' ><a href='revoke_success.py?test_id=%(id)s'>Revoke</a></td>" %{ "id":test_id[i]})

            else:
                print('<td colspan=2>No</td>')
            print('</tr>')
            print('<tr>')
            print('<td><b>Comments:</b></td>' )
            print('<td colspan=3> %(comm)s </td>' %{ "comm":comments[i][0]})
            print('</tr>')
            # gets attachment(s)
            attachments=Portage_fetch_attach(test_id[i])
            try:
                for afile in attachments:
                    # links attachment
                    print('<tr><td>Attachment: <a href="get_attach.py?attach_id=%s">%s</a><td colspan=2><i>%s</i>' % (afile[0],afile[3],afile[2]))
            except:
                print('<tr><td>Attachment: No attachment<td colspan=3><i>None</i>' % (afile[0],afile[3],afile[2]))
            print('</tbody>')
            print('</table>')

        # closes the dropdown if one needs to be created
        if i == len(test_id)-1 and len(test_id) > 1:
            print('</div>')

    print('</div>')
    print('</div>')

def board_info(sn):
    # gets board id

    cur.execute('select board_id from Board where full_id="%s"' % sn)
    board_id = cur.fetchall()[0][0]
    # gets location info
    cur.execute('select location from Board where board_id=%s' % board_id)
    location = cur.fetchall()[0][0]
        
    try:
        cur.execute('select comments from Board where board_id=%s' % board_id)
        info_com = cur.fetchall()[0][0]
    except:
        info_com = 'None'

    registered_name = 'Registered'

    cur.execute('select successful from Test where board_id=%s and test_type_id in (select test_type from Test_Type where name="%s")' % (board_id, registered_name))
    registered = cur.fetchall()
    if registered:
        if registered[0][0] == 1:
            registered = '<td colspan=1><span class="badge bg-success rounded-pill">Done</span></td>'
        else:
            registered = '<td class="bg-danger">&nbsp</td>'
    else:
        registered = '<td>Board has not been registered.</td>'

    # determine how many tests have passed
    cur.execute('select type_id from Board where board_id=%s' % board_id)
    type_sn = cur.fetchall()[0][0]
    cur.execute('select type_id from Board_type where type_sn="%s"' % type_sn)
    type_id = cur.fetchall()[0][0]
    cur.execute('select test_type_id from Type_test_stitch where type_id=%s' % type_id)
    names = cur.fetchall()
    outcomes = []

    cur.execute('select test_type_id, successful, day from Test where board_id=%s order by day desc, test_id desc' % board_id)
    temp = cur.fetchall()
    ids = []
    run = []
    for t in temp:
        if t[0] not in ids:
            if t[1] == 1:
                outcomes.append(True)
            else:
                outcomes.append(False)
        ids.append(t[0])

    num = outcomes.count(True)
    total = len(names)
 
    # adds info
    print('<div class="col-md-11 pt-2 px-4 mx-2 my-2">')
    print('<table class="table table-bordered table-hover table-active">')
    print('<tbody>')
    print('<tr>')
    print('<th colspan=2>Location</th>')
    print('<th colspan=1>Testing Status</th>')
    print('<th colspan=1>Registered?</th>')
    print('</tr>')
    print('<tr>')
    print('<td colspan=2>%s</td>' % location)
    if num == total:
        print('<td colspan=1><span class="badge bg-success rounded-pill">Done</span></td>')
    else:
        print('<td colspan=1><span class="badge bg-dark rounded-pill">%(success)s/%(total)s</span></td>' %{'success': num, 'total': total})
    print(registered)
        
    print('</tr>')
    print('<tr>')
    print('<th colspan=1>Comments</th>')
    print('<th colspan=1>Date Received</th>')
    print('<th colspan=1>Manufacturer</th>')
    print('<th colspan=1>Date Shipped</th>')
    print('</tr>')
    print('<tr>')
    print('<td colspan=1>%s</td>' % info_com)
    # gets check in date
    cur.execute('select checkin_date from Check_In where board_id=%s' % board_id)
    try:
        r_date = cur.fetchall()[0][0]
    except:
        r_date = None
    if r_date:
        print('<td colspan=1>%s</td>' % r_date)
    else:
        print('<td colspan=1>No Receiving Date</td>')  

    cur.execute('select manufacturer_id from Board where board_id=%s' % board_id)
    manuf_id = cur.fetchall()[0][0]
    try:
        cur.execute('select name from Manufacturers where manufacturer_id=%s' % manuf_id)
        manufacturer = cur.fetchall()[0][0]
    except:
        manufacturer = 'None listed'
    print('<td colspan=1>%s</td>' % manufacturer)
        
    # if the board has been checked out, get the check out data
    try:
        cur.execute('select checkout_date,comment from Check_Out where board_id=%s' % board_id)
        checkout = cur.fetchall()[0]
        print('<td>%s</td>' % checkout[0])
    except:
        print('<td colspan=1> Board has not been shipped. </td>')
        
    print('</tr>')
    print('</tbody>')
    print('</table>')

    try:
        print('<h5>Top View:</h5>') 
        print('<img src="get_image.py?board_id=%s&view=%s" width=900 height=auto>' % (board_id, 'Top'))
        print('<h5>Bottom View:</h5>')
        print('<img src="get_image.py?board_id=%s&view=%s" width=900 height=auto>' % (board_id, 'Bottom'))
    except Exception as e:
        print('<h6>This board has no images.</h6>')


def add_board_info(board_id, sn, info, passwd):
    try:
        db = connect_admin(passwd, db_name)
        cur = db.cursor()
    except Exception as e:
        print("Administrative access denied")
        return

    cur.execute('update Board set comments="%s" where board_id=%s' % (info, board_id))

    db.commit()


def add_revoke(test_id):
    db = connect(0)
    cur = db.cursor()
    
    # gets the test type and board id for the test being revoked
    cur.execute("SELECT test_type_id, board_id FROM Test WHERE test_id = %s" % test_id)
    test_type_id, board_id = cur.fetchall()[0]
    
    # gets the test type name
    cur.execute("SELECT name FROM Test_Type WHERE test_type = %s" % test_type_id)
    name = cur.fetchall()[0][0]

    # gets the serial number
    cur.execute("Select full_id FROM Board WHERE board_id = %s" % board_id)
    full_id = cur.fetchall()[0][0]

    print('<div class="row">')
    print('<div class="col-md-10 pt-5 ps-5 mx-2 my-2">')
    print('<h2>Revoke %s for Board %s</h2>' % (name, full_id))
    print('</div>')
    print('</div>')

    # form that submits the revoke by running revoke_success2.py on submit
    print('<form action="revoke_success2.py" method="post" enctype="multipart/form-data">')
    print('<input type="hidden" name="test_id" value="%s">' % test_id)
    # gives options for tester
    cur.execute("Select person_id, person_name from People;")

    print('<div class="row">')
    print('<div class="col-md-3 pt-2 ps-5 mx-2 my-2">')
    print('<label>Tester')
    print('<select class="form-control" name="person_id">')
    for person_id in cur:
        print("<option value='%s'>%s</option>" % ( person_id[0] , person_id[1] ))
                        
    print('</select>')
    print('</label>')
    print('</div>')

    print("<div class='row'>")
    print('<div class = "col-md-3 pt-2 ps-5 mx-2 my-2">')
    print("<label for='password'>Admin Password</label>")
    print("<input type='password' name='password'>")
    print("</div>")
    print("</div>")

    print('<div class="form-group pt-2 px-5 mx-2 my-2">')
    print('<label for="revokeComments"> Revoke Comments </label>')
    print('<textarea class="form-control" name="revokeComments" rows="3" cols="50"></textarea>')
    print('</div>')
    print('<div class="row">')
    print('<div class="col-md-3 pt-2 ps-5 mx-2 my-2">')
    print('<input type="submit" class="btn btn-dark" value="Submit Revoke">')
    print('</form>')

def revoke_success(test_id, comments, person_id):
    # revokes the specified test
    db = connect(1)
    cur = db.cursor()
  
    cur.execute('select board_id, test_type_id from Test where test_id = %s' % test_id)
    x = cur.fetchall()

    cur.execute("insert into Test (person_id, test_type_id, board_id, successful, comments, day) values (%s,%s,%s,%s,%s,NOW())" % (person_id, x[0][1], x[0][0], 0, comments))
    db.commit()

def get_sn_from_lpgbt_id(lpgbt_id):

    QUERY = "SELECT full_id FROM Board INNER JOIN Test INNER JOIN Attachments ON Board.board_id=Test.board_id and Test.test_id=Attachments.test_id WHERE JSON_EXTRACT(Attachments.attach, '$.test_data.DAQ.id') = %s ORDER BY Test.test_id desc"

    lpgbt_id_int = str(int(lpgbt_id, 16)) if lpgbt_id.lower().startswith('0x') else lpgbt_id

    cur.execute(QUERY % (lpgbt_id_int,))
    full_id = cur.fetchall()
    if full_id:
        print(full_id[0][0])
    else:
        print("Could not find full_id associated with LPGBT ID {}".format(lpgbt_id))

def get_test_types():
    # used in Testing GUI
    db = connect(0)
    cur = db.cursor()

    try:
        cur.execute('SELECT name, test_type FROM Test_Type')

        rows = cur.fetchall()
        tests = [[r[0],r[1]] for r in rows]

        return tests

    except mariadb.Error as err:
        print("CONNECTION ERROR")
        print(err)

def add_board_image(sn, img_file, view):
    # writes the image file
    db = connect(1)
    cur = db.cursor() 

    print("Adding board image")

    try: 
        # gets board id
        cur.execute("SELECT board_id FROM Board WHERE full_id = '%s';" % sn)
        rows = cur.fetchall()

        # check if board id exists
        # it will be on the GUI side, new boards are automatically entered when scanned
        if not rows:
            print("Board sn does not exist! Make sure this board has been entered into the database.")

        else:
            board_id = rows[0][0]

        img_path = get_image_location()
        # generates random string for the image name
        img_name = str(uuid.uuid4())

        path = "{}/{}".format(img_path, img_name)

        # puts the file name and other info into DB
        cur.execute('INSERT INTO Board_images (board_id, image_name, view, date) VALUES (%s, "%s", "%s", NOW())' % (board_id, img_name, view))

        db.commit()
        db.close()

        print("Attempting to write file...")

        # saves the image file
        with open(path, "wb") as f:
            print("File opened!")
            f.write(img_file)
            print("File wrote:)")

        print("File received successfully!")

    except mariadb.Error as err:
        print("CONNECTION ERROR")
        print(err)

def change_board_location(sn, location):

    db = connect(1)
    cur = db.cursor() 

    try: 
        # gets board id
        cur.execute("SELECT board_id FROM Board WHERE full_id = '%s';" % sn)
        rows = cur.fetchall()

        # check if board exists
        if not rows:
            print("Board sn does not exist! Make sure this board has been entered into the database.")

        else:
            board_id = rows[0][0]

        # updates location
        cur.execute('UPDATE Board SET location="%s" WHERE board_id=%i' % (location, board_id))

        db.commit()
        db.close()

        print("Location Updated Successfully!")

    except mariadb.Error as err:
        print("CONNECTION ERROR")
        print(err)


