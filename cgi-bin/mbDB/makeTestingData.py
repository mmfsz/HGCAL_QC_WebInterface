from connect import connect
import numpy as np
import json
import csv
import os
import io
import pandas as pd
import datetime
import pickle
import multiprocessing as mp
from collections import defaultdict


db = connect(0)
cur = db.cursor(buffered=True)

# collects all the necessary data from the database to be put into .csv WagonDB for the plotting scripts

def get_test():
    # some data can easily be written into a .csv just by writing rows
    # in this case a csv.writer can be used

    csv_file = io.StringIO()

    columns = ['Test ID', 'Test Type ID', 'Board ID', 'Person ID', 'Time', 'Successful']
    writer = csv.writer(csv_file)
    writer.writerow(columns)

    cur.execute('select test_id, test_type_id, board_id, person_id, day, successful from Test order by day asc')
    Test_Data = cur.fetchall()
    writer.writerows(Test_Data)

    # need to tell the file pointer to go to the beginning
    csv_file.seek(0)

    return csv_file

def get_board(): 
    csv_file = io.StringIO()

    header = ['Full ID', 'Board ID', 'Sub Type', 'Location', 'Major Type']
    writer = csv.writer(csv_file)
    writer.writerow(header)
    
    cur.execute('select full_id,board_id,type_id,location from Board')
    Temp_Data = cur.fetchall()
    Board_Data = []
    for line in Temp_Data:
        Board_Data.append(line + (line[0][3:5],))
    writer.writerows(Board_Data)

    csv_file.seek(0)

    return csv_file

def get_people():
    csv_file = io.StringIO()

    header = ['Person ID', 'Person Name']
    writer = csv.writer(csv_file)
    writer.writerow(header)
    
    cur.execute('select * from People')
    People_Data = cur.fetchall()
    writer.writerows(People_Data)

    csv_file.seek(0)

    return csv_file

def get_test_types():
    csv_file = io.StringIO()

    columns = ['Test Type ID', 'Name', 'Required', 'Short Desc.', 'Long Desc.', 'Relative Order']
    writer = csv.writer(csv_file)
    writer.writerow(columns)

    cur.execute('select * from Test_Type')
    Test_Data = cur.fetchall()
    writer.writerows(Test_Data)

    csv_file.seek(0)

    return csv_file

def get_attachments():
    csv_file = io.StringIO()

    columns = ['Test ID', 'Attach ID']
    writer = csv.writer(csv_file)
    writer.writerow(columns)

    cur.execute('select test_id, attach_id from Attachments')
    Test_Data = cur.fetchall()
    writer.writerows(Test_Data)

    csv_file.seek(0)

    return csv_file

def get_check_in():
    csv_file = io.StringIO()

    columns = ['Board ID', 'Check In Time', 'Check Out Time']
    writer = csv.DictWriter(csv_file, fieldnames=columns)
    writer.writeheader()

    cur.execute('select board_id, checkin_date from Check_In')
    CheckIn_Data = cur.fetchall()
    for c in CheckIn_Data:
        cur.execute('select checkout_date from Check_Out where board_id=%s' % c[0])
        checkout_date = cur.fetchall()
        if checkout_date:
            writer.writerow({'Board ID': c[0], 'Check In Time': c[1], 'Check Out Time': checkout_date[0][0]})
        else:
            writer.writerow({'Board ID': c[0], 'Check In Time': c[1], 'Check Out Time': datetime.datetime.fromtimestamp(0)})

    csv_file.seek(0)

    return csv_file

def get_check_out():
    csv_file = io.StringIO()

    columns = ['Board ID', 'Person ID', 'Shipping Location', 'Time']
    writer = csv.writer(csv_file)
    writer.writerow(columns)

    cur.execute('select board_id, person_id, comment, checkout_date from Check_Out')
    check_out = cur.fetchall()
    for c in check_out:
        loc = c[2].split()[-1]
        writer.writerow((c[0], c[1], loc, c[3]))

    csv_file.seek(0)

    return csv_file

def get_stitch_types():
    cur.execute('''
        select BT.type_sn, TTS.type_id, TT.test_type, TT.name
        from Type_test_stitch TTS
        join Board_type BT on BT.type_id=TTS.type_id
        join Test_Type TT on TTS.test_type_id = TT.test_type
    ''')
    stitch_types_by_subtype = {}
    for type_sn, type_id, test_type_id, test_name in cur.fetchall():
        stitch_types_by_subtype.setdefault(type_sn, []).append((test_type_id, test_name))

    return stitch_types_by_subtype

