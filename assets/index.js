var vue = new Vue({
    el: '#vue-container',
    data: {
        items: [
            // {
            //     path: 'dddddd/aaaa.txt',
            //     progress: '0%',
            //     bold: false,
            // }
        ]
    },
    methods: {
        topBottom: function() {
            $(document).scrollTop($(document).height());
        },
        findItem: function(path) {
            let index = 0
            for (let item of this.items) {
                if(item['path'] == path)
                    return index
                index += 1
            }
            return -1
        },
        setProgress: function(path, progress) {
            let index = this.findItem(path)
            if(index != -1)
                this.items[index]['progress'] = progress
        },
        setBold: function(path, bold) {
            let index = this.findItem(path)
            if(index != -1)
                this.items[index]['bold'] = bold
        },
        removeItem: function(path) {
            let index = this.findItem(path)
            if(index != -1)
                this.items.splice(index - 1, 1)
        },
    }
})

var ex_translations = {
    NotInRightPathError: '找不到../../.minecraft目录',
    NoSettingsFileError: '找不到配置文件',
    FailedToConnectError: '无法连接至服务器',
    UnableToDecodeError: '服务器返回了无法解码的数据',
    UnexpectedTransmissionError: '传输中断',
    UnexpectedHttpCodeError: '不正确的HTTP状态码',
    
    're.error': '正则表达式错误'
}

var config = null
var totalBytes = 0
var receivedBytes = 0

var callback = {
    init: (_config) => {
        updaterApi.setTitle('正在连接服务器')
        config = _config
        console.warn(_config)
    },
    check_for_upgrade: (url) => {
    },
    calculate_differences_for_upgrade: () => {
        updaterApi.setTitle('检查升级..')
    },
    whether_upgrade: (isupgrade) => {
        vue.items = []
        if(isupgrade) {
            updaterApi.setTitle('正在升级')
        } else {
            updaterApi.setTitle('正在更新文件')
        }
    },
    
    upgrading_old_files: (paths) => {
    },
    upgrading_new_files: (paths) => {
        for(let p of paths) {
            let path = p[0]
            let len = p[1]
            let hash = p[2]

            totalBytes += len

            vue.items.push({
                path: path,
                progress: '0%',
                bold: false
            })
        }
    },
    upgrading_before_downloading: () => {
    },
    upgrading_downloading: (file, recv, bytes, total) => {
        vue.setBold(file, true)
        receivedBytes += recv

        vue.setProgress(file, parseInt(bytes/total*100)+'%')
        updaterApi.setTitle('正在升级 '+parseInt(receivedBytes/totalBytes*100)+'%')
    },
    upgrading_before_installing: () => {
        updaterApi.setTitle('开始安装更新')
    },

    check_for_update: (url) => {
    },
    calculate_differences_for_update: () => {
        updaterApi.setTitle('获取新文件')
    },
    updating_old_files: (paths) => {
        for(let p of paths) {
            vue.items.push({
                path: p,
                progress: '等待删除',
                bold: false
            })
        }
    },
    updating_new_files: (paths) => {
        for(let p of paths) {
            let path = p[0]
            let len = p[1]

            totalBytes += len

            vue.items.push({
                path: path,
                progress: '0%',
                bold: false
            })
        }
    },
    updating_before_removing: () => {
    },
    updating_removing: (file) => {
        vue.setBold(file, true)
        vue.setProgress(file, '已删除')
    },
    updating_before_downloading: () => {
        updaterApi.setTitle('下载新文件')
    },
    updating_downloading: (file, recv, bytes, total) => {
        vue.setBold(file, true)
        receivedBytes += recv

        vue.setProgress(file, parseInt(bytes/total*100)+'%')
        updaterApi.setTitle('正在更新文件 '+parseInt(receivedBytes/totalBytes*100)+'%')
    },

    cleanup: () => {
        updaterApi.setTitle('清理退出')
    },

    alert: (text) => {
        alert(text)
    },
    on_error: (type, detail, isPyException, trackback) => {
        if(type in ex_translations)
            type += '('+ex_translations[type]+')'

        alert('出现异常: '+type+'\n\n'+detail)

        if(isPyException && confirm('是否显示异常调用栈?'))
            alert(trackback)

        if(config.error_message && confirm(config.error_message))
            if(config.error_help)
                updaterApi.execute(config.error_help)
    }
}
