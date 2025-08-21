#!./cgi_runner.sh

import cgi, html
import base
import sys
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


BoardData = pd.read_csv(mTD.get_board())
PeopleData = pd.read_csv(mTD.get_people())
check_out = pd.read_csv(mTD.get_check_out(), parse_dates=['Time'])
mergetemp = check_out.merge(BoardData, on='Board ID', how='left')
AllData = mergetemp.merge(PeopleData, on='Person ID', how='left')
AllData.dropna()

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
const d_keys = Array.from(dates.get('Shipped After').keys());
let start_date = 0;
let end_date = 0;
for (let i = 0; i < d_keys.length; i++) {
    if (dates.get('Shipped After').get(d_keys[i]) == true) {
        let sd = d_keys[i];
        start_date = new Date(sd);
    }
    if (dates.get('End Date').get(d_keys[i]) == true) {
        let ed = d_keys[i];
        end_date = new Date(ed);
    }
}
for (let i = 0; i < source.get_length(); i++) {
    if (source.data['Time'][i] >= start_date && indices[i] == true) {
        indices[i] = true;
    } else {
        indices[i] = false;
    }
}
return indices;

''')

def makeTable(ds, widgets, view):
    td = ColumnDataSource({'Sub Type':[], 'Full ID':[], 'Person':[], 'Date':[], 'Location':[], 'Raw Time':[]})

    x = CustomJS(args=dict(td=td, data=ds, view=view),code='''
const type_ids=[];
const full_ids=[];
const people=[];
const times=[];
const locations=[];
const raw_time=[];

const indices = view.filters[0].compute_indices(data);
let mask = new Array(data.data['Full ID'].length).fill(false);
[...indices].forEach((x)=>{mask[x] = true;})

for (let j = 0; j < data.get_length(); j++) {
    if (mask[j] == true){
        type_ids.push(data.data['Sub Type'][j])
        full_ids.push(data.data['Full ID'][j])
        people.push(data.data['Person Name'][j])
    
        // converts date to a readable format
        let temp_date = new Date(data.data['Time'][j] + 21600000);
        let date = temp_date.toString().slice(4, 24)
        times.push(date)
        raw_time.push(temp_date.valueOf())

        locations.push(data.data['Shipping Location'][j])
    }
}
td.data['Sub Type'] = type_ids;
td.data['Full ID'] = full_ids;
td.data['Person'] = people;
td.data['Date'] = times;
td.data['Raw Time'] = raw_time;
td.data['Location'] = locations;
td.change.emit()
''')

    for widget in widgets.values():
        widget.js_on_change('value', x)

    return td

def Filter():
    ds = ColumnDataSource(AllData.dropna())
    df = AllData.dropna()

    # create the widgets to be used
    mc_widgets = {}
    dr_widgets = {}
    multi_choice = (lambda x,y: MultiChoice(options=x, value=[], title=y), 'value')
    start_date = (lambda x,y,z: DatePicker(min_date=x,max_date=y, value=x, title=z), 'value')
    today = datetime.date.today()
    today_plus_one = today + datetime.timedelta(days=1)
    end_date = (lambda x,y,z: DatePicker(min_date=x,max_date=y, value=today_plus_one, title=z), 'value')
    min_date = pd.Timestamp((min(ds.data['Time']))).date()
    date_range = []
    while min_date <= today_plus_one:
        date_range.append(min_date)
        min_date += datetime.timedelta(days=1)
    # widget titles and data for those widgets has to be manually entered, as well as the type
    columns = ['Major Type', 'Sub Type', 'Shipping Location', 'Person Name', 'Shipped After', 'End Date']
    data = [ds.data['Major Type'].tolist(), ds.data['Sub Type'].tolist(), ds.data['Shipping Location'].tolist(), ds.data['Person Name'].tolist(), date_range, date_range]
    t = [multi_choice, multi_choice, multi_choice, multi_choice, start_date, end_date]

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

    td = makeTable(ds, widgets, view)
    
    # html template formatter can be used to apply typical html code to bokeh elements
    template = '''
<div style="font-size: 150%">
<%= value %>
</div> 
'''
    bigger_font = HTMLTemplateFormatter(template=template)

    link_template = '''
<div style="font-size: 150%">
<a href="get_attach.py?attach_id=<%= value %>"target="_blank">
Attach
</a>
</div> 
'''
    link = HTMLTemplateFormatter(template=link_template)

    module_template = '''
<div style="font-size: 150%">
<a href="module.py?full_id=<%= value %>"target="_blank">
<%= value %>
</a>
</div> 
'''
    board = HTMLTemplateFormatter(template=module_template)

    table_columns = [
                    TableColumn(field='Sub Type', title='Sub Type', formatter=bigger_font),
                    TableColumn(field='Full ID', title='Full ID', formatter=board),
                    TableColumn(field='Person', title='Shipped by', formatter=bigger_font),
                    TableColumn(field='Date', title='Time', formatter=bigger_font),
                    TableColumn(field='Raw Time', title='Raw Time', formatter=bigger_font),
                    TableColumn(field='Location', title='Shipped to', formatter=bigger_font),
                    ]

    data_table = DataTable(source=td, columns=table_columns, row_height = 40, autosize_mode='fit_columns', width_policy = 'fit', height=600)

    w = [*widgets.values()]

    subtypes = {}
    for major in np.unique(ds.data['Major Type'].tolist()).tolist():
        subtypes[major] = np.unique(df.query('`Major Type` == @major')['Sub Type'].values.tolist()).tolist()
    serial_numbers = {}
    for s in np.unique(ds.data['Sub Type'].tolist()).tolist():
        serial_numbers[s] = np.unique(df.query('`Sub Type` == @s')['Full ID'].values.tolist()).tolist()
    
    all_subtypes = np.unique(ds.data['Sub Type'].tolist()).tolist()
    all_serials = np.unique(ds.data['Full ID'].tolist()).tolist()

    update_options = CustomJS(args=dict(subtypes=subtypes, widget=w[1], all_subtypes=all_subtypes), code=('''
if (this.value.length != 0) {
    widget.options = subtypes[this.value]
} else {
    widget.options = all_subtypes
}
'''))
    w[0].js_on_change('value', update_options)
    
    return json.dumps(json_item(row(column(row(w[0:5]), data_table))))


print("Content-type: text/html\n")

base.header(title='Checkout Summary')
base.top()

print('''
    <div id='exfilter' class='bk-root'></div>
    <script>
    data = {};
    Bokeh.embed.embed_item(data, 'exfilter');
    </script>
    '''.format(Filter()))

base.bottom()
