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
  var yValues = [];
  keys.forEach(function(key, index) {
    var y = 100 * (index + 1);
    yValues.push(y)
    obj[key] = {
      name: 'Stream ' + key,
      value: y
    }
  });
  obj.yValues = yValues;
  return obj;
}


/**
 * 处理 packets_received
 *
 * @author yang.xiaolong
 * @date 2019-11-29
 * @param {*} packets_received
 */
function initPacketsReceived(packets_received) {
  var lastTime = 0;
  packets_received.forEach(function (item) {

  })
}