from visualize import helper_data
from visualize.helper_graph import *


def show():
    packet_size_inflight_source = helper_data.get_packet_size_inflight()

    p = get_plot('Time Since Request Begin (ms)', 'Packet Size Inflight (KB)', 'Packet Size Inflight')
    p.line(x='x', y='y', source=packet_size_inflight_source,line_width=2,
                   alpha=0.8, color='green', legend_label='Packet Size Inflight', muted_color='green', muted_alpha=0.05)
    display(p)