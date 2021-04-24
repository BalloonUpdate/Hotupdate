const sleep2 = (timeountMS) => new Promise((resolve) => {
    setTimeout(resolve, timeountMS);
});


async function test_(isupgrade) {
    updaterApi.dispatchEvent('init', {})
    await sleep2(100)
    updaterApi.dispatchEvent('check_for_upgrade', 'https://baidu.com')
    await sleep2(100)
    updaterApi.dispatchEvent('calculate_differences_for_upgrade')
    await sleep2(100)
    updaterApi.dispatchEvent('whether_upgrade', isupgrade)
    await sleep2(100)

    if(isupgrade) {
        let old_files = [
            ['UpdaterHotupdatePackage.exe', true]
        ]
        let new_files = [
            ['2.6dev0', 35644, 'cc101a36a955aade313ea815e30234f557d622d2'],
            ['UpdaterHotupdatePackage.exe', 71218479, '8b321031c8b47f2bb6a273171d51b71b039b2579']
        ]
    
        updaterApi.dispatchEvent('upgrading_new_files', new_files)
        await sleep2(100)
    
        updaterApi.dispatchEvent('upgrading_before_downloading')
        await sleep2(100)
    
        // 开始下载
        for (const file of new_files) {
            let filename = file[0]
            let filelen = file[1]
            for(let i=0;i<11;i++) {
                let recv = i==0?0:parseInt(1/10*filelen)
                updaterApi.dispatchEvent('upgrading_downloading', filename, recv, parseInt(i/10*filelen), filelen)
                await sleep2(30)
            }
        }
    
        updaterApi.dispatchEvent('upgrading_before_installing')
    } else {
        updaterApi.dispatchEvent('check_for_update', 'https://127.0.0.1.com')
        await sleep2(100)
        updaterApi.dispatchEvent('calculate_differences_for_update')
        await sleep2(100)

        await sleep2(2000)

        let old_files = [
            '.minecraft/mods/XNetGases-1.16.4-2.1.0 - 副本.jar',
            '.minecraft/mods/keng34343434.jar',
            '.minecraft/mods/updater-php - 快捷方式223123213.jar',
            '.minecraft/mods/vue-2.6.12343434.js',
            '.minecraft/launcher_profiles.json',
            '.minecraft/output-client.log',
            '.minecraft/debug.log',
        ]
        let new_files = [
            ['.minecraft/mods/ZeroCore2-1.16.4-2.0.+7.jar', 649672],
            ['.minecraft/mods/keng.jar', 36553],
            ['.minecraft/mods/updater-php - 快捷方式.jar', 543546],
            // ['.minecraft/mods/vue-2.6.12.js', 37246],
            // ['.minecraft/mods2/ZeroCore2-1.16.4-2.0.+7.jar', 649672],
            // ['.minecraft/mods2/keng.jar', 36553],
            // ['.minecraft/mods2/updater-php - 快捷方式.jar', 543546],
            // ['.minecraft/mods2/vue-2.6.12.js', 37246],
            // ['.minecraft/mods3/ZeroCore2-1.16.4-2.0.+7.jar', 649672],
            // ['.minecraft/mods33/keng.jar', 36553],
            // ['.minecraft/mods3/updater-php - 快捷方式.jar', 543546],
            // ['.minecraft/mods3/vue-2.6.12.js', 37246],
            // ['.minecraft/mods4/ZeroCore2-1.16.4-2.0.+7.jar', 649672],
            // ['.minecraft/mods4/keng.jar', 36553],
            // ['.minecraft/mods4/updater-php - 快捷方式.jar', 543546],
            // ['.minecraft/mods4/vue-2.6.12.js', 37246],
            // ['.minecraft/mods5/ZeroCore2-1.16.4-2.0.+7.jar', 649672],
            // ['.minecraft/mods5/keng.jar', 36553],
            // ['.minecraft/mods6/updater-php - 快捷方式.jar', 543546],
            // ['.minecraft/mods7/vue-2.6.12.js', 37246],
            // ['.minecraft/mods12/updater-php - 快捷方式.jar', 543546],
            // ['.minecraft/mods12/vue-2.6.12.js', 37246],
            // ['.minecraft/mods31/ZeroCore2-1.16.4-2.0.+7.jar', 649672],
            // ['.minecraft/mods133/keng.jar', 36553],
            // ['.minecraft/mods13/updater-php - 快捷方式.jar', 543546],
            // ['.minecraft/mods13/vue-2.6.12.js', 37246],
            // ['.minecraft/mods14/ZeroCore2-1.16.4-2.0.+7.jar', 649672],
            // ['.minecraft/mods14/keng.jar', 36553],
            // ['.minecraft/mods14/updater-php - 快捷方式.jar', 543546],
            // ['.minecraft/mods14/vue-2.6.12.js', 37246],
            // ['.minecraft/mods15/ZeroCore2-1.16.4-2.0.+7.jar', 649672],
            // ['.minecraft/mods15/keng.jar', 36553],
            // ['.minecraft/mods16/updater-php - 快捷方式.jar', 543546],
            // ['.minecraft/mods17/vue-2.6.12.js', 37246],
        ]

        updaterApi.dispatchEvent('updating_new_files', new_files)
        await sleep2(100)
        updaterApi.dispatchEvent('updating_before_downloading')

        for (const file of new_files) {
            let filename = file[0]
            let filelen = file[1]
            let count = 20
            for(let i=0;i<count+1;i++) {
                let recv = i==0?0:parseInt(1/count*filelen)
                updaterApi.dispatchEvent('updating_downloading', filename, recv, parseInt(i/count*filelen), filelen)
                // await sleep2(Range(50, 500))
                await sleep2(Range(50, 90))
            }
        }

        await sleep2(100)
        updaterApi.dispatchEvent('cleanup')
    }
}

function Range(min, max) { 
    return Math.floor(Math.random()*(max-min+1)+min) 
}

function testA() {
    test_(true)
}

function testB() {
    test_(false)
}