def get_board_states():

    cur.execute('''
        select B.full_id, B.type_id, B.board_id, BT.name as nickname, BT.type_id as bt_type_id, B.location, C.checkin_date  
        from Board B
        join Board_type BT on B.type_id=BT.type_sn
        join Check_In C on B.board_id=C.board_id
        order by B.type_id
    ''')
    all_boards = cur.fetchall()

    boards_by_major_type = {}
    board_info = {}
    for full_id, type_sn, board_id, nickname, bt_type_id, location, checkin_date in all_boards:
        boards_by_major_type.setdefault(type_sn[0:2], []).append(full_id)
        board_info[full_id] = {
                'board_id': board_id,
                'type_sn': type_sn,
                'bt_type_id': bt_type_id,
                'nickname': nickname,
                'check_in_time': checkin_date,
                'location': location,
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

    csvs_to_return = []

    for major_type, boards in boards_by_major_type.items():
        bt_type_id = board_info[boards[0]]['bt_type_id']
        stitch_types = stitch_types_by_subtype.get(bt_type_id, [])

        csv_file = io.StringIO()

        writer = csv.writer(csv_file)
        header = ['Subtype', 'Nickname', 'Full ID', 'Check In Time', 'Location']

        for test_type_id, test_name in stitch_types:
            header.append(test_name)

        header.append('Status')
        writer.writerow(header)

        for full_id in boards:
            row = [
                    board_info[full_id]['type_sn'],
                    board_info[full_id]['nickname'],
                    full_id, 
                    board_info[full_id]['check_in_time'],
                    board_info[full_id]['location'],
                    ]
            board_id = board_info[full_id]['board_id']
            failed = {}
            outcomes = {}
            for test_type_id, test_name in stitch_types:
                result = test_results.get(board_id, {}).get(test_type_id)
                outcomes[test_name] = result == 1
                failed[test_name] = result == 0
                if result == 1:
                    row.append('Passed')
                elif result == 0:
                    row.append('Failed')
                else:
                    row.append('Not Run')


            num_tests_passed = sum(outcomes.values())
            num_tests_req = len(outcomes)
            num_tests_failed = sum(failed.values())

            if board_id in shipped_board_ids:
                status = 'Shipped'
            elif num_tests_failed != 0:
                status = 'Failed QC'
            elif num_tests_passed == num_tests_req:
                status = 'Ready for Shipping'
            elif (num_tests_passed == num_tests_req - 1 and not outcomes.get('Registered', False)):
                status = 'Passed QC, Awaiting Registration'
            else:
                status = 'Awaiting Testing'

            row.append(status)
            writer.writerow(row)

        csv_file.seek(0)
        csvs_to_return.append(csv_file)

    return csvs_to_return

def get_status_over_time():

    cur.execute('''
        SELECT B.full_id, B.type_id, B.board_id, BT.name as nickname, BT.type_id as bt_type_id, B.location, C.checkin_date
        FROM Board B
        JOIN Board_type BT ON B.type_id=BT.type_sn
        JOIN Check_In C ON B.board_id=C.board_id
    ''')
    board_rows = cur.fetchall()

    cur.execute('''
        SELECT T.board_id, T.test_type_id, T.successful, T.day
        FROM Test T
        ORDER BY T.day
    ''')
    test_rows = cur.fetchall()

    cur.execute('SELECT board_id, checkout_date FROM Check_Out')
    checkout_rows = cur.fetchall()

    cur.execute('''
        SELECT TTS.type_id, TT.test_type, TT.name
        FROM Type_test_stitch TTS
        JOIN Test_Type TT ON TTS.test_type_id = TT.test_type
    ''')
    stitch_type_map = defaultdict(list)
    for type_id, test_type_id, test_name in cur.fetchall():
        stitch_type_map[type_id].append((test_type_id, test_name))

    board_info = {}
    all_dates = set()
    for full_id, type_sn, board_id, nickname, bt_type_id, location, checkin_date in board_rows:
        board_info[board_id] = {
            'full_id': full_id,
            'type_sn': type_sn,
            'nickname': nickname,
            'bt_type_id': bt_type_id,
            'location': location,
            'checkin_date': checkin_date,
        }
        all_dates.add(checkin_date.date())

    checkout_dates = {}
    for board_id, checkout_date in checkout_rows:
        checkout_dates[board_id] = checkout_date
        all_dates.add(checkout_date.date())

    test_history = defaultdict(lambda: defaultdict(list))
    for board_id, test_type_id, successful, timestamp in test_rows:
        test_history[board_id][test_type_id].append((timestamp, successful))
        all_dates.add(timestamp.date())

    all_dates = sorted(all_dates)
    status_over_time = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))

    for date in all_dates:
        for board_id, info in board_info.items():
            if info['checkin_date'].date() > date:
                continue  # not yet checked in

            full_id = info['full_id']
            type_sn = info['type_sn']
            major_type = type_sn[:2]
            subtype = type_sn
            bt_type_id = info['bt_type_id']
            stitch_types = stitch_type_map.get(bt_type_id, [])

            # Get most recent test outcomes before or on this date
            outcomes = {}
            failed = {}
            for test_type_id, test_name in stitch_types:
                tests = test_history[board_id][test_type_id]
                latest = None
                for ts, success in tests:
                    if ts.date() <= date:
                        latest = success
                    else:
                        break
                if latest is not None:
                    outcomes[test_name] = latest == 1
                    failed[test_name] = latest == 0
                else:
                    outcomes[test_name] = None
                    failed[test_name] = None

            num_tests_passed = sum(1 for v in outcomes.values() if v is True)
            num_tests_req = len(stitch_types)
            num_tests_failed = sum(1 for v in failed.values() if v is True)

            # Determine status
            if checkout_dates.get(board_id, None) and checkout_dates[board_id].date() <= date:
                status = 'Shipped'
            elif num_tests_failed:
                status = 'Failed QC'
            elif num_tests_passed == num_tests_req:
                status = 'Ready for Shipping'
            elif (num_tests_passed == num_tests_req - 1 and not outcomes.get('Registered', False)):
                status = 'Passed QC, Awaiting Registration'
            else:
                status = 'Awaiting Testing'

            status_over_time[date][major_type][subtype][status] += 1
            status_over_time[date][major_type][subtype]['Total'] += 1

    return status_over_time
