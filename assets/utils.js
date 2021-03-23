var timer = 0
var samples = [0, 0, 0, 0, 0]

function flowSpeedSample(bytes)
{
    if(timer == 0) {
        timer = new Date().getTime()
        return 0
    }

    now = new Date().getTime()
    timeDiff = now - timer
    timer = now
    sample = parseInt(bytes / timeDiff * 1000)
    samples.push(sample)
    samples.shift()

    count = samples.length
    val = 0

    for(i=0;i<count;i++)
        val += samples[i]

    // https://www.cnblogs.com/jialinG/p/9577724.html
    function bytesToSize(bytes, space = ' ') {
        if (bytes === 0) return '0 B';
        var k = 1024, // or 1024
            sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'],
            i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseInt((bytes / Math.pow(k, i))*100)/100 + space + sizes[i];
    }

    return bytesToSize(parseInt(val/count))
}