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
function initPacketsSent(render, data) {
  data.forEach(function (item) {
    console.log(item)
  })
}

/**
 * 初始化packet received
 *
 * @author yang.xiaolong
 * @date 2019-11-19
 * @param {*} data
 */
function initPacketsReceived(render, data) {
  data.forEach(function (item) {
    console.log(item)
  })
}

/**
 * 初始化 stream
 *
 * @author yang.xiaolong
 * @date 2019-11-19
 * @param {*} render
 * @param {*} map
 */
function initStream(render, map, streamMap) {
  var keys = Object.keys(map);
  keys.reverse();
  var w = render.getWidth();
  var h = render.getHeight();
  // 获取每个stream的坐标间距
  var step = h / (keys.length + 2);
  keys.forEach(function(key, index) {
    // 计算stream的y坐标，并保存
    var y = step * (index + 1);
    streamMap[key] = {
      x1: 100,
      y1: y,
      x2: w - 25,
      y2: y,
    };
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
      shape: streamMap[key]
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