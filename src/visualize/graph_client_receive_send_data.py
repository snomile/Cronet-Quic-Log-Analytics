from bokeh.models import LabelSet

from visualize import helper_data
from visualize.helper_graph import *


def show():
    p = get_plot('Time Since Request Begin (ms)','Traffic Size (KB)','Packet Traffic')
    p.hover.tooltips = [
        ('time', '@x'),
        ('y', '@y'),
        ('packet number', '@number'),
        ('ack_delay', '@ack_delay'),
        ('frame', '@frame')
    ]

    #dns
    dns_source = helper_data.get_dns_source()
    p.circle("x", "y", source=dns_source,size=12,color='pink', line_color="black", fill_alpha=0.7,legend_label='DNS', muted_color='pink', muted_alpha=0.05)
    dns_labels = LabelSet(x="x", y="y", text="name", y_offset=8,text_font_size="8pt", text_color="#555555", source= dns_source, text_align='center')
    p.add_layout(dns_labels)

    #handshake
    handshake_source = helper_data.get_handshake_source()
    p.circle("x", "y", source=handshake_source,size=12,color='yellow', line_color="black", fill_alpha=0.7,legend_label='Handshake', muted_color='yellow', muted_alpha=0.05)
    dns_labels = LabelSet(x="x", y="y", text="actions", y_offset=8,text_font_size="8pt", text_color="#555555", source= handshake_source, text_align='center')
    p.add_layout(dns_labels)

    #client send packet
    packet_send_source, packet_lost_source = helper_data.get_packet_send_source()
    p.circle_cross(x='x', y='y', source=packet_send_source, size='size', #'ack_delay',
                   alpha=0.8, color='navy', legend_label='Packet Sent(size means ack delay)', muted_color='navy', muted_alpha=0.05)
    p.line(x='x', y='y', source=packet_send_source,line_width=2,
                   alpha=0.4, color='navy', legend_label='Total Send Size', muted_color='navy', muted_alpha=0.05)
    y_range_max_packet_send = packet_send_source.data['y'][-1]

    #client send packet lost
    p.circle_cross(x='x', y='y', source=packet_lost_source, size='size',
                   alpha=1, color='red', legend_label='Packet Sent Lost', muted_color='red', muted_alpha=0.05)

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


    #client receive
    packet_receive_source = helper_data.get_packet_receive_source()
    p.circle_cross(x='x', y='y', source=packet_receive_source, size=5,
                   alpha=0.8, color='green', legend_label='Packet Received', muted_color='green', muted_alpha=0.05)
    p.line(x='x', y='y', source=packet_receive_source,line_width=2,
                   alpha=0.4, color='green', legend_label='Total Receive Size', muted_color='green', muted_alpha=0.05)
    y_range_max_packet_receive = packet_receive_source.data['y'][-1]

    #client cfcw, if the cfcw wasn't a problem ,then no need to display
    client_cfcw_source = helper_data.get_client_cfcw_source()
    y_range_max_client_cfcw = client_cfcw_source.data['y'][-1]
    if y_range_max_client_cfcw <= y_range_max_packet_receive*2: #TODO use window_update event to determain if display the graph
        p.line(x='x', y='y', source=client_cfcw_source, line_width=2,alpha=0.5,
                    color='blue', legend_label='Client CFCW', muted_color='blue', muted_alpha=0.05)

    display(p)
