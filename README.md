Cronet log is important for QUIC client and server developers, which including detailed Quic Connection/Stream/Frame logs.

But reading the log by netlog-viewer(https://netlog-viewer.appspot.com/) is painful, so I decided to make my own tool to speed up the process.

By this tool, you can
1) read QUIC client log on the packet/frame/stream level, each packet would be tagged by important info(eg. ack_delay, if_lost, etc.), along with the content of the packet itself.
2) track the handshake and client/server CFCW/SFCW related frames, which would be hlepful for analyzing the bottleneck of the throughput.


![image](http://github.com/snomile/Cronet-Quic-Log-Analytics/raw/master/resource/doc/packet_traffic_analyze.png)