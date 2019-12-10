FROM python:slim
RUN apt update; apt install wget git tar xz-utils build-essential zip unzip -y
#RUN apt install curl nano iputils-ping net-tools netcat zsh -y \
#    && chsh -s /bin/zsh \
#    && sh -c "$(curl -fsSL https://raw.github.com/robbyrussell/oh-my-zsh/master/tools/install.sh)" \
#    && cd ~ && git clone https://github.com/zsh-users/zsh-syntax-highlighting.git \
#    && echo "source ~/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" >> ~/.zshrc
RUN cd /opt && wget https://nodejs.org/dist/v12.13.1/node-v12.13.1-linux-x64.tar.xz \
	&& tar xvf node-v12.13.1-linux-x64.tar.xz \
	&& rm -f node-v12.13.1-linux-x64.tar.xz \
	&& mv node-v12.13.1-linux-x64 nodejs \
	&& ln -s /opt/nodejs/bin/node /usr/local/bin/node \
	&& ln -s /opt/nodejs/bin/npm /usr/local/bin/npm
RUN mkdir /opt/cla \
	&& cd /opt/cla \
	&& git clone https://github.com/snomile/Cronet-Quic-Log-Analytics.git
RUN pip install Cython && \
	pip install numpy && \
	pip install scikit-learn && \
    pip install bokeh
RUN cd /opt/cla/Cronet-Quic-Log-Analytics/server && npm i

ENTRYPOINT ["/bin/sh", "/opt/cla/Cronet-Quic-Log-Analytics/server/startup.sh"]