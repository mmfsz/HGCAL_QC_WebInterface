#!/usr/bin/python3

import cgi
import sys

sys.path.insert(0, '../../hgcal-label-info/label-authority/')
import label_authority as la

#cgi header
print("Content-type: text/html\n")

# takes in a label and prints out the decoded information
# this goes to the GUI and is really only used for Wagons and Engines
form = cgi.FieldStorage()
label = form.getvalue('label')

def decode_label(label):
    
    decoded = la.decode(label)
    major = la.getMajorType(decoded.major_type_code)
    sub = major.getSubtypeByCode(decoded.subtype_code)
    schema = la.getMajorType(decoded.major_type_code).getSubtypeByCode(decoded.subtype_code).serial_schema
    sn = schema.encode(decoded.field_values)
    
    return [major.name, sub.name, sn, major.code, sub.code]

data = decode_label(label)

print('Begin')

for i in data:
    print(i)

print('End')
