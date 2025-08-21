#!./cgi_runner.sh

from connect import connect
import cgi, html
import cgitb; cgitb.enable()
import base
import home_page_list
import add_test_functions

def board_checkout_form_sn(full):
    db = connect(0)
    cur = db.cursor()

    # creates a form that sends the information to board_checkout2.py on submitting
    print('<form action="board_checkout2.py" method="post" enctype="multipart/form-data">')
    print("<div class='row'>")
    print('<div class = "col-md-6 pt-4 ps-4 mx-2 my-2">')
    print('<h2>Board Checkout</h2>')
    print("</div>")
    print("</div>")

    print('<input type="hidden" name="webpage" value="True">')

    print("<div class='row'>")
    print('<div class = "col-md-3 pt-2 ps-5 mx-2 my-2">')
    print('<label for="sn">Full ID</label>')
    print('<input type="text" name="full_id" value="%s">'%full)
    print("</div>")

    # creates a form to select the person checking the board out
    cur.execute("Select person_id, person_name from People;")
    print('<div class="col-md-3 pt-2 ps-5 mx-2 my-2">')
    print('<label>Tester')
    print('<select class="form-control" name="person_id">')
    for person_id in cur:
        print("<option value='%s'>%s</option>" % ( person_id[0] , person_id[1] ))
                        
    print('</select>')
    print('</label>')
    print('</div>')

    print("<div class='row'>")
    print('<div class="col-md-9 pt-2 ps-5 mx-2 my-2">')
    print('<label>Location</label><p>')
    print('<textarea rows="1" cols="20" name="location"></textarea>')
    print('</div>')
    print('</div>')

    print("<div class='row'>")
    print('<div class = "col-md-3 pt-2 ps-5 mx-2 my-2">')
    print("<label for='password'>Admin Password</label>")
    print("<input type='password' name='password'>")
    print("</div>")
    print("</div>")

    print("<div class='row'>")
    print('<div class = "col-md-6 pt-2 ps-5 mx-2 my-2">')
    # submits the form on click
    print('<input type="submit" class="btn btn-dark" value="Checkout">')
    print("</div>")
    print("</div>")
    print("<div class='row pt-4'>")
    print("</div>")
    print("</form>")

def board_checkout(board_id, person_id, comments):
    # this function is also used by the Testing GUI
    db = connect(1)
    cur = db.cursor()
   
    try:
        # gets the check in id for this board
        cur.execute('select checkin_id from Check_In where board_id=%s' % board_id)
        checkin_id = cur.fetchall()[0][0]
        print(checkin_id)
      
        # checks if the board has already been checked out
        sql = "SELECT checkin_id, person_id FROM Check_Out WHERE board_id = %s" % board_id
        cur.execute(sql)
        checkouts = cur.fetchall()
        if checkouts:
            checkout_id = checkouts[-1][0]
            checkout_person = checkouts[-1][1]
            print('Error: This board has already been checked out.')

        else:
            # otherwise, checks the board out
            sql = "INSERT INTO Check_Out (checkin_id, board_id, person_id, comment, checkout_date) VALUES (%s, %s, %s, '%s', NOW())" % (checkin_id, board_id, person_id, comments)        
            cur.execute(sql)

            location = comments
           
            sql = "UPDATE Board SET location='%s' WHERE board_id=%i" % (location, board_id)
            cur.execute(sql)
            
            db.commit()
 
            cur.execute('select checkin_id from Check_Out where board_id=%s' % board_id)
            c_id = cur.fetchall()[0][0]
            # this tells the testing GUI where to look to grab the ID
            print('Begin')
            print(c_id)
            print('End') 

    except Exception as e:
        print(e)    

        print('<div class ="row">')
        print('<div class = "col-md-3 pt-4 ps-4 mx-2 my-2">')
        print('<h3> Attempt Failed. Please ensure all fields are filled. </h3>')
        print('</div>')
        print('</div>')
    

def board_checkin_form_sn(full):
    db = connect(0)
    cur = db.cursor()

    # this creates a form that runs board_checkin2.py with the inputted information when submitted
    print('<form action="board_checkin2.py" method="post" enctype="multipart/form-data">')
    print("<div class='row'>")
    print('<div class = "col-md-6 pt-4 ps-4 mx-2 my-2">')
    print('<h2>Board Checkin</h2>')
    print("</div>")
    print("</div>")

    print("<div class='row'>")
    print('<div class = "col-md-3 pt-2 ps-5 mx-2 my-2">')
    print('<label for="sn">Full ID</label>')
    # pre-inputs the barcode if the page was loaded with one
    print('<input type="text" name="full_id" value="%s">'%full)
    print("</div>")

    # creates an input for who's checking in the board
    cur.execute("Select person_id, person_name from People;")

    print('<div class="col-md-3 pt-2 ps-5 mx-2 my-2">')
    print('<label>Tester')
    print('<select class="form-control" name="person_id">')
    for person_id in cur:
        print("<option value='%s'>%s</option>" % ( person_id[0] , person_id[1] ))
                        
    print('</select>')
    print('</label>')
    print('</div>')

    print("<div class='row'>")
    print('<div class="col-md-9 pt-2 ps-5 mx-2 my-2">')
    print('<label>Comments</label><p>')
    print('<textarea rows="5" cols="50" name="comments"></textarea>')
    print('</div>')
    print('</div>')

    print("<div class='row'>")
    print('<div class = "col-md-6 pt-2 ps-5 mx-2 my-2">')
    # button that submits the form on click
    print('<input type="submit" class="btn btn-dark" value="Check In">')
    print("</div>")
    print("</div>")
    print("<div class='row pt-4'>")
    print("</div>")
    print("</form>")

def board_checkin(board_id, person_id, comment):
    # this function is used by both the webpage and the GUI
    # connect(1) to write to the DB
    db = connect(1)
    cur = db.cursor()
   
    try:
        # checks if the board has been checked in before
        sql = "SELECT checkin_id, person_id FROM Check_In WHERE board_id = %s" % board_id
        cur.execute(sql)
        checkins = cur.fetchall()
        if checkins:
            checkin_id = checkins[-1][0]
            checkin_person = checkins[-1][1]
            print('Error: This board has already been checked in.')
        else:
            # if it hasn't, add the check in information
            sql = "INSERT INTO Check_In (board_id, person_id, comment, checkin_date) VALUES (%s, %s, '%s', NOW())" % (board_id, person_id, comment)        
            cur.execute(sql)

            db.commit()        

            cur.execute('select checkin_id from Check_In where board_id=%s' % board_id)
            c_id = cur.fetchall()[0][0]
            # tells the GUI where to grab the check in id from the output
            print('Begin')
            print(c_id)
            print('End') 

    except Exception as e:
        print(e)    

        print('<div class ="row">')
        print('<div class = "col-md-3 pt-4 ps-4 mx-2 my-2">')
        print('<h3> Attempt Failed. Please ensure all fields are filled. </h3>')
        print('</div>')
        print('</div>')
