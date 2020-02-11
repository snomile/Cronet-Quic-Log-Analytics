var mainVue = new Vue({
  el: '#app',
  data: function () {
    return {
      start: 0,
      end: 0,
      fileName: '',
      fileList: [],
      done: false,
      visible: false,
      message: '',
      error: '',
      netlog: '',
      htmlList: {},
      localPath: '',
      httpPath: '',
      htmlPath: '',
      form: {
        show_all_packet_info: 'True',
        show_receive_send: 'True',
        show_ack_delay: 'False',
        show_size_inflight: 'False',
        ignore_domain_name_list: ['googleapis.com', 'doubleclick.net', 'google-analytics.com']
      },
      loading: null,
    }
  },
  methods: {
    clean() {
      this.fileList = []
    },
    handleBefore() {
      if (this.start > 0) {
        return
      }
      this.loading = this.$loading({
        lock: true,
        text: 'Loading',
        spinner: 'el-icon-loading',
        background: 'rgba(0, 0, 0, 0.7)'
      });
      this.message = '';
      this.error = '';
      this.start = new Date().getTime()
    },
    handleSuccess(response, file, fileList) {
      let hasUpload = false
      fileList.forEach(item => {
        if (item.status !== 'success') {
          hasUpload = true
        }
      })
      this.fileName = file.name;
      if (!hasUpload) {
        this.done = true;
        this.end = new Date().getTime() - this.start
        this.start = 0
      }
      if (response.code === 200) {
        this.httpPath = response.data.url;
        this.localPath = response.data.local;
        this.analysisLog();
      }
    },
    analysisLog() {
      const _this = this;
      $.post('./analysis', {
        localPath: _this.localPath,
        show_all_packet_info: _this.form.show_all_packet_info,
        show_receive_send: _this.form.show_receive_send,
        show_ack_delay: _this.form.show_ack_delay,
        show_size_inflight: _this.form.show_size_inflight,
        ignore_domain_name_list: _this.form.ignore_domain_name_list
      }, function (res) {
        if (res.code === 200) {
          _this.htmlPath = './data_converted/' + res.data.split('/')[0] + '/';
          $.getJSON('./data_converted/' + res.data, function (data) {
            _this.netlog = data.netlog;
            _this.htmlList = data.connections;
          });
        }
        _this.message = res.message.replace(/\r\n/g, "<br>").replace(/\n/g, "<br>").replace(/\s{2,}/g, "&nbsp;&nbsp;&nbsp;&nbsp;");
        _this.error = res.error.replace(/\r\n/g, "<br>").replace(/\n/g, "<br>").replace(/\s{2,}/g, "&nbsp;&nbsp;&nbsp;&nbsp;");
        _this.loading.close();
      }, 'json');
    },
    showLog(url) {
      var _this = this;
      $.getJSON(url, function (data) {
        _this.htmlPath = url.replace('event_session_info.json', '');
        _this.netlog = data.netlog;
        _this.htmlList = data.connections;
      });
    }
  }
})