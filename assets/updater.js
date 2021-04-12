var pywebview = pywebview || {
    api: {
        setTitle: (title) => {
            $('title').html(title)
        },
        toggleFullscreen: () => {
            console.log('toggleFullscreen()')
        },
        minimize: () => {
            console.log('minimize()')
        },
        restore: () => {
            console.log('restore()')
        },
        close: () => {
            console.log('close()')
        },
        execute: (command) => {
            console.log('Execute: '+command)
        },
        getUrl: () => {
            return location.pathname
        },
        loadUrl: (url) => {
            window.open(url)
        },
        start: () => {
            console.log('startUpdate!')
        }
    }
}

var updaterApi = {
    setTitle: (title) => {
        pywebview.api.setTitle(title)
    },
    toggleFullscreen: () => {
        pywebview.api.toggleFullscreen()
    },
    minimize: () => {
        pywebview.api.minimize()
    },
    restore: () => {
        pywebview.api.restore()
    },
    close: () => {
        pywebview.api.close()
    },
    execute: (command) => {
        pywebview.api.execute(command)
    },
    getUrl: () => {
        return pywebview.api.getUrl()
    },
    loadUrl: (url) => {
        pywebview.api.loadUrl(url)
    },
    start: () => {
        pywebview.api.startUpdate()
    }
}