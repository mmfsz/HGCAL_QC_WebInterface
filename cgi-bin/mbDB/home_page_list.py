#!./cgi_runner.sh

import numpy as np
from connect import connect
import sys
import cgitb
import mariadb
import pandas as pd
import os
import enum

cgitb.enable()
db = connect(0)
cur=db.cursor()

def fetch_list_tests():
    # gets the number of successful tests and number of boards with successful tests for each test
    cur.execute("select Test_Type.name,COUNT(DISTINCT Test.test_id),COUNT(DISTINCT Test.board_id) from Test,Test_Type WHERE Test.successful=1 and Test.test_type_id=Test_Type.test_type GROUP BY Test.test_type_id ORDER BY Test_Type.relative_order");
    rows = cur.fetchall()
    # gets total tests done for each test
    cur.execute("select Test_Type.name,COUNT(DISTINCT Test.test_id) from Test,Test_Type WHERE Test.test_type_id=Test_Type.test_type GROUP BY Test.test_type_id ORDER BY Test_Type.relative_order");
    rows2 = cur.fetchall()
   
    # iterates over test types
    for i,r in enumerate(rows):
        rows[i] = (r[0], r[1], r[2])
    # creates final set of data before returning it
    finalrows = ()
    ofs = 0
    for i in range (0,len(rows2)):
        # returns test type, number of successful tests, number of boards with successful tests, total tests
        if rows2[i][0] == rows[i-ofs][0]:
            arow=(rows2[i][0], rows[i-ofs][1],rows[i-ofs][2],rows2[i][1])
        else:
            arow=(rows2[i][0], 0, 0,rows2[i][1])
            ofs += 1
        finalrows=finalrows+(arow,)
    return finalrows

