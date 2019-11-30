Cronet log is important for QUIC client and server developers, which including detailed Quic Connection/Stream/Frame logs.

But reading the log by netlog-viewer(https://netlog-viewer.appspot.com/) is painful, so I decided to make my own tool to speed up the process.

By this tool, you can
1) read cronet log on the packet/frame/stream level, each packet would be tagged by important info(eg. ack_delay, if_lost, etc.), along with the content of the packet itself.
2) track the client/server CFCW/SFCW/Window_Update/Block related frames, which would be hlepful for analyzing the bottleneck of the throughput.
3) use the interactive diagram to go through every details of the quic session, including DNS time cost, handshake time cost, which packet is lost, packet size inflight......

Usage:
1) clone the project to a linux desktop environment with browser installed(Chrome/Firefox/...)
2) enter src directory with terminal, pip3 install -r requirements.txt
3) use "python3 cronet_log_analyze.py $path_to_cronet_log.json" to process log files, browser will open automatically when processing ends. if doesn't, the html files would be under cronet_quic_log_analytics/resource/html_output, open them with your favorite browser



![image](https://github.com/snomile/Cronet-Quic-Log-Analytics/blob/master/resource/doc/packet_traffic_analyze.png)
![image](https://github.com/snomile/Cronet-Quic-Log-Analytics/blob/master/resource/doc/massive_send.png)
![image](https://github.com/snomile/Cronet-Quic-Log-Analytics/blob/master/resource/doc/block.png)
![image](https://github.com/snomile/Cronet-Quic-Log-Analytics/blob/master/resource/doc/packet_size_inflight.png)