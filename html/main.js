// 默认字体集
var fontFamily = 'Helvetica Neue,Helvetica,Arial,Microsoft Yahei,Hiragino Sans GB,Heiti SC,WenQuanYi Micro Hei,sans-serif';
// 默认字体样式
var defaultFont = {
  text: '',
  textAlign: 'center',
  textVerticalAlign: 'middle',
  fontSize: 14,
  fontFamily: fontFamily,
  fontWeight: 'normal',
  textFill: '#666'
}
/**
 * 初始化packet send
 *
 * @author yang.xiaolong
 * @date 2019-11-19
 * @param {*} data
 */
function initPacketsSent(render, data, streamMap, frameMap) {
  var h = render.getHeight();
  var lastTime = 0;
  var step = 0;
  data.forEach(function (item) {
    if (item.time === lastTime) {
      step += 1;
    } else {
      step = 0;
    }
    lastTime = item.time;
    var ack_by_frame = item.ack_by_frame;
    var ack_delay = item.ack_delay;
    item.frame_ids.forEach(function(frame, index) {
      var streamObj = streamMap[frameMap[frame].stream_id];
      var x = item.time * 10 + 100;
      var y = streamObj.y1 - 4.5 - index * 9 - step * 9;
      var rect = new zrender.Rect({
        shape: {
          width: 9,
          height: 9,
          x: x,
          y: y,
        },
        style: {
          fill: '#00bfff',
          stroke: '#ffffff'
        },
        info: frame
      })
      render.add(rect);
      var ackFrame = frameMap[ack_by_frame];
      if (ackFrame) {
        ackFrame.ack_delay = ack_delay;
        // 添加关联连线
        var line = new zrender.Line({
          style: {
            lineWidth: 1,
            lineDash: [5],
            opacity: 0.6
          },
          shape: {
            x1: x + 4.5,
            y1: y + 4.5,
            x2: ackFrame.x + 4.5,
            y2: ackFrame.y + 4.5
          }
        });
        render.add(line);
      }
    })
  })
}

/**
 * 初始化packet received
 *
 * @author yang.xiaolong
 * @date 2019-11-19
 * @param {*} data
 */
function initPacketsReceived(render, data, streamMap, frameMap) {
  var h = render.getHeight();
  var lastTime = 0;
  var step = 0;
  data.forEach(function (item) {
    if (item.time === lastTime) {
      step += 1;
    } else {
      step = 0;
    }
    lastTime = item.time;
    item.frame_ids.forEach(function (frame, index) {
      var streamObj = streamMap[frameMap[frame].stream_id];
      var x = item.time * 10 + 100;
      var y =  streamObj.y1 - 4.5 - index * 9 - step * 9;
      var rect = new zrender.Rect({
        shape: {
          width: 9,
          height: 9,
          x: x,
          y: y,
        },
        style: {
          fill: '#ff4500',
          stroke: '#ffffff'
        },
        info: frame
      })
      frameMap[frame] = Object.assign(frameMap[frame], {
        x: x,
        y: y,
      })
      render.add(rect);
    })
  })
}

/**
 * 初始化 stream
 *
 * @author yang.xiaolong
 * @date 2019-11-19
 * @param {*} render
 * @param {*} stream_dict
 */
function initStream(render, stream_dict, maxWidth) {
  var keys = Object.keys(stream_dict);
  keys.reverse();
  var w = render.getWidth();
  var h = render.getHeight();
  // 获取每个stream的坐标间距
  var step = h / (keys.length + 3);
  keys.forEach(function(key, index) {
    // 计算stream的y坐标，并保存
    var y = step * (index + 2);
    var streamObj = stream_dict[key];
    if (streamObj) {
      streamObj = Object.assign(streamObj, {
        x1: 100,
        y1: y,
        x2: maxWidth - 25,
        y2: y,
      });
    }
    // 设定stream文字
    var fontStyle = Object.assign(defaultFont, { text: 'stream_' + key });
    var streamText = new zrender.Text({
      style: fontStyle,
      position: [50, y]
    });
    render.add(streamText);
    // 设定stream线轴
    var streamLine = new zrender.Line({
      style: {
        lineWidth: 1,
        lineDash: [2],
        opacity: 0.8
      },
      shape: streamObj,
      // info: streamObj
    });
    render.add(streamLine);
  })
}


/**
 * 初始化 frame
 *
 * @author yang.xiaolong
 * @date 2019-11-19
 * @param {*} render
 * @param {*} data
 */
function initFrame(render, map) {
  var keys = Object.keys(map)
  keys.forEach(function (key) {
    console.log(key, map[key])
  })
}

function tip(info, x, y) {
  var html = '';
  var keys = Object.keys(info)
  keys.forEach(function (key) {
    html += '<div class="info">' + key + ':' + JSON.stringify(info[key]) + '</div>'
  })
  $('#show').html(html);
  $('#show').show();
  if ($('#main').width() - $('#show').width() < x) {
    x = x - $('#show').width() - 20;
  }
  if ($('#main').height() - $('#show').height() < y) {
    y = y - $('#show').height() - 20;
  }
  $('#show').css('left', x);
  $('#show').css('top', y);
}