def render_list_tests():

    cur.execute('''
        select B.full_id, B.type_id, B.board_id, BT.name as nickname, BT.type_id as bt_type_id 
        from Board B
        join Board_type BT on B.type_id=BT.type_sn
        order by B.type_id
    ''')
    all_boards = cur.fetchall()

    boards_by_type_sn = {}
    board_info = {}
    for full_id, type_sn, board_id, nickname, bt_type_id in all_boards:
        boards_by_type_sn.setdefault(type_sn, []).append(full_id)
        board_info[full_id] = {
                'board_id': board_id,
                'type_sn': type_sn,
                'bt_type_id': bt_type_id,
                'nickname': nickname,
        }

    cur.execute('''
        select T.board_id, T.test_type_id, T.successful
        from Test T
        join (
            select board_id, test_type_id, MAX(test_id) as latest_test_id
            from Test
            group by board_id, test_type_id
        ) latest on T.test_id = latest.latest_test_id
    ''')

    test_results = {}
    for board_id, test_type_id, successful in cur.fetchall():
        test_results.setdefault(board_id, {})[test_type_id] = successful

    cur.execute('''
        select TTS.type_id, TT.test_type, TT.name
        from Type_test_stitch TTS
        join Test_Type TT on TTS.test_type_id = TT.test_type
    ''')
    stitch_types_by_subtype = {}
    for type_id, test_type_id, test_name in cur.fetchall():
        stitch_types_by_subtype.setdefault(type_id, []).append((test_type_id, test_name))

    cur.execute('select board_id from Check_Out')
    shipped_board_ids = set(row[0] for row in cur.fetchall())

    print('<div class="col-md-11 mx-4 my-4"><table class="table table-bordered table-hover table-active">')
    print('<tr><th>Subtype<th>Nickname<th>Total Checked In<th>Awaiting Testing<th>QC Passed, Awaiting Registration<th>Ready for Shipping<th>Shipped<th>Failed QC</tr>')

    for type_sn, boards in boards_by_type_sn.items():
        nickname = board_info[boards[0]]['nickname']
        bt_type_id = board_info[boards[0]]['bt_type_id']
        stitch_types = stitch_types_by_subtype.get(bt_type_id, [])

        status_map = {}
        print('<tr>')
        print('<td>%s</td>' % type_sn)
        print('<td>%s</td>' % nickname)

        print('<td>')
        print('<div class="list-group list-group-flush">')
        print('<a class="list-group-item list-group-item-action list-group-item-dark text-decorate-none justify-content-between" data-bs-toggle="collapse" href="#boardstable%s">%s</a>' % (type_sn, len(boards)))
        print('</div>')

        print('<div class="collapse" id="boardstable%s">' % type_sn)
        print('<div class="list-group list-group-flush">')
        for full_id in boards:
            board_id = board_info[full_id]['board_id']
            failed = {}
            outcomes = {}
            for test_type_id, test_name in stitch_types:
                result = test_results.get(board_id, {}).get(test_type_id)
                outcomes[test_name] = result == 1
                failed[test_name] = result == 0

            num_tests_passed = sum(outcomes.values())
            num_tests_req = len(outcomes)
            num_tests_failed = sum(failed.values())

            if board_id in shipped_board_ids:
                status = 'Shipped'
            elif num_tests_failed != 0:
                status = 'Failed'
            elif num_tests_passed == num_tests_req:
                status = 'Passed'
            elif (num_tests_passed == num_tests_req - 1 and not outcomes.get('Registered', False)):
                status = 'Not Registered'
            else:
                status = 'Awaiting'

            status_map[full_id] = status

            print('<a class="list-group-item list-group-item-action text-decorate-none justify-content-between" href="module.py?full_id=%(id)s"> %(id)s </a>' % {'id': full_id})
                
        print('</div></div>')
        print('</td>')

        awaiting = [k for k,v in status_map.items() if v == 'Awaiting']
        not_registered = [k for k,v in status_map.items() if v == 'Not Registered']
        passed = [k for k,v in status_map.items() if v == 'Passed']
        shipped = [k for k,v in status_map.items() if v == 'Shipped']
        failed = [k for k,v in status_map.items() if v == 'Failed']

        def print_status_column(status_id, items):
            print('<td>')
            print('<div class="list-group list-group-flush">')
            print('<a class="list-group-item list-group-item-action list-group-item-dark text-decorate-none justify-content-between" data-bs-toggle="collapse" href="#%s%s">%s</a>' % (status_id, type_sn, len(items)))
            print('</div>')
            print('<div class="collapse" id="%s%s">' % (status_id, type_sn))
            print('<div class="list-group list-group-flush">')
            for b in items:
                print('<a class="list-group-item list-group-item-action text-decorate-none justify-content-between" href="module.py?full_id=%(id)s"> %(id)s </a>' % {'id': b})
            print('</div></div>')
            print('</td>')

        print_status_column('awaiting', awaiting)
        print_status_column('not_reg', not_registered)
        print_status_column('passed', passed)
        print_status_column('shipped', shipped)
        print_status_column('failed', failed)

        print('</tr>')

    print('</table></div>')

    print('<div class="row">')
    print('<div class="col-md-4 mx-4 my-2">')
    print('<form action="create_CSV_for_factory_workflow.py" method="post">')
    print('<button type="submit" class="btn btn-dark text-light">Download Table</button>')
    print('</form>')
    print('</div>')
    print('</div>')

    # gets data for the table
    rows = fetch_list_tests()
    
    print('<div class="row">')
    print('<div class="col-md-11 mx-4 my-4"><table class="table table-bordered table-hover table-active">')
    print('<tr><th>Test<th>Total Tests<th>Total Successful Tests<th>Total Wagons with Successful Tests</tr>')
    for test in rows:
            print('<tr><td>%s' % (test[0]))
            print('<td>%s' % (test[3]))
            print('<td>%s' % (test[1]))
            print('<td>%s' % (test[2]))
            print('</tr>'            )
    print('<tr>')
    print('<td>Shipped</td>')
    cur.execute('select COUNT(DISTINCT board_id) from Check_Out')
    print('<td></td>')
    print('<td></td>')
    print('<td>%s</td>' % cur.fetchall()[0][0])
    print('</table></div>')

