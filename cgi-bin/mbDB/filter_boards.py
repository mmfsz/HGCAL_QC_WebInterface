#!./cgi_runner.sh

import sys
import pandas as pd
import csv
import numpy as np
from datetime import datetime as dt
import datetime
from bokeh.plotting import figure
from bokeh.models import (
    ColumnDataSource, 
    CustomJS, 
    CheckboxGroup, 
    CustomJSFilter, 
    MultiChoice, 
    CDSView, 
    DatePicker,
    DataTable,
    DateFormatter,
    TableColumn,
    Select,
    Label,
    NumericInput,
)
from bokeh.embed import json_item
from bokeh.layouts import column, row
from bokeh.models.widgets import HTMLTemplateFormatter
import numpy as np
import pandas as pd
import json
from datetime import datetime as dt
import datetime
import makeTestingData as mTD

csv_WM, = mTD.get_board_states()
stitch_types = mTD.get_stitch_types()
WM = pd.read_csv(csv_WM, parse_dates=['Check In Time'])

filter_code=('''
const is_selected_map = new Map([
    ["multi_choice", (wi, pos, el, idx) => wi.value.includes(el)],
    ["date_range", (wi, pos, el, idx) => wi.value == el]
]);
const passed_vals = new Map(
    Object.keys(mc_widgets).map(
        (col) => {
            let pos = mc_widgets[col].possible_vals;
            let wi = mc_widgets[col].widget;
            let t = mc_widgets[col].type;
            return [col, new Map(pos.map((x, i) => [x, is_selected_map.get(t)(wi, pos, x, i)]))];
        })
);
const keys = Array.from(passed_vals.keys());
function allfalse(value) {
    return value === false;
}
for (let k = 0; k < keys.length; k++) {
    const innermap = passed_vals.get(keys[k])
    const pv = Array.from(passed_vals.get(keys[k]).values())
    let bool = pv.every(allfalse);
    const nk = Array.from(passed_vals.get(keys[k]).keys())
    if (bool == true) {
        for (let i = 0; i < nk.length; i++) {
            innermap.set(nk[i], true)
        }
    passed_vals.set(keys[k], innermap);
    }
}
const indices = [];
for (let i = 0; i < source.get_length(); i++) {
    if (keys.every((k) => {
            return passed_vals.get(k).get(source.data[k][i])
        })) {
        indices.push(true);
    } else {
        indices.push(false);
    }
}
const dates = new Map(
    Object.keys(dr_widgets).map(
        (col) => {
            let pos = dr_widgets[col].possible_vals;
            let wi = dr_widgets[col].widget;
            let t = dr_widgets[col].type;
            return [col, new Map(pos.map((x, i) => [x, is_selected_map.get(t)(wi, pos, x, i)]))];
        })
);
const d_keys = Array.from(dates.get('Checked In After').keys());
let start_date = 0;
let end_date = 0;
for (let i = 0; i < d_keys.length; i++) {
    if (dates.get('Checked In After').get(d_keys[i]) == true) {
        let sd = d_keys[i];
        start_date = new Date(sd);
    }
    if (dates.get('Checked In Before').get(d_keys[i]) == true) {
        let ed = d_keys[i];
        end_date = new Date(ed);
    }
}
for (let i = 0; i < source.get_length(); i++) {
    if (source.data['Check In Time'][i] >= start_date && source.data['Check In Time'][i] <= end_date && indices[i] == true) {
        indices[i] = true;
    } else {
        indices[i] = false;
    }
}
return indices;

''')

