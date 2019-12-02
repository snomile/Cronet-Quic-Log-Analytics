const fs = require('fs')
const path = require('path')
const Koa = require('koa')
const router = require('koa-router')()
const koaBody = require('koa-body'); //解析上传文件的插件
const staticFiles = require('koa-static')
const shelljs = require('shelljs')
const { log, error } = require('./util')
const { htmlStatic, pythonStatic, shellStatic, port, maxSize } = require('./config')

// 获取koa实例
const app = new Koa()

// 增加日志
app.use(async (ctx, next) => {
  log(`Process ${ctx.request.method} ${ctx.request.url}...`)
  await next()
})

// 设置上传
app.use(koaBody({
  multipart: true,
  formidable: {
    maxFileSize: maxSize * 1000 * 1024 * 1024    // 设置上传文件大小最大限制，默认10M
  }
}))

// 搭建静态目录
app.use(staticFiles(path.join(__dirname + htmlStatic)))
app.use(staticFiles(path.join(__dirname + pythonStatic)))
app.use(staticFiles(path.join(__dirname + '/upload/')))

// 搭建上传服务
router.post('/upload', async (ctx, next) => {
  const file = ctx.request.files.file; // 上传的文件在ctx.request.files.file
  // 修改文件的名称
  var myDate = new Date();
  var newFilename = myDate.getTime() + '-' + file.name;
  var targetPath = path.join(__dirname, '/upload/' + `${newFilename}`);
  // 写入本身是异步的，这里改为同步方法，防止接下来的执行报错
  var writeFile = function () {
    return new Promise(function (resolve, reject) {
      // 创建可读流
      const reader = fs.createReadStream(file.path);
      //创建可写流
      const upStream = fs.createWriteStream(targetPath);
      // 可读流通过管道写入可写流
      reader.pipe(upStream);
      upStream.on('finish', () => {
        resolve('finish');
      });
    });
  }
  await writeFile();
  return ctx.body = { code: 200, data: { url: 'http://' + ctx.headers.host + '/' + newFilename, local: targetPath } };
});

router.post('/analysis', async (ctx, next) => {
  const { localPath, show_all_packet_info, show_receive_send, show_ack_delay, show_size_inflight, ignore_domain_name_list } = ctx.request.body;
  let shell = 'python3 '
    + path.join(__dirname, shellStatic)
    + ' ' + localPath
    + ' ' + show_all_packet_info
    + ' ' + show_receive_send
    + ' ' + show_ack_delay
    + ' ' + show_size_inflight;
  if (ignore_domain_name_list) {
    shell = shell + ' ' + ignore_domain_name_list.join(' ');
  }  
  log('begin shell: ' + shell);
  const res = shelljs.exec(shell);
  const urls = {};
  const htmls = [];
  if (res.stdout) {
    const resLog = res.stdout;
    resLog.split('\n').forEach(line => {
      if (line.indexOf('generate json at') >= 0) {
        const json = line.split('/data_converted/')[1];
        const keyArray = json.split('_').reverse();
        const key = keyArray[3] + '_' + keyArray[2];
        urls[key] = [json];
      }
      if (line.indexOf('generate html at') >= 0) {
        htmls.push(line.split('/html_output/')[1]);
      }
    })
    const keys = Object.keys(urls);
    keys.forEach(key => {
      htmls.forEach(html => {
        if (html.indexOf(key) >= 0) {
          urls[key].push(html);
        }
      })
    })
  } else {
    log(res.stderr, 'red');
    return ctx.body = { code: 0, message: res.stdout, error: res.stderr };
  }
  //返回
  return ctx.body = { code: 200, data: urls, message: res.stdout, error: res.stderr };
});

// 添加路由配置
app.use(router.routes())
// 启动监听端口
app.listen(port)
log(`应用程序已经启动，访问地址:http://127.0.0.1:${port}`)