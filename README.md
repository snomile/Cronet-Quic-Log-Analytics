Cronet log is important for QUIC client and server developers, which including detailed Quic Connection/Stream/Frame logs.

But reading the log by netlog-viewer(https://netlog-viewer.appspot.com/) is painful, so I decided to make my own tool to speed up the process.

By this tool, you can
1) read cronet log on the packet/frame/stream level, each packet would be tagged by important info(eg. ack_delay, if_lost, etc.), along with the content of the packet itself.
2) track the client/server CFCW/SFCW/Window_Update/Block related frames, which would be hlepful for analyzing the bottleneck of the throughput.
3) use the interactive diagram to go through every details of the quic session, including DNS time cost, handshake time cost, which packet is lost, packet size inflight......

Usage
1) Use online service: https://hk.snomile.ink/cronet/, just upload the log files, and click links at the bottom of the page.
2) Host service on your own server: clone the project, enter project root, build a docker image by 'docker build -t cla .', start the docker container by 'docker run -idt --name cla -p 80:80 --restart=always cla', then access the service from http://your-ip/


![image](https://github.com/snomile/Cronet-Quic-Log-Analytics/blob/master/resource/doc/packet_traffic_analyze.png)
![image](https://github.com/snomile/Cronet-Quic-Log-Analytics/blob/master/resource/doc/massive_send.png)
![image](https://github.com/snomile/Cronet-Quic-Log-Analytics/blob/master/resource/doc/block.png)
![image](https://github.com/snomile/Cronet-Quic-Log-Analytics/blob/master/resource/doc/packet_size_inflight.png)
