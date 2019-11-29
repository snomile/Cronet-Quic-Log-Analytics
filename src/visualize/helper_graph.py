from bokeh.plotting import figure, show, output_file

def get_plot(x_label,y_label,title):
    p = figure(plot_width=1200, plot_height=800, sizing_mode='scale_both', toolbar_location="above",
               tools='wheel_zoom,hover,box_select,reset,pan,crosshair', active_scroll="wheel_zoom")
    p.xaxis.axis_label = x_label
    p.yaxis.axis_label = y_label
    p.title.text = title
    return p

def display(plot):
    plot.legend.location = "top_left"
    plot.legend.click_policy = "mute"
    output_file("../test/graph.html")
    show(plot)