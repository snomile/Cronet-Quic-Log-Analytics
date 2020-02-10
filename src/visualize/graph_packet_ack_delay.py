from bokeh.models import ColumnDataSource

from visualize.helper_data import calculate_packet_ack_delay, calculate_rtt
from visualize.helper_graph import *


def show(show_all_packet_info):
    packet_sent_time_sequence_list,ack_delay_total_list,ack_delay_server_list = calculate_packet_ack_delay()

    rtt_timestamp, rtt_list = calculate_rtt()

    packet_ack_delay_source = ColumnDataSource(data={
        'x': packet_sent_time_sequence_list,
        'y': ack_delay_total_list,
    })

    rtt_source = ColumnDataSource(data={
        'x': rtt_timestamp,
        'y': rtt_list,
    })

    p = get_plot('Time Since Request Begin (ms)','Packet ACK Delay (ms)','Packet ACK Delay')
    p.circle_cross(x='x', y='y', source=packet_ack_delay_source, size=5,
                   alpha=0.5, color='navy', legend_label='Packet Sent', muted_color='navy', muted_alpha=0.05)
    # p.circle_x(x='x', y='y', source=packet_lost_source, size=10, alpha=0.8,
    #            color='red', legend_label='Lost Packet', muted_color='red', muted_alpha=0.1)
    p.square(x='x', y='y', source=rtt_source, size=4, alpha=0.8,
               color='green', legend_label='RTT', muted_color='green', muted_alpha=0.1)

    display(p)