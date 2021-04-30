var vue = new Vue({
    el: '#vue-container',
    data: {
        currentProgressText: '',
        currentProgress: 0,
        totalProgressText: '',
        totalProgress: 0,
    }
})

function exit()
{
    if('postcalled_command' in config && config.postcalled_command != '')
        updaterApi.execute(config.postcalled_command)
    
    updaterApi.close()
}

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

updaterApi.on('init', function(_config) {
    console.log(this)
    this.setTitle('准备文件更新')
    vue.progressText = '正在连接服务器'
    config = _config
    console.log(_config)
    
    this.start()
})

updaterApi.on('calculate_differences_for_upgrade', function() {
    this.setTitle('检查文件')
    vue.progressText = '检查文件..'
})

updaterApi.on('whether_upgrade', function(isupgrade) {
    this.setTitle('正在更新文件')
    vue.progressText = '正在更新文件'
})

updaterApi.on('upgrading_new_files', function(paths) {
    for(let p of paths) {
        let path = p[0]
        let len = p[1]
        let hash = p[2]
        totalBytes += len
    }
})

updaterApi.on('upgrading_downloading', function(file, recv, bytes, total) {
    receivedBytes += recv

    vue.currentProgress = parseInt(bytes/total*10000)
    vue.currentProgressText = file

    let totalProgress = parseInt(receivedBytes/totalBytes*10000)
    vue.totalProgress = totalProgress
    vue.totalProgressText = '正在下载新文件 '+(totalProgress/100)+'%'

    this.setTitle('正在下载新文件 '+(totalProgress/100)+'%')
})

updaterApi.on('upgrading_before_installing', function() {
    this.setTitle('开始安装更新包')
    vue.totalProgressText = '开始安装更新包'
})

//    -------------------------------------

updaterApi.on('calculate_differences_for_update', function() {
    this.setTitle('检查文件更新中')
    vue.totalProgressText = '校验文件..'
})


updaterApi.on('updating_new_files', function(paths) {
    totalFileCount = paths.length

    for(let p of paths) {
        let path = p[0]
        let len = p[1]
        totalBytes += len
    }

    this.setTitle('下载新文件')
})

var lastUpdate = 0
var lastFile = ''
updaterApi.on('updating_downloading', function(file, recv, bytes, total) {
    receivedBytes += recv

    let filename = file.lastIndexOf('/')!=-1? file.substring(file.lastIndexOf('/')+1):file
    let ts = new Date().getTime()

    if(ts-lastUpdate > 1000)
    {
        vue.currentProgress = parseInt(bytes/total*10000)
        vue.currentProgressText = filename
        lastUpdate = ts
        lastFile = filename
    } else {
        if(lastFile==filename)
            vue.currentProgress = parseInt(bytes/total*10000)
    }

    let totalProgress = parseInt(receivedBytes/totalBytes*10000)
    vue.totalProgress = totalProgress
    vue.totalProgressText = (totalProgress/100)+'% - '+(downloadFileCount+1)+'/'+totalFileCount

    this.setTitle('下载新文件 '+parseInt((totalProgress/10)+'')/10+'%')

    // 下载完成时
    if(bytes==total)
        downloadFileCount += 1
})

updaterApi.on('cleanup', function() {
    this.setTitle('正在结束')
    vue.totalProgressText = '正在结束'

    if('hold_ui' in config && config.hold_ui)
        $('#exit-button').css('display', 'flex')
    else if('visible_time' in config && config.visible_time >= 0) {
        setTimeout(() => exit(), config.visible_time);
    } else {
        exit()
    }
})

updaterApi.on('on_error', function(type, detail, isPyException, trackback) {
    if(type in ex_translations)
        type += '('+ex_translations[type]+')'

    alert('出现错误: '+type+'\n\n'+detail)
    
    if(!('indev' in config && config['indev']) || true)
    {
        if(isPyException && confirm('是否显示错误详情? (请将错误报告给开发者)'))
            alert(trackback)
    }

    if(config.error_message && confirm(config.error_message))
        if(config.error_help)
            this.execute(config.error_help)
    
    updaterApi.close()
})

