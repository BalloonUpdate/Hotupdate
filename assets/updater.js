var pywebview = pywebview || {
    api: {
        setTitle: (title) => {
            $('title').html(title)
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
    }
}