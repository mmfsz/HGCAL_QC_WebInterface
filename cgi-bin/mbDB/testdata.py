#!./cgi_runner.sh

import cgi, html
import cgitb
import base
import module_functions
import sys
import total_tests as mp

cgitb.enable()
#cgi header
print("Content-type: text/html\n")

base.header(title='Total Tests Over Time')
base.top()

print('''
<div id='exfilter' class='bk-root'></div>
<script>
data = {};
Bokeh.embed.embed_item(data, 'exfilter');
</script>
'''.format(mp.Filter()))

base.bottom()
