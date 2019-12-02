import pandas as pd
from bokeh.plotting import figure,show
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.plotting import figure, show, output_file
from bokeh.sampledata.periodic_table import elements

if __name__ == '__main__':
    source = ColumnDataSource(data={
        'x': [1,3,2,4],
        'y': [1,3,2,4]
    })
    # 转化为ColumnDataSource对象
    # 这里注意了，index和columns都必须有名称字段

    p = figure(plot_width=600, plot_height=400)
    p.line(x='x', y='y', source=source,  # 设置x，y值, source → 数据源
           line_width=1, line_alpha=0.8, line_color='black', line_dash=[10, 4])  # 线型基本设置
    # 绘制折线图
    p.circle(x='x', y='y', source=source,size=2, color='red', alpha=0.8)

    output_file("../test/graph.html")
    show(p)