from bokeh.plotting import figure, show, save, output_file
from bokeh.models import ColumnDataSource, LabelSet

from visualize import prepare_data
from visualize.prepare_data import calculate_packet_ack_delay, calculate_packet_lost_timestamp, calculate_rtt, init, calculate_server_cfcw,calculate_client_block


def show_packet_ack_delay_all():
    packet_sent_time_sequence_list, ack_delay_total_list = calculate_packet_ack_delay()
    lost_packet_sent_time_sequence_list, lost_packet_sent_ack_delay_list = calculate_packet_lost_timestamp()
    rtt_timestamp, rtt_list = calculate_rtt()

    packet_ack_delay_source = ColumnDataSource(data={
        'Packet Sent Time Offset (ms)': packet_sent_time_sequence_list,
        'Latency (ms)': ack_delay_total_list,
        'color': ['green'] * len(packet_sent_time_sequence_list)
    })

    packet_lost_timestamp_source = ColumnDataSource(data={
        'Packet Sent Time Offset (ms)': lost_packet_sent_time_sequence_list,
        'Latency (ms)': lost_packet_sent_ack_delay_list,
        'color': ['red'] * len(lost_packet_sent_time_sequence_list)
    })

    rtt_source = ColumnDataSource(data={
        'Packet Sent Time Offset (ms)': rtt_timestamp,
        'Latency (ms)': rtt_list,
        'color': ['blue'] * len(rtt_timestamp)
    })

    p = figure(plot_width=1000, plot_height=800, toolbar_location="above",
               tools=['hover,box_select,reset,wheel_zoom,pan,crosshair'])
    p.circle_cross(x='Packet Sent Time Offset (ms)', y='Latency (ms)', source=packet_ack_delay_source, size=5,
                   alpha=0.5, color='color', legend_label='Packet', muted_color='color', muted_alpha=0.05)
    p.circle_x(x='Packet Sent Time Offset (ms)', y='Latency (ms)', source=packet_lost_timestamp_source, size=10, alpha=0.8,
               color='color', legend_label='Lost', muted_color='color', muted_alpha=0.1)
    p.square(x='Packet Sent Time Offset (ms)', y='Latency (ms)', source=rtt_source, size=4, alpha=0.8,
               color='color', legend_label='RTT', muted_color='color', muted_alpha=0.1)

    p.legend.location = "bottom_right"
    p.legend.click_policy = "mute"
    p.title.text = 'Packet ACK Delay'
    show(p)


def show_client_receive_send_data():
    p = figure(plot_width=1000, plot_height=800, toolbar_location="above", tools='wheel_zoom,hover,box_select,reset,pan,crosshair',active_scroll="wheel_zoom")

    #dns
    dns_source = prepare_data.get_dns_source()
    p.circle("x", "y", source=dns_source,size=12,color='pink', line_color="black", fill_alpha=0.7,legend_label='DNS', muted_color='pink', muted_alpha=0.05)
    dns_labels = LabelSet(x="x", y="y", text="name", y_offset=8,text_font_size="8pt", text_color="#555555", source= dns_source, text_align='center')
    p.add_layout(dns_labels)

    #client send packet
    packet_send_source = prepare_data.get_packet_send_source()
    p.circle_cross(x='x', y='y', source=packet_send_source, size=5,
                   alpha=0.8, color='navy', legend_label='Packet Sent', muted_color='navy', muted_alpha=0.05)
    p.line(x='x', y='y', source=packet_send_source,line_width=2,
                   alpha=0.4, color='navy', legend_label='Send Size', muted_color='navy', muted_alpha=0.05)
    y_range_max_packet_send = packet_send_source.data['y'][-1]

    #server cfcw
    server_cfcw_source = prepare_data.get_server_cfcw_source()
    y_range_max_server_cfcw = server_cfcw_source.data['y'][-1]
    if y_range_max_server_cfcw <= y_range_max_packet_send*2:  #TODO use window_update event to determain if display the graph
        p.line(x='x', y='y', source=server_cfcw_source, line_width=2,alpha=0.5,
                    color='blue', legend_label='Server CFCW', muted_color='blue', muted_alpha=0.05)

    #client send block
    client_send_block_source = prepare_data.get_client_block_connection_level_source()
    p.circle(x='x', y='y', source=client_send_block_source,size=12,color='color', line_color="black", fill_alpha=0.7,legend_label='Client Send Block', muted_color='pink', muted_alpha=0.05)
    client_send_block_labels = LabelSet(x="x", y="y", text="stream_id", y_offset=8,text_font_size="8pt", text_color="#555555", source= client_send_block_source, text_align='center')
    p.add_layout(client_send_block_labels)

    #client congestion


    #client receive
    packet_receive_source = prepare_data.get_packet_receive_source()
    p.circle_cross(x='x', y='y', source=packet_receive_source, size=5,
                   alpha=0.8, color='red', legend_label='Packet Received', muted_color='red', muted_alpha=0.05)
    p.line(x='x', y='y', source=packet_receive_source,line_width=2,
                   alpha=0.4, color='red', legend_label='Receive Size', muted_color='brown', muted_alpha=0.05)
    y_range_max_packet_receive = packet_receive_source.data['y'][-1]

    #client cfcw, if the cfcw wasn't a problem ,then no need to display
    client_cfcw_source = prepare_data.get_client_cfcw_source()
    y_range_max_client_cfcw = client_cfcw_source.data['y'][-1]
    if y_range_max_client_cfcw <= y_range_max_packet_receive*2: #TODO use window_update event to determain if display the graph
        p.line(x='x', y='y', source=client_cfcw_source, line_width=2,alpha=0.5,
                    color='blue', legend_label='Client CFCW', muted_color='blue', muted_alpha=0.05)

    #legend
    p.legend.location = "top_left"
    p.legend.click_policy = "mute"
    p.xaxis.axis_label = 'Time Since Request Begin (ms)'
    p.yaxis.axis_label = 'Traffic Size (KB)'
    p.title.text = 'Client CFCW and Received Size'

    output_file("../test/graph.html")
    show(p)  # save(p)


if __name__ == '__main__':
    init("../data_converted/netlog-1_quic_connection.json")
    #init("../data_converted/quic-gh2ir_quic_connection.json")

    #show_packet_ack_delay_all()
    show_client_receive_send_data()
