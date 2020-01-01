from bokeh.models import LabelSet

from visualize import helper_data
from visualize.helper_graph import *


def show(show_all_packet_info):
    p = get_plot('Time Since Request Begin (ms)','Packet Number','Packet Number Traffic')
    p.hover.tooltips = [
        ('time', '@x'),
        ('size', '@y'),
        ('time_h', '@time_h'),
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
    packet_send_line_source, packet_send_source, packet_send_chlo_source = helper_data.get_packet_send_source(show_all_packet_info)
    p.circle(x='x', y='number', source=packet_send_chlo_source, size='size',
                   alpha=0.8, color='color', line_color="black", legend_label='CHLO', muted_color='color', muted_alpha=0.05)
    packet_send_labels = LabelSet(x="x", y="number", text="tag", y_offset=8,text_font_size="8pt", text_color="#555555", source= packet_send_chlo_source, text_align='center')
    p.add_layout(packet_send_labels)
    p.line(x='x', y='number', source=packet_send_source,line_width=2,alpha=0.4, color='navy', legend_label='Packet Number', muted_color='navy', muted_alpha=0.05)
    p.circle(x='x', y='number', source=packet_send_source, size='size',alpha=0.8, color='color', line_color="black", legend_label='Packet Sent(size means ack delay)', muted_color='color', muted_alpha=0.05)
    packet_send_labels = LabelSet(x="x", y="number", text="tag", y_offset=8,text_font_size="8pt", text_color="#555555", source= packet_send_source, text_align='center')
    p.add_layout(packet_send_labels)


    #client send block
    client_send_block_source = helper_data.get_client_block_connection_level_source()
    p.circle(x='x', y='y', source=client_send_block_source,size=12,color='color', line_color="black", fill_alpha=0.7,legend_label='Client Send Block', muted_color='pink', muted_alpha=0.05)
    client_send_block_labels = LabelSet(x="x", y="y", text="stream_id", y_offset=8,text_font_size="8pt", text_color="#555555", source= client_send_block_source, text_align='center')
    p.add_layout(client_send_block_labels)

    #client congestion

    #client ack size #TODO ack number
    # ack_size_source = helper_data.get_ack_size_source()
    # p.line(x='x', y='y', source=ack_size_source, line_width=2, alpha=0.4, color='deepskyblue',
    #        legend_label='Total Acked Send Size', muted_color='deepskyblue', muted_alpha=0.05)

    #connection close_frame
    client_send_connection_close_source = helper_data.get_connection_close_source()
    p.circle("x", "y", source=client_send_connection_close_source, size=12, color='brown', line_color="black", fill_alpha=0.7, legend_label='Connection Close',
             muted_color='pink', muted_alpha=0.05)
    send_connection_close_labels = LabelSet(x="x", y="y", text="name", y_offset=8, text_font_size="8pt", text_color="#555555",
                          source=client_send_connection_close_source, text_align='center')
    p.add_layout(send_connection_close_labels)


    if len(helper_data.packet_received_dict) > 0:  #in case of there're no received packet
        # client receive graph
        packet_receive_line_source, packet_receive_source, packet_receive_shlo_source = helper_data.get_packet_receive_source(show_all_packet_info)
        p.line(x='x', y='number', source=packet_receive_source,line_width=2,
                       alpha=0.4, color='green', legend_label='Total Receive Size', muted_color='green', muted_alpha=0.05)
        p.circle(x='x', y='number', source=packet_receive_shlo_source, size='size',
                 alpha=0.8, color='color', line_color="black", legend_label='SHLO', muted_color='color', muted_alpha=0.05)
        packet_send_labels = LabelSet(x="x", y="number", text="tag", y_offset=8, text_font_size="8pt", text_color="#555555",
                                      source=packet_receive_shlo_source, text_align='center')
        p.add_layout(packet_send_labels)
        p.circle(x='x', y='number', source=packet_receive_source, size='size',
                       alpha=0.8, color='color', line_color="black", legend_label='Packet Received', muted_color='color', muted_alpha=0.05)
        packet_receive_labels = LabelSet(x="x", y="number", text="tag", y_offset=8,text_font_size="8pt", text_color="#555555", source= packet_receive_source, text_align='center')
        p.add_layout(packet_receive_labels)

    display(p)
