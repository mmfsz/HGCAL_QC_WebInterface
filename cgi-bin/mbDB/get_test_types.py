#!./cgi_runner.sh

import cgi, html
import base
import module_functions 
import os

#cgi header
print("Content-type: text/html\n")

base.header(title='Get Test Types')
base.top()

tests = module_functions.get_test_types()

# tells the GUI where to look
print('Begin')

for t in tests:
    print(t)

print('End')

base.bottom()
