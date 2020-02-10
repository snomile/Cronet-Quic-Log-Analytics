import datetime
from bokeh.plotting import figure, show, save, output_file
import warnings
warnings.filterwarnings('ignore')

html_output_path = None
filename = None
host = None

def init(output_path, filename_without_ext,host_starttime):
    global html_output_path,filename,host
    html_output_path = output_path
    filename = filename_without_ext
    host = host_starttime


def get_plot(x_label,y_label,title):
    p = figure(plot_width=1200, sizing_mode='scale_both', toolbar_location="above",
               tools='wheel_zoom,xwheel_zoom, ywheel_zoom,box_zoom,hover,box_select,reset,pan,crosshair', active_scroll="wheel_zoom")
    p.xaxis.axis_label = x_label
    p.yaxis.axis_label = y_label
    p.title.text = host + '_' + title

    # print('title: ',title)
    # print('host: ',host)

    return p

def display(plot):
    plot.legend.location = "top_left"
    plot.legend.click_policy = "mute"
    safe_filename = filename.replace(':','_')  # convert : to _ to avoid corrupting the file system

    output_filename = safe_filename + '_' + plot.title.text.replace(" ", "").lower()

    # print('plot title: ', plot.title.text.replace(" ", "").lower())
    # print('safe filename: ', safe_filename)
    # print('html output path: ', html_output_path)

    output_filepath = "%s/%s.html" % (html_output_path,output_filename)
    output_file(output_filepath)
    print('generate html at', output_filepath)
    show(plot)