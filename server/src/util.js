const log4js = require('log4js')
const chalk = require('chalk')
const crypto = require('crypto')

log4js.configure({
  appenders: { access: { type: 'file', filename: './logs/access.log' } },
  categories: { default: { appenders: ['access'], level: 'error' } }
})
// 将日志输出
const logger = log4js.getLogger('access')

// 封装日志
const log = (msg, color = 'limegreen') => {
  logger.info(msg)
  // eslint-disable-next-line no-console
  console.log(chalk.keyword(color)(msg))
}
// 错误日志
const error = (msg, color = 'orangered ') => {
  logger.error(msg)
  // eslint-disable-next-line no-console
  console.log(chalk.keyword(color)(msg))
}

const getClientIP = (req) => {
  let ip = '0.0.0.0';
  try {
    ip = req.headers['x-forwarded-for'] || // 判断是否有反向代理 IP
      req.connection.remoteAddress || // 判断 connection 的远程 IP
      req.socket.remoteAddress || // 判断后端的 socket 的 IP
      req.connection.socket.remoteAddress;
  } catch (e) {
    log(err, red);
  }
  return ip;
};

module.exports = {
  log, error, getClientIP
}