def add_module_form():
    
    # calls add_module2.py and sends it the new serial number
    print('<form method="post" class="sub-card-form" action="add_module2.py">')
    print('<div class="row">')
    print('<div class="col-md-12 pt-4 ps-5 mx-2 my-2">')
    print('<h2>Add a new Board</h2>')
    print('</div>')
    print('</div>')

    print('<div class="row">')
    print('<div class = "col-md-3 ps-5 mx-2 my-2">')
    print('<input type="int" name="full_id" placeholder="Full ID">')
    print('</div>')
    cur.execute("Select name from Manufacturers;")
    print('</div>')
    print('<div class="row">')
    print('<div class="col-md-3 ps-5 mx-2 my-2">')
    print('<label>Manufacturer')
    print('<select class="form-control" name="manufacturer">')
    for m in cur:
        print("<option value='%s'>%s</option>" % (m[0],m[0]))
                        
    print('</select>')
    print('</label>')
    print('</div>')
    print('</div>')
    print('<div class="row">')
    print('<div class="col-md-3 ps-5 mx-2 my-2 sub-card-submit">')
    print('<button type="submit" class="btn btn-dark">Submit</button>')
    print('</div>')
    print('</div>')

    print('</form>')

    print('<hr>')

def add_board_info_form(full_id, board_id):
    
    # creates a form for board info and calls add_board_info2.py to submit it
    print('<form method="post" class="sub-card-form" action="add_board_info2.py">')
    print('<div class="row">')
    print('<div class="col-md-12 pt-4 ps-4 mx-2 my-2">')
    print('<h2>Adding Extra Board Information for %s</h2>' % full_id)
    print('</div>')
    print('</div>')

    print('<input type="hidden" name="full_id" value="%s">' % full_id)
    print('<input type="hidden" name="board_id" value="%s">' % board_id)

    print('<div class="row">')
    print('<div class = "col-md-10 ps-5 pt-2 mx-2 my-2">')
    print('<input type="text" name="comments" placeholder="Comments">')
    print('</div>')
    print('</div>')

    print("<div class='row'>")
    print('<div class = "col-md-3 pt-2 ps-5 mx-2 my-2">')
    print("<label for='password'>Admin Password</label>")
    print("<input type='password' name='password'>")
    print("</div>")
    print("</div>")

    print('<div class="row">')
    print('<div class="col-md-1 ps-5 pt-2 mx-2 my-2 sub-card-submit">')
    print('<button type="submit" class="btn btn-dark">Submit</button>')
    print('</div>')
    print('</div>')

    print('<div class="row pt-4">')
    print('</div>')
    
    print('</form>')

    print('<hr>')

def add_module(serial_number, manu, location):
    try:
        db = connect(1)
        cur = db.cursor()
        
        # grabs correct sections of the full id to add it to the database
        if len(serial_number) == 15:
            sn = serial_number[9:15]
            type_id = serial_number[3:9]

            # makes sure serial number doesn't already exist
            cur.execute("SELECT board_id FROM Board WHERE Board.full_id = '%s'" % (serial_number))

            rows = cur.fetchall()

            if not rows:
                if manu != 'None':
                    cur.execute('select manufacturer_id from Manufacturers where name="%s"' % manu)
                    manu_id = cur.fetchall()[0][0]
                    
                    print(manu_id)
                    cur.execute("INSERT INTO Board (sn, full_id, type_id, manufacturer_id, location) VALUES ('%s', '%s', '%s', '%s', '%s'); " % (sn, serial_number, type_id, manu_id, location)) 
                    db.commit()
                    db.close()

                else:
                    cur.execute("INSERT INTO Board (sn, full_id, type_id, location) VALUES ('%s', '%s', '%s', '%s'); " % (sn, serial_number, type_id, location)) 
                    db.commit()
                    db.close()
                print('Board entered successfully!')
            else:
                print("<h3>Board already exists!<h3>")
        else:
            print('Barcode is not the correct length.')
    except mariadb.Error as err:
        print(err)
        print('Failed to enter Board')
    
