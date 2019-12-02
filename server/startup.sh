#!/bin/sh

cd /opt/cla/Cronet-Quic-Log-Analytics
git fetch --all
git reset --hard origin/master
node /opt/cla/Cronet-Quic-Log-Analytics/server/src/server.js