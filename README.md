Cronet log is important for QUIC client and server developers, which including detailed Quic Connection/Stream/Frame logs.

But reading the log by netlog-viewer(https://netlog-viewer.appspot.com/) is painful, so I decided to make my own tool to speed up the process.

By this tool, you can
1) read cronet log on the packet/frame/stream level, each packet would be tagged by important info(eg. ack_delay, if_lost, etc.), along with the content of the packet itself.
2) track the client/server CFCW/SFCW/Window_Update/Block related frames, which would be hlepful for analyzing the bottleneck of the throughput.
3) use the interactive diagram to go through every details of the quic session, including DNS time cost, handshake time cost, which packet is lost, packet size inflight......

Usage
put your cronet log under data_original, then run process_visualize.py(file_path should be match your log file name)


![image](https://github.com/snomile/Cronet-Quic-Log-Analytics/blob/master/resource/doc/packet_traffic_analyze.png)
![image](https://github.com/snomile/Cronet-Quic-Log-Analytics/blob/master/resource/doc/packet_size_inflight.png)
