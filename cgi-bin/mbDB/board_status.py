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
    Slider,
    DataTable,
    DateFormatter,
    TableColumn,
    Select,
    Label,
    Text,
)
from bokeh.embed import json_item
from bokeh.palettes import d3, brewer
from bokeh.layouts import column, row
import json
import makeTestingData as mTD

ds = mTD.get_status_over_time()

colors = [
        d3['Category10'][10][0],
        d3['Category10'][10][1],
        d3['Category10'][10][7],
        d3['Category10'][10][8],
        d3['Category10'][10][2],
        d3['Category10'][10][3],
        ]

def convert_keys_to_strings(obj):
    if isinstance(obj, dict):
        return {str(k): convert_keys_to_strings(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_keys_to_strings(item) for item in obj]
    else:
        return obj

ds = convert_keys_to_strings(ds)

def TotalPlot(data, mc_widgets, widgets):
    data_total = ColumnDataSource(data={'dates':[], 'counts':[]})
    data_notreg = ColumnDataSource(data={'dates':[], 'counts':[]})
    data_failed = ColumnDataSource(data={'dates':[], 'counts':[]})
    data_passed = ColumnDataSource(data={'dates':[], 'counts':[]})
    data_shipped = ColumnDataSource(data={'dates':[], 'counts':[]})
    data_inprog = ColumnDataSource(data={'dates':[], 'counts':[]})

    x = CustomJS(args=dict(data_failed=data_failed, data_total=data_total, data_notreg=data_notreg, data_passed=data_passed, data_shipped=data_shipped, data_inprog=data_inprog, data=data, mc_widgets=mc_widgets),code='''
const dates = []
const tsd_failed = []
const tsd_passed = []
const tsd_shipped = []
const tsd_inprog = []
const tsd_notreg = []
const tsd_total = []

const is_selected_map = new Map([
    ["multi_choice", (wi, pos, el, idx) => wi.value.includes(el)],
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

const days = Array.from(Object.keys(data));
for (let d = 0; d < days.length; d++) {
    let total = 0;
    let awaiting = 0;
    let notreg = 0;
    let passed = 0;
    let shipped = 0;
    let failed = 0;
    const majors = Array.from(Object.keys(data[days[d]]));
    for (let m = 0; m < majors.length; m++) {
        if (passed_vals.get('Major Type').get(majors[m]) == true) {
            const subs = Array.from(Object.keys(data[days[d]][majors[m]]))
            for (let s = 0; s < subs.length; s++) {
                if (passed_vals.get('Sub Type').get(subs[s]) == true) {
                    if (data[days[d]][majors[m]][subs[s]]['Total']) {
                        total = total + data[days[d]][majors[m]][subs[s]]['Total']
                    }
                    if (data[days[d]][majors[m]][subs[s]]['Awaiting Testing']) {
                        awaiting = awaiting + data[days[d]][majors[m]][subs[s]]['Awaiting Testing']
                    }
                    if (data[days[d]][majors[m]][subs[s]]['Passed QC, Awaiting Registration']) {
                        notreg = notreg + data[days[d]][majors[m]][subs[s]]['Passed QC, Awaiting Registration']
                    }
                    if (data[days[d]][majors[m]][subs[s]]['Ready for Shipping']) {
                        passed = passed + data[days[d]][majors[m]][subs[s]]['Ready for Shipping']
                    }
                    if (data[days[d]][majors[m]][subs[s]]['Shipped']) {
                        shipped = shipped + data[days[d]][majors[m]][subs[s]]['Shipped']
                    }
                    if (data[days[d]][majors[m]][subs[s]]['Failed QC']) {
                        failed = failed + data[days[d]][majors[m]][subs[s]]['Failed QC']
                    }
                }
            }
        }
    }
    dates.push(Date.parse(days[d]))
    tsd_failed.push(failed)
    tsd_passed.push(passed)
    tsd_shipped.push(shipped)
    tsd_inprog.push(awaiting)
    tsd_notreg.push(notreg)
    tsd_total.push(total)
}
data_total.data['dates'] = dates;
data_total.data['counts'] = tsd_total;
data_total.change.emit()

data_notreg.data['dates'] = dates;
data_notreg.data['counts'] = tsd_notreg;
data_notreg.change.emit()

data_failed.data['dates'] = dates;
data_failed.data['counts'] = tsd_failed;
data_failed.change.emit()

data_passed.data['dates'] = dates;
data_passed.data['counts'] = tsd_passed;
data_passed.change.emit()

data_shipped.data['dates'] = dates;
data_shipped.data['counts'] = tsd_shipped;
data_shipped.change.emit()

data_inprog.data['dates'] = dates;
data_inprog.data['counts'] = tsd_inprog;
data_inprog.change.emit()
''')
    for widget in widgets.values():
        widget.js_on_change('value', x)
    return data_total, data_inprog, data_notreg, data_passed, data_shipped, data_failed

def Filter():
    mc_widgets = {}
    multi_choice = (lambda x,y: MultiChoice(options=x, value=[], title=y), 'value')
    columns = ['Major Type', 'Sub Type']

    majors = list(ds[list(ds.keys())[-1]].keys())
    all_subtypes = []
    subtypes = {}
    for m in majors:
        subtypes[m] = list(ds[list(ds.keys())[-1]][m].keys())
        for s in subtypes[m]:
            all_subtypes.append(s)

    data = [majors, all_subtypes]
    t = [multi_choice, multi_choice]

    p = figure(
        title='Board Status Over Time',
        x_axis_label='Date',
        y_axis_label='',
        tools='pan,wheel_zoom,box_zoom,reset,save',
        width = 925,
        x_axis_type='datetime',
        )

    for i in range(len(columns)):
        widget_constructor, trigger = t[i]
        if t[i] == multi_choice:
            possible_vals = np.unique(data[i]).tolist()
            widget = widget_constructor(possible_vals, columns[i])
            typ = 'multi_choice'
            mc_widgets[columns[i]] = {
                'type': typ,
                'possible_vals': possible_vals,
                'widget': widget,}

    widgets = {k:w['widget'] for k,w in mc_widgets.items()}
    data_total, data_awaiting, data_notreg, data_passed, data_shipped, data_failed = TotalPlot(ds, mc_widgets, widgets)

    p.line('dates', 'counts', source=data_total, legend_label='Total Received', color=colors[0], line_width=2, muted_alpha=0.2)
    p.line('dates', 'counts', source=data_awaiting, legend_label='Awaiting Testing', color=colors[1], line_width=2, muted_alpha=0.2)
    p.line('dates', 'counts', source=data_notreg, legend_label='Awaiting Registration', color=colors[2], line_width=2, muted_alpha=0.2)
    p.line('dates', 'counts', source=data_passed, legend_label='Passed QC', color=colors[3], line_width=2, muted_alpha=0.2)
    p.line('dates', 'counts', source=data_shipped, legend_label='Shipped', color=colors[4], line_width=2, muted_alpha=0.2)
    p.line('dates', 'counts', source=data_failed, legend_label='Failed QC', color=colors[5], line_width=2, muted_alpha=0.2)

    p.legend.click_policy='hide'
    p.legend.label_text_font_size = '8pt'
    p.legend.location = 'top_left'
    w = [*widgets.values()]


    update_options = CustomJS(args=dict(subtypes=subtypes, widget=w[1], all_subtypes=all_subtypes), code=('''
if (this.value.length != 0) {
    widget.options = subtypes[this.value]
} else {
    widget.options = all_subtypes
}
'''))
    w[0].js_on_change('value', update_options)
    

    plot_json = json.dumps(json_item(column(row(w), p)))
    return plot_json

