#!/usr/bin/python3

import mariadb
from hashlib import sha256

# connects to the database, 1 is for inserting and 0 is for reading
def connect(num):
    if(num==1):
        connection = mariadb.connect(
            host='localhost',
            #user='writer',
            user='testwriter',
            password='writepass',
            database=get_db_name(),
            #cursorclass=mariadb.cursors.DictCursor
        )
    if(num==0):
        connection = mariadb.connect(
            host='localhost',
            #user='reader',
            user='testreader',
            password='readpass',
            database=get_db_name(),
            #cursorclass=mariadb.cursors.DictCursor
        )

    return connection

# for requiring an admin password to perform certain actions with the database
def connect_admin(passwd):
    
    
    #if sha256(passwd.encode('utf-8')).hexdigest() == '0af9a3439168759e823f14dd710145547a4a09542e90d0e365eff7bf28884f62':
    if sha256(passwd.encode('utf-8')).hexdigest() == '713bfda78870bf9d1b261f565286f85e97ee614efe5f0faf7c34e7ca4f65baca':
        return connect(1)
    else:
        print("Failed to make DB connection. Wrong admin password")
        return None

# holds the directory location
def get_base_url():
    # TODO replace this with the web address for your directory
    base = "http://localhost/Factory/mbDB/"
    return base

def get_db_name():
    name = 'mbdb'
    return name

def get_image_location():
    # Absolute path to the directory holding photograph-station board images.
    # The photograph station (Testing GUI) must deposit image files here, and the
    # web upload form (add_board_image) writes here as well. Must end with a slash.
    # NOTE: update this to match wherever the photograph station writes on this host.
    fp = "/home/user/HGCAL_QC_WebInterface/board_photos/"
    return fp

