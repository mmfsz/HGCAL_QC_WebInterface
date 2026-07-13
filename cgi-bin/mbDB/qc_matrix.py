#!./cgi_runner.sh

import cgi, html
import cgitb
import base
import sys
from qc_matrix_functions import render_matrix

cgitb.enable()
#cgi header
print("Content-type: text/html\n")

base.header(title='QC Status Matrix')
base.top()

render_matrix()

base.bottom()
