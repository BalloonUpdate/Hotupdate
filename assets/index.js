var vue = new Vue({
    el: '#vue-container',
    data: {
        progressText: '',
        progress: 0,
        items: [
            // {
            //     path: 'dddddd/aaaa.txt',
            //     progress: 0,
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
        focusOn: function(path) {
            let el = $(".item[data='"+path+"']")
            console.log('focus on: '+path)

            let list = $('.list')
            let scroll = list.scrollTop() + el.position().top - ((document.body.clientHeight-30)*0.85)
            list.stop(true)
            list.animate({scrollTop: scroll}, 10)
        },
        getItemProgress: function(progress) {
            if(progress<=0)
                return 0
            return progress<1000?progress:0
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
var totalFileCount = 0
var downloadFileCount = 0
var holdUi = false

var callback = {
    init: (_config) => {
        updaterApi.setTitle('正在连接服务器')
        vue.progressText = '正在连接服务器'
        config = _config
        
        $('#bg').css('background-image', 'url(\'loading.gif\')')

        if('hold_ui' in _config && _config.hold_ui)
            holdUi = true
    },
    check_for_upgrade: (url) => {
    },
    calculate_differences_for_upgrade: () => {
        updaterApi.setTitle('检查升级..')
        vue.progressText = '检查升级..'
    },
    whether_upgrade: (isupgrade) => {
        vue.items = []
        if(isupgrade) {
            updaterApi.setTitle('正在升级')
            vue.progressText = '正在升级'
        } else {
            updaterApi.setTitle('正在更新文件')
            vue.progressText = '正在更新文件'
        }
    },
    upgrading_new_files: (paths) => {
        $('#bg').css('background-image', '')

        for(let p of paths) {
            let path = p[0]
            let len = p[1]
            let hash = p[2]

            totalBytes += len

            vue.items.push({
                path: path,
                progress: 0,
                bold: false
            })
        }
    },
    upgrading_before_downloading: () => {
    },
    upgrading_downloading: (file, recv, bytes, total) => {
        receivedBytes += recv

        vue.setProgress(file, parseInt(bytes/total*1000))
        updaterApi.setTitle('正在升级 '+parseInt(receivedBytes/totalBytes*100)+'%')
        vue.progressText = '正在升级 '+parseInt(receivedBytes/totalBytes*100)+'%'

        if(bytes==total)
            vue.setBold(file, true)
    },
    upgrading_before_installing: () => {
        updaterApi.setTitle('开始安装更新')
        vue.progressText = '开始安装更新'
    },

    check_for_update: (url) => {
    },
    calculate_differences_for_update: () => {
        updaterApi.setTitle('校验文件..')
        vue.progressText = '校验文件..'
    },
    updating_new_files: (paths) => {
        $('#bg').css('background-image', '')

        totalFileCount = paths.length

        for(let p of paths) {
            let path = p[0]
            let len = p[1]

            totalBytes += len

            vue.items.push({
                path: path,
                progress: 0,
                bold: false
            })
        }
    },
    updating_before_downloading: () => {
        updaterApi.setTitle('下载新文件')
    },
    updating_downloading: (file, recv, bytes, total) => {
        receivedBytes += recv

        // 更新全局信息
        vue.setProgress(file, parseInt(bytes/total*1000))

        let totalprogress = parseInt(receivedBytes/totalBytes*1000)
        vue.progress = totalprogress
        updaterApi.setTitle('正在更新文件 '+(totalprogress/10)+'%')
        filename = file.split('/').reverse()
        vue.progressText = (totalprogress/10)+'%    -    '+downloadFileCount+'/'+vue.items.length+'    -    '+flowSpeedSample(recv)+'/s'

        // 下载开始时
        if(bytes==0)
            vue.focusOn(file)
        
        // 下载完成时
        if(bytes==total)
        {
            vue.setBold(file, true)
            downloadFileCount += 1
        }
    },

    cleanup: () => {
        updaterApi.setTitle('正在结束..')
        vue.progressText = '正在结束..'

        if(holdUi)
            $('#exit-button').css('display', 'flex')
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
