from bokeh.models import LabelSet

from visualize import helper_data
from visualize.helper_graph import *


def show():
    p = get_plot('Time Since Request Begin (ms)','Traffic Size (KB)','Packet Traffic')
    p.hover.tooltips = [
        ('time', '@x'),
        ('size', '@y'),
        ('packet number', '@number'),
        ('ack_delay', '@ack_delay'),
        ('info', '@info')
    ]
    p.hover.mode = 'mouse'

    #dns
    dns_source = helper_data.get_dns_source()
    p.circle("x", "y", source=dns_source,size=12,color='pink', line_color="black", fill_alpha=0.7,legend_label='DNS', muted_color='pink', muted_alpha=0.05)
    dns_labels = LabelSet(x="x", y="y", text="name", y_offset=8,text_font_size="8pt", text_color="#555555", source= dns_source, text_align='center')
    p.add_layout(dns_labels)

    #client send packet
    packet_send_source = helper_data.get_packet_send_source()
    p.line(x='x', y='y', source=packet_send_source,line_width=2,
                   alpha=0.4, color='navy', legend_label='Total Send Size', muted_color='navy', muted_alpha=0.05)
    p.circle(x='x', y='y', source=packet_send_source, size='size', #'ack_delay',
                   alpha=0.8, color='color', line_color="black", legend_label='Packet Sent(size means ack delay)', muted_color='color', muted_alpha=0.05)
    packet_send_labels = LabelSet(x="x", y="y", text="tag", y_offset=8,text_font_size="8pt", text_color="#555555", source= packet_send_source, text_align='center')
    p.add_layout(packet_send_labels)
    y_range_max_packet_send = packet_send_source.data['y'][-1]

    #server cfcw
    server_cfcw_source = helper_data.get_server_cfcw_source()
    y_range_max_server_cfcw = server_cfcw_source.data['y'][-1]
    if y_range_max_server_cfcw <= y_range_max_packet_send*2:  #TODO use window_update event to determain if display the graph
        p.line(x='x', y='y', source=server_cfcw_source, line_width=2,alpha=0.5,
                    color='blue', legend_label='Server CFCW', muted_color='blue', muted_alpha=0.05)

    #client send block
    client_send_block_source = helper_data.get_client_block_connection_level_source()
    p.circle(x='x', y='y', source=client_send_block_source,size=12,color='color', line_color="black", fill_alpha=0.7,legend_label='Client Send Block', muted_color='pink', muted_alpha=0.05)
    client_send_block_labels = LabelSet(x="x", y="y", text="stream_id", y_offset=8,text_font_size="8pt", text_color="#555555", source= client_send_block_source, text_align='center')
    p.add_layout(client_send_block_labels)

    #client congestion

    #client send close
    client_send_connection_close_source = helper_data.get_client_send_connection_close_source()
    p.circle("x", "y", source=client_send_connection_close_source, size=12, color='brown', line_color="black", fill_alpha=0.7, legend_label='Connection Close',
             muted_color='pink', muted_alpha=0.05)
    send_connection_close_labels = LabelSet(x="x", y="y", text="name", y_offset=8, text_font_size="8pt", text_color="#555555",
                          source=client_send_connection_close_source, text_align='center')
    p.add_layout(send_connection_close_labels)


    #client receive
    packet_receive_source = helper_data.get_packet_receive_source()
    p.line(x='x', y='y', source=packet_receive_source,line_width=2,
                   alpha=0.4, color='green', legend_label='Total Receive Size', muted_color='green', muted_alpha=0.05)
    p.circle(x='x', y='y', source=packet_receive_source, size=5,
                   alpha=0.8, color='color', line_color="black", legend_label='Packet Received', muted_color='color', muted_alpha=0.05)
    packet_receive_labels = LabelSet(x="x", y="y", text="tag", y_offset=8,text_font_size="8pt", text_color="#555555", source= packet_receive_source, text_align='center')
    p.add_layout(packet_receive_labels)
    y_range_max_packet_receive = packet_receive_source.data['y'][-1]

    #client cfcw, if the cfcw wasn't a problem ,then no need to display
    client_cfcw_source = helper_data.get_client_cfcw_source()
    y_range_max_client_cfcw = client_cfcw_source.data['y'][-1]
    if y_range_max_client_cfcw <= y_range_max_packet_receive*2: #TODO use window_update event to determain if display the graph
        p.line(x='x', y='y', source=client_cfcw_source, line_width=2,alpha=0.5,
                    color='blue', legend_label='Client CFCW', muted_color='blue', muted_alpha=0.05)

    display(p)
