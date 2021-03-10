var vue = new Vue({
    el: '#vue-container',
    data: {
        message: '',
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
        output: function(text) {
            this.message += text+'<br/>'
        },
        clearOutput: function() {
            this.message = ''
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



function output(text) {
    vue.output(text)
}

var totalBytes = 0
var receivedBytes = 0

var callback = {
    init: () => {
        updaterApi.setTitle('正在连接服务器')
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
    on_error: (type, detail, trackback) => {
        alert('出现异常: '+type+'\n\n'+detail)
        if(type=='PythonException' && confirm('是否显示异常调用栈?'))
            alert(trackback)
        else if(confirm('是否需要打开服务器官网下载完整客户端?'))
            updaterApi.execute('start https://baidu.com')
    }
}