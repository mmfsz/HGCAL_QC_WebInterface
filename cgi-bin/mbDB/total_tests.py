#!./cgi_runner.sh

# framework for creating dynamic plots
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
    NumericInput,
)
from bokeh.embed import json_item
from bokeh.palettes import d3, brewer
from bokeh.layouts import column, row
import json
import makeTestingData as mTD

#import all data from csv files and set it up properly
TestData = pd.read_csv(mTD.get_test(), parse_dates=['Time'])
BoardData = pd.read_csv(mTD.get_board())
PeopleData = pd.read_csv(mTD.get_people())
TestTypeData = pd.read_csv(mTD.get_test_types())
TestTypeData = TestTypeData.rename(columns={'Name':'Test Name'})
mergetemp = TestData.merge(BoardData, on='Board ID', how='left')
AllData = mergetemp.merge(PeopleData, on='Person ID', how='left')
AllData = AllData.rename(columns={'Successful':'Outcome'})
AllData['Outcome'] = AllData['Outcome'].replace(0, 'Unsuccessful')
AllData['Outcome'] = AllData['Outcome'].replace(1, 'Successful')
AllData = AllData.merge(TestTypeData, on='Test Type ID', how='left')

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
const d_keys = Array.from(dates.get('Start Date').keys());
let start_date = 0;
let end_date = 0;
for (let i = 0; i < d_keys.length; i++) {
    if (dates.get('Start Date').get(d_keys[i]) == true) {
        let sd = d_keys[i];
        start_date = new Date(sd);
    }
    if (dates.get('End Date').get(d_keys[i]) == true) {
        let ed = d_keys[i];
        end_date = new Date(ed);
        end_date = new Date(end_date.setDate(end_date.getDate() + 1));
    }
}
for (let i = 0; i < source.get_length(); i++) {
    if (source.data['Time'][i] >= start_date && source.data['Time'][i] <= end_date && indices[i] == true) {
        indices[i] = true;
    } else {
        indices[i] = false;
    }
}
return indices;

''')

#create a color pallete to be used on graphs
colors = [d3['Category10'][10][0], d3['Category10'][10][1], d3['Category10'][10][2], d3['Category10'][10][3], d3['Category10'][10][4], d3['Category10'][10][5], d3['Category10'][10][6], d3['Category10'][10][7], d3['Category10'][10][8], d3['Category10'][10][9], brewer['Accent'][8][0], brewer['Accent'][8][3], brewer['Dark2'][8][0], brewer['Dark2'][8][2], brewer['Dark2'][8][3], brewer['Dark2'][8][4], brewer['Dark2'][8][5], brewer['Dark2'][8][6]]

def TotalPlot(data, view, widgets, date_range, modules):
    # a data source for each
    time_series_data_total = ColumnDataSource(data={'dates':[], 'counts':[]})
    time_series_data_suc = ColumnDataSource(data={'dates':[], 'counts':[]})
    time_series_data_unc = ColumnDataSource(data={'dates':[], 'counts':[]})
    dt = ColumnDataSource(data={'dates':[], 'total_counts':[], 'suc_counts':[], 'unc_counts':[]})
    x = CustomJS(args=dict(tsd_total=time_series_data_total, tsd_suc=time_series_data_suc, tsd_unc=time_series_data_unc, data=data, view=view, date_range=date_range, modules=modules, dt=dt),code='''
