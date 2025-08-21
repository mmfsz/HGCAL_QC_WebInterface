#!./cgi_runner.sh

import cgi, html
import cgitb
import base
import sys
from search_functions import Filter

cgitb.enable()
#cgi header
print("Content-type: text/html\n")

base.header(title='Search Tests')
base.top()

print('''
<div id='exfilter' class='bk-root'></div>
<script>
data = {};
Bokeh.embed.embed_item(data, 'exfilter');
</script>
'''.format(Filter()))

base.bottom()

