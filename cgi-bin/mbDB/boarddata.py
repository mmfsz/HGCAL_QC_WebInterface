#!./cgi_runner.sh

import cgi, html
import cgitb
import base
import module_functions
import sys
import board_status as mp
import bokeh
import os

#cgi header
cgitb.enable()
print("Content-type: text/html\n\n")

base.header(title='Board Status Over Time')
base.top()
print('''
<div id='exfilter' class='bk-root'></div>
<script>
data = {};
Bokeh.embed.embed_item(data, 'exfilter');
</script>
'''.format(mp.Filter()))

base.bottom()

