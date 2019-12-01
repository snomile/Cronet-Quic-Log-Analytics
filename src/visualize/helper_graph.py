import datetime

from bokeh.plotting import figure, show, save, output_file

project_root = None
filename = None
host = None

def init(root_path, filename_without_ext,host_starttime):
    global project_root,filename,host
    project_root = root_path
    filename = filename_without_ext
    host = host_starttime


def get_plot(x_label,y_label,title):
    p = figure(plot_width=1200, sizing_mode='scale_both', toolbar_location="above",
               tools='wheel_zoom,xwheel_zoom, ywheel_zoom,box_zoom,hover,box_select,reset,pan,crosshair', active_scroll="wheel_zoom")
    p.xaxis.axis_label = x_label
    p.yaxis.axis_label = y_label
    p.title.text = title + '_' + host
    return p

def display(plot):
    plot.legend.location = "top_left"
    plot.legend.click_policy = "mute"
    output_filename = datetime.datetime.now().strftime('%y%m%d_%H%M%S_') + filename + '_' + plot.title.text.replace(" ", "").lower()
    output_filepath = project_root + "/resource/html_output/%s.html" % output_filename
    output_file(output_filepath)
    print('generate html at', output_filepath)
    show(plot)