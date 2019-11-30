from bokeh.plotting import figure, show, save, output_file

project_root = None
filename = None

def init(root_path, filename_without_ext):
    global project_root,filename
    project_root = root_path
    filename = filename_without_ext


def get_plot(x_label,y_label,title):
    p = figure(plot_width=1200, sizing_mode='scale_both', toolbar_location="above",
               tools='wheel_zoom,hover,box_select,reset,pan,crosshair', active_scroll="wheel_zoom")
    p.xaxis.axis_label = x_label
    p.yaxis.axis_label = y_label
    p.title.text = title
    return p

def display(plot):
    plot.legend.location = "top_left"
    plot.legend.click_policy = "mute"
    output_filename = filename + '_' + plot.title.text.replace(" ", "").lower()
    output_file(project_root + "/resource/html_output/%s.html" % output_filename)
    show(plot)