// goes through the modules case by case
console.log(data.data)
for (let t = 0; t < modules.length; t++) {
    if (modules[t] == 'Total') {
        const indices = view.filters[0].compute_indices(data);
        let mask = new Array(data.data['Test ID'].length).fill(false);
        [...indices].forEach((x)=>{mask[x] = true;})
        let count = 0;
        const dates = [];
        const counts = [];
        // iterate over all data points
        // by incorporating this mask, it allows the data to be filtered properly by the date range widget
        for (let m = 0; m < mask.length; m++) {
            if (mask[m] ==  true) {
                // get date of current index
                let temp_date = new Date(data.data['Time'][m]);
                let new_date = temp_date.toLocaleDateString();
                let date = new Date(new_date);
                // convert to central time
                if (String(date).includes('Daylight')) {
                    date = new Date(date.setHours(date.getHours() - 5));
                } else {
                    date = new Date(date.setHours(date.getHours() - 6));
                }
                // iterate over all days within range
                for (let i = 0; i < date_range.length; i++) {
                    // create a date range of one day
                    let day0 = new Date(date_range[i]);
                    let day1 = new Date(date_range[i]);
                    day1 = new Date(day1.setDate(day1.getDate() + 1));
                    // check if date of data point is before iterated date
                    if (day0 >= date) {
                        // if so, check all data points that have occured on this day
                        for (let j = 0; j < mask.length; j++) {
                            if (mask[j] == true && data.data['Time'][j] >= day0 && data.data['Time'][j] <= day1){
                                count++; 
                            }
                        }
                        dates.push(day0.getTime());
                        counts.push(count);
                    }
                }
                break;
            }
        }
        tsd_total.data['dates'] = dates;
        tsd_total.data['counts'] = counts;
        tsd_total.change.emit()
    } if (modules[t] == 'Successful') {
        const indices = view.filters[0].compute_indices(data);
        let mask = new Array(data.data['Test ID'].length).fill(false);
        [...indices].forEach((x)=>{mask[x] = true;})
        for (let m = 0; m < mask.length; m++) {
            if (mask[m] == true && data.data['Outcome'][m] == modules[t]) {
                mask[m] = true;
            } else {
                mask[m] = false;
            }
        }
        let count = 0;
        const dates = [];
        const counts = [];
        for (let m = 0; m < mask.length; m++) {
            if (mask[m] ==  true) {
                let temp_date = new Date(data.data['Time'][m]);
                let new_date = temp_date.toLocaleDateString();
                let date = new Date(new_date);
                date = new Date(date.setHours(date.getHours() - 5));
                for (let i = 0; i < date_range.length; i++) {
                    let day0 = new Date(date_range[i]);
                    let day1 = new Date(date_range[i]);
                    day1 = new Date(day1.setDate(day1.getDate() + 1));
                    if (day0 >= date) {
                        for (let j = 0; j < mask.length; j++) {
                            if (mask[j] == true && data.data['Time'][j] >= day0 && data.data['Time'][j] <= day1){
                                count++; 
                            }
                        }
                        dates.push(day0.getTime());
                        counts.push(count);
                    }
                }
                break;
            }
        }
        tsd_suc.data['dates'] = dates;
        tsd_suc.data['counts'] = counts;
        tsd_suc.change.emit()
    } if (modules[t] == 'Unsuccessful') {
        const indices = view.filters[0].compute_indices(data);
        let mask = new Array(data.data['Test ID'].length).fill(false);
        [...indices].forEach((x)=>{mask[x] = true;})
        for (let m = 0; m < mask.length; m++) {
            if (mask[m] == true && data.data['Outcome'][m] == modules[t]) {
                mask[m] = true;
            } else {
                mask[m] = false;
            }
        }
        let count = 0;
        const dates = [];
        const counts = [];
        for (let m = 0; m < mask.length; m++) {
            if (mask[m] ==  true) {
                let temp_date = new Date(data.data['Time'][m]);
                let new_date = temp_date.toLocaleDateString();
                let date = new Date(new_date);
                date = new Date(date.setHours(date.getHours() - 5));
                for (let i = 0; i < date_range.length; i++) {
                    let day0 = new Date(date_range[i]);
                    let day1 = new Date(date_range[i]);
                    day1 = new Date(day1.setDate(day1.getDate() + 1));
                    if (day0 >= date) {
                        for (let j = 0; j < mask.length; j++) {
                            if (mask[j] == true && data.data['Time'][j] >= day0 && data.data['Time'][j] <= day1){
                                count++; 
                            }
                        }
                        dates.push(day0.getTime());
                        counts.push(count);
                    }
                }
                break;
            }
        }
        tsd_unc.data['dates'] = dates;
        tsd_unc.data['counts'] = counts;
        tsd_unc.change.emit()
    }
}
dt.data['dates'] = tsd_total.data['dates'];
dt.data['total_counts'] = tsd_total.data['counts'];
dt.data['suc_counts'] = tsd_suc.data['counts'];
dt.data['unc_counts'] = tsd_unc.data['counts'];
dt.change.emit()
    ''')
    for widget in widgets:
        widget.js_on_change('value', x)
    return time_series_data_total, time_series_data_suc, time_series_data_unc, dt


def Filter():
    df_temp = AllData
    df_temp = df_temp.dropna()
    ds = ColumnDataSource(df_temp)
    mc_widgets = {}
    dr_widgets = {}
    multi_choice = (lambda x,y: MultiChoice(options=x, value=[], title=y), 'value')
    start_date = (lambda x,y,z: DatePicker(min_date=x,max_date=y, value=x, title=z), 'value')
    today = datetime.date.today()
    end_date = (lambda x,y,z: DatePicker(min_date=x,max_date=y, value=today, title=z), 'value')
    min_date = pd.Timestamp((min(ds.data['Time']))).date()
    date_range = []
    while min_date <= today:
        date_range.append(min_date)
        min_date += datetime.timedelta(days=1)
    modules = ['Total', 'Successful', 'Unsuccessful']
    columns = ['Major Type', 'Sub Type', 'Full ID', 'Person Name', 'Test Name', 'Start Date', 'End Date']
    data = [ds.data['Major Type'].tolist(), ds.data['Sub Type'].tolist(), ds.data['Full ID'].tolist(), ds.data['Person Name'].tolist(), ds.data['Test Name'].tolist(), date_range, date_range]
    t = [multi_choice, multi_choice, multi_choice, multi_choice, multi_choice, start_date, end_date]

    p = figure(
        title='Total Tests Over Time',
        x_axis_label='Date',
        y_axis_label='Number of Tests',
        tools='pan,wheel_zoom,box_zoom,reset,save',
        width = 1200,
        x_axis_type='datetime',
        )

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

    custom_filter = CustomJSFilter(args=dict(mc_widgets=mc_widgets, dr_widgets=dr_widgets),code=filter_code)
    view = CDSView(source=ds, filters=[custom_filter])
    all_widgets = {**mc_widgets, **dr_widgets}
    widgets = {k:w['widget'] for k,w in all_widgets.items()}
    tsd_total, tsd_suc, tsd_unc, dt = TotalPlot(ds, view, widgets.values(), date_range, modules)
    # when items on the legend are clicked, the lines are muted instead of hidden
    p.line('dates', 'counts', source=tsd_total, legend_label=modules[0], color=colors[0], line_width=2, muted_alpha=0.2)
    p.line('dates', 'counts', source=tsd_suc, legend_label=modules[1], color=colors[2], line_width=2, muted_alpha=0.2)
    p.line('dates', 'counts', source=tsd_unc, legend_label=modules[2], color=colors[3], line_width=2, muted_alpha=0.2)
    table_columns = [
                    TableColumn(field='dates', title='Dates', formatter=DateFormatter()),
                    TableColumn(field='total_counts', title='Total Tests Completed'),
                    TableColumn(field='suc_counts', title='Successful Tests Completed'),
                    TableColumn(field='unc_counts', title='Unsuccessful Tests Completed'),
                    ]
    data_table = DataTable(source=dt, columns=table_columns, autosize_mode='fit_columns')
    p.legend.click_policy='mute'
    p.legend.label_text_font_size = '8pt'
    p.legend.location = 'top_left'
    w = [*widgets.values()]

    # update options for serial numbers upon selecting a subtype
    subtypes = {}
    for major in np.unique(ds.data['Major Type'].tolist()).tolist():
        subtypes[major] = np.unique(df_temp.query('`Major Type` == @major')['Sub Type'].values.tolist()).tolist()
    serial_numbers = {}
    for s in np.unique(ds.data['Sub Type'].tolist()).tolist():
        serial_numbers[s] = np.unique(df_temp.query('`Sub Type` == @s')['Full ID'].values.tolist()).tolist()
    
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
    
    update_options_2 = CustomJS(args=dict(serial_numbers=serial_numbers, widget=w[2], all_serials=all_serials), code=('''
if (this.value.length != 0) {
    widget.options = serial_numbers[this.value]
} else {
    widget.options = all_serials
}
'''))
    w[1].js_on_change('value', update_options_2)

    plot_json = json.dumps(json_item(column(row(w[0:3]), row(w[3:]), p, data_table)))
    return plot_json


