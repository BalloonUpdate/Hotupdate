class UpdaterApi
{
    constructor()
    {
        this.inDev = true
    }

    onPywebviewReady()
    {
        this.inDev = typeof pywebview.api == 'undefined'
    }

    dispatchEvent(eventName, ...args)
    {
        let event = new CustomEvent(eventName, { detail: {
            args: args
        }})
        document.dispatchEvent(event)
    }

    on(eventName, callback)
    {
        document.addEventListener(eventName, (e) => {
            callback.bind(this)(...e.detail.args)
        })
    }

    setTitle(title) {
        if(!this.inDev)
            pywebview.api.setTitle(title)
        else
            document.querySelector('title').innerText
    }

    toggleFullscreen() {
        if(!this.inDev)
            pywebview.api.toggleFullscreen()
        else
            console.log('toggleFullscreen()')
    }

    minimize() {
        if(!this.inDev)
            pywebview.api.minimize()
        else
            console.log('minimize()')
    }

    restore() {
        if(!this.inDev)
            pywebview.api.restore()
        else
            console.log('restore()')
    }

    close() {
        if(!this.inDev)
            pywebview.api.close()
        else
            console.log('close()')
    }

    execute(command) {
        if(!this.inDev)
            this.getWorkDirectory().then(wd => pywebview.api.execute('cd /D "'+wd+'" && '+command))
        else
            console.log('execute: '+command)
    }

    async getWorkDirectory() {
        if(!this.inDev)
            return pywebview.api.getWorkDirectory()
        else
            return ''
    }

    async getUrl() {
        if(!this.inDev)
            return pywebview.api.getUrl()
        else
            return location.pathname
    }

    loadUrl(url) {
        if(!this.inDev)
            pywebview.api.loadUrl(url)
        else
            window.open(url)
    }

    start()  {
        if(!this.inDev)
            setTimeout(() => pywebview.api.startUpdate(), 50);
        else
            console.log('startUpdate!')
    }

}

var updaterApi = new UpdaterApi();

window.addEventListener('pywebviewready', function() {
    console.log('<i>pywebview</i> is ready')
    updaterApi.onPywebviewReady()
})