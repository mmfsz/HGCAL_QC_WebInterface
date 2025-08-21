#!./cgi_runner.sh

import cgi, html
import cgitb
import base
import sys
from filter_boards import Filter

cgitb.enable()
#cgi header
print("Content-type: text/html\n")

base.header(title='Search Boards')
base.top()

try:
    form = cgi.FieldStorage()
    major = form.getvalue('major_type')
except:
    major = None

layout = Filter(major)

print('''
<div id='render' class='bk-root'></div>
<script>
data = {};
Bokeh.embed.embed_item(data, 'render');
</script>
'''.format(layout))

base.bottom()

