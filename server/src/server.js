const fs = require('fs')
const path = require('path')
const Koa = require('koa')
const router = require('koa-router')()
const koaBody = require('koa-body'); //解析上传文件的插件
const staticFiles = require('koa-static')
const shelljs = require('shelljs')
const { log, error } = require('./util')
const { htmlStatic, pythonStatic, uploadStatic, port } = require('./config')

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
    maxFileSize: 10000 * 1024 * 1024    // 设置上传文件大小最大限制，默认10M
  }
}))

// 搭建静态目录
app.use(staticFiles(path.join(__dirname + htmlStatic)))
app.use(staticFiles(path.join(__dirname + pythonStatic)))
app.use(staticFiles(path.join(__dirname + '/upload/')))
console.log(path.join(__dirname + '/upload/'))

// 搭建上传服务
router.post('/upload', async (ctx, next) => {
  const file = ctx.request.files.file; // 上传的文件在ctx.request.files.file
  // 创建可读流
  const reader = fs.createReadStream(file.path);
  // 修改文件的名称
  var myDate = new Date();
  var newFilename = myDate.getTime() + '-' + file.name;
  var targetPath = path.join(__dirname, '/upload/' + `${newFilename}`);
  //创建可写流
  const upStream = fs.createWriteStream(targetPath);
  // 可读流通过管道写入可写流
  reader.pipe(upStream);
  //返回保存的路径
  return ctx.body = { code: 200, data: { url: 'http://' + ctx.headers.host + '/' + newFilename, local: targetPath } };
});

// 添加路由配置
app.use(router.routes())
// 启动监听端口
app.listen(port)
log(`应用程序已经启动，访问地址:http://127.0.0.1:${port}`)