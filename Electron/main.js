const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')
const { spawn } = require('child_process');

let win = null;

const createWindow = () => {
    win = new BrowserWindow({
        width: 780,
        height: 450,
        icon: path.join(__dirname, 'OpenAI.ico'),
        autoHideMenuBar: true,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    })

    win.loadFile('index.html')

    ipcMain.on('python-output', (event, output) => {
        const outputElement = document.getElementById('text');
        outputElement.innerText = output;
    });
}

let pythonModule = null;
let modelSize = "base", nonEnglish = false, device = "GPU";

function startModule() {
    pythonModule = spawn('python', [path.join(__dirname, 'model.py'), modelSize, nonEnglish, device]);

    console.log("started")

    pythonModule.stdout.on('data', (data) => {
        const output = data.toString();
        console.log(output)
        win.webContents.send('python-output', output);
    });

    pythonModule.stderr.on('data', (data) => {
        console.error(data.toString());
    });
}

function stopModule() {
    pythonModule.stdin.write('stop\n');
}

function muteModule() {
    pythonModule.stdin.write('mute\n');
}


function SendOSC(text) {
    let sender = spawn('python', [path.join(__dirname, 'send.py'), text]);

    sender.stderr.on('data', (data) => {
        console.error(data.toString());
    });
}

app.whenReady().then(() => {
    createWindow();
    startModule();
})

app.on('window-all-closed', () => {
    stopModule();
    if (process.platform !== 'darwin') app.quit();
})

// Model listeners
ipcMain.on("model-stop", () => {
    stopModule();
});
ipcMain.on("model-start", () => {
    startModule();
});
ipcMain.on("model-size", (something, model) => {
    stopModule();
    modelSize = model;
    startModule();
})
ipcMain.on("model-mute", () => {
    muteModule();
})
ipcMain.on("model-clear", () => {
    SendOSC("");
})
ipcMain.on("model-nonEnglish", () => {
    stopModule();
    nonEnglish = !nonEnglish;
    startModule();
})

// Text
ipcMain.on("text-send", (something, text) => {
    SendOSC(text);
})