/**
 * 处理stream
 *
 * @author yang.xiaolong
 * @date 2019-11-29
 * @param {*} stream_dict
 */
function initStream(stream_dict) {
  var keys = Object.keys(stream_dict);
  var obj = {};
  var yData = {
    0: ''
  };
  keys.forEach(function(key, index) {
    var y = 150 * (index + 1);
    yData[y] = 'Stream ' + key
    obj[key] = {
      name: 'Stream ' + key,
      value: y
    }
  });
  obj.yData = yData;
  return obj;
}

/**
 * 处理 packets_received
 *
 * @author yang.xiaolong
 * @date 2019-11-29
 * @param {*} packets_received
 * @param {*} streamMap
 * @param {*} frameMap
 */
function initPacketsReceived(packets_received, streamMap, frameMap) {
  var lastTime = 0; // 上一个时间
  var step = 0; // 如果时间存在，则远点向上位移的距离
  var receivedData = [];
  packets_received.forEach(function (item) {
    if (item.time === lastTime) {
      step += 1;
    } else {
      step = 0;
    }
    lastTime = item.time;
    item.frame_ids.forEach(function (frame, index) {
      var frameObj = frameMap[frame];
      var streamObj = streamMap[frameObj.stream_id];
      var x = item.time * 10;
      var y = parseInt(streamObj.value) + index * 10 + step * 10;
      frameObj.x = x;
      frameObj.y = y;
      receivedData.push([x, y, frame]);
    })
  });
  return receivedData;
}


/**
 * 处理 
 *
 * @author yang.xiaolong
 * @date 2019-11-30
 * @param {*} packets_sent
 * @param {*} streamMap
 * @param {*} frameMap
 */
function initPacketsSent(packets_sent, streamMap, frameMap) {
  var lastTime = 0; // 上一个时间
  var step = 0; // 如果时间存在，则远点向上位移的距离
  var frameData = [];
  var packetData = [];
  var lineData = [];
  packets_sent.forEach(function (item) {
    if (item.time === lastTime) {
      step += 1;
    } else {
      step = 0;
    }
    lastTime = item.time;
    item.frame_ids.forEach(function (frame, index) {
      var frameObj = frameMap[frame];
      var streamObj = streamMap[frameObj.stream_id];
      var x = item.time * 10;
      var y = parseInt(streamObj.value) + index * 10 + step * 10;
      frameObj.x = x;
      frameObj.y = y;
      frameData.push([x, y, frame]);
    });
    var packetX = item.time * 10;
    var packetY = step * 10, item;
    packetData.push([packetX, packetY, item]);
    var ackFrameObj = frameMap[item.ack_by_frame];
    if (ackFrameObj) {
      lineData.push({
        coords: [
          [packetX, packetY],
          [ackFrameObj.x, ackFrameObj.y]
        ]
      });
    }
  });
  return {
    frameData: frameData,
    packetData: packetData,
    lineData: lineData,
  };
}