def makeTable(ds, widgets, view, test_names, serial_numbers):
    data_dict = {'Sub Type':[], 'Nickname':[], 'Full ID':[], 'Location':[], 'Status': [], 'Check In Date':[], 'Raw Time': []}
    for name in test_names:
        data_dict[name] = []

    td = ColumnDataSource(data_dict)

    x = CustomJS(args=dict(td=td, data=ds, view=view, test_names=test_names, serial_numbers=serial_numbers),code='''
const type_ids = [];
const nicknames = [];
const full_ids = [];
const locations = [];
const status = [];
const dates = [];
const raw_times = [];
const test_dict = {};
for (let i = 0; i < test_names.length; i++) {
    test_dict[test_names[i]] = [];
}

const indices = view.filters[0].compute_indices(data);
let mask = new Array(data.data['Full ID'].length).fill(false);
[...indices].forEach((x)=>{mask[x] = true;})

for (let sn = 0; sn < serial_numbers.length; sn++) {
    if (mask[sn] == true) {
        type_ids.push(data.data['Subtype'][sn])
        nicknames.push(data.data['Nickname'][sn])
        full_ids.push(data.data['Full ID'][sn])
        locations.push(data.data['Location'][sn])
        status.push(data.data['Status'][sn])

        // converts to eastern time
        let temp_date = new Date(data.data['Check In Time'][sn]);
        if (String(temp_date).includes('Daylight')) {
            temp_date = new Date(data.data['Check In Time'][sn] + 18000000 + 3600000);
        } else {
            temp_date = new Date(data.data['Check In Time'][sn] + 21600000 + 3600000);
        }
        let date = temp_date.toString().slice(4, 24)
        dates.push(date)
        raw_times.push(temp_date.valueOf())

        for (let i = 0; i < test_names.length; i++) {
            test_dict[test_names[i]].push(data.data[test_names[i]][sn])
        }

    }
}
td.data['Sub Type'] = type_ids;
td.data['Nickname'] = nicknames;
td.data['Full ID'] = full_ids;
td.data['Location'] = locations;
td.data['Status'] = status;
td.data['Check In Date'] = dates;
td.data['Raw Time'] = raw_times;
for (let i = 0; i < test_names.length; i++) {
    td.data[test_names[i]] = test_dict[test_names[i]];
}
td.change.emit()
''')

    for widget in widgets.values():
        widget.js_on_change('value', x)

    return td

def Filter(major_type):
    # how to split up this page based on boards with different tests
    if major_type == 'WM':
        ds = ColumnDataSource(WM.sort_values('Check In Time', ascending=False))
        test_types = stitch_types.get('WMMBD0', [])
    # for all the same tests

    # create the widgets to be used
    mc_widgets = {}
    dr_widgets = {}
    multi_choice = (lambda x,y: MultiChoice(options=x, value=[], title=y), 'value')
    start_date = (lambda x,y,z: DatePicker(min_date=x,max_date=y, value=x, title=z), 'value')
    today = datetime.date.today()
    today_plus_one = today + datetime.timedelta(days=1)
    end_date = (lambda x,y,z: DatePicker(min_date=x,max_date=y, value=today_plus_one, title=z), 'value')
    min_date = pd.Timestamp((min(ds.data['Check In Time']))).date()
    date_range = []
    while min_date <= today_plus_one:
        date_range.append(min_date)
        min_date += datetime.timedelta(days=1)
    # widget titles and data for those widgets has to be manually entered, as well as the type
    columns = ['Subtype', 'Nickname', 'Location', 'Status', 'Checked In After', 'Checked In Before']
    data = [ds.data['Subtype'].tolist(), ds.data['Nickname'].tolist(), ds.data['Location'].tolist(), ds.data['Status'].tolist(), date_range, date_range]
    t = [multi_choice, multi_choice, multi_choice, multi_choice, start_date, end_date]

    test_names = []
    for test_id,test_name in test_types:
        columns.append(test_name)
        test_names.append(test_name)
        data.append(ds.data[test_name].tolist())
        t.append(multi_choice)

    # constructs the widgets
    for i in range(len(columns)):
        widget_constructor, trigger = t[i]
        if t[i] == multi_choice:
            possible_vals = np.unique(data[i]).tolist()
            widget = widget_constructor(possible_vals, columns[i])
            typ = 'multi_choice'
            widget.js_on_change(trigger, CustomJS(args=dict(src=ds), code='src.change.emit()'))
            mc_widgets[columns[i]] = {
                'type': typ,
                'possible_vals': possible_vals,
                'widget': widget,}
        else:
            possible_vals = data[i]
            widget = widget_constructor(min(data[i]),max(data[i]), columns[i])
            typ = 'date_range'
            widget.js_on_change(trigger, CustomJS(args=dict(src=ds), code='src.change.emit()'))
            dr_widgets[columns[i]] = {
                'type': typ,
                'possible_vals': possible_vals,
                'widget': widget,}

    #custom data filter, has to be written in javascript to be integrated into the website
    custom_filter = CustomJSFilter(args=dict(mc_widgets=mc_widgets, dr_widgets=dr_widgets),code=filter_code)
    #implements the filter on the data source
    view = CDSView(source=ds, filters=[custom_filter])
    #sets up all the objects to be created
    all_widgets = {**mc_widgets, **dr_widgets}
    widgets = {k:w['widget'] for k,w in all_widgets.items()}

    serial_numbers = np.unique(ds.data['Full ID'].tolist()).tolist()

    td = makeTable(ds, widgets, view, test_names, serial_numbers)
    
    # html template formatter can be used to apply typical html code to bokeh elements
    template = '''
<div style="font-size: 150%">
<%= value %>
</div> 
'''
    bigger_font = HTMLTemplateFormatter(template=template)

    module_template = '''
<div style="font-size: 150%">
<a href="module.py?full_id=<%= value %>"target="_blank">
<%= value %>
</a>
</div> 
'''
    board = HTMLTemplateFormatter(template=module_template)

    color_template = '''
<div style="font-size: 150%; background:<%=
    (function color() {
        if (value == 'Passed'){
            return('#d1e7dd')}
        else if (value == 'Failed'){
            return('#f8d7da')}
        else if (value == 'Not Run'){
            return('#d3d3d4')}
        }())%>;">
<%= value %>
</div> 
'''

    color_status = HTMLTemplateFormatter(template=color_template)

    color_template_2 = '''
<div style="font-size: 150%; background:<%=
    (function color() {
        if (value == 'Shipped'){
            return('#2ca02c')}
        else if (value == 'Ready for Shipping'){
            return('#1f77b4')}
        else if (value == 'Awaiting Testing'){
            return('#ff7f0e')}
        else if (value == 'Failed QC'){
            return('#d62728')}
        else if (value == 'Passed QC, Awaiting Registration'){
            return('#17becf')}
        }())%>;">
<%= value %>
</div> 
'''

    color_status_2 = HTMLTemplateFormatter(template=color_template_2)

    table_columns = [
                    TableColumn(field='Sub Type', title='Sub Type', formatter=bigger_font, width=100),
                    TableColumn(field='Nickname', title='Nickname', formatter=bigger_font, width=100),
                    TableColumn(field='Full ID', title='Full ID', formatter=board, width=180),
                    TableColumn(field='Location', title='Location', formatter=bigger_font, width=180),
                    TableColumn(field='Status', title='Status', formatter=color_status_2, width=300),
                    TableColumn(field='Check In Date', title='Check In Time', formatter=bigger_font, width=180),
                    TableColumn(field='Raw Time', title='Raw Time', formatter=bigger_font, width=100),
                    ]

    for name in test_names:
        col = TableColumn(field=name, title=name, formatter=color_status, width=150)
        table_columns.append(col)

    data_table = DataTable(source=td, columns=table_columns, row_height = 40, height=600, width=1800, fit_columns=False)

    w = [*widgets.values()]

    if major_type == 'HD':
        layout = row(column(row(w[0:4] + [w[-2], w[-1]]), row(w[4:10]), row(w[10:15]), row(w[15:20]), data_table))
    elif major_type == 'LD':
        layout = row(column(row(w[0:4] + [w[-2]]), row(w[4:8] + [w[-1]]), row(w[8:11]), data_table))
    else:
        layout = row(column(row(w[0:4] + [w[-2]]), row(w[4:8] + [w[-1]]), data_table))


    return json.dumps(json_item(layout))

