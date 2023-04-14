const { ipcRenderer } = require('electron');

let DOMtext = document.getElementById("text");

let stopped = false;
let muted = false;
let nonEnglish = false;

ipcRenderer.on("python-output", (event, text) => {
    DOMtext.innerHTML = text;
});

function SendTextOSC(text) {
    ipcRenderer.send("text-send", text);
}

function UpdateButton(id, text, add, remove) {
    let button = document.getElementById(id);

    button.classList.remove(remove);
    button.classList.add(add);
    button.innerText = text;
}

// Right bar buttons
document.getElementById("StopButton").addEventListener("click", () => {
    console.log("Stop button");

    if(stopped) {
        //start it
        DOMtext.innerText = "Preparing to load model";

        UpdateButton("StopButton", "Stop model", "green", "red");

        ipcRenderer.send("model-start");
    } else {
        //stop it

        UpdateButton("StopButton", "Start model", "red", "green");

        ipcRenderer.send("model-stop");
    }

    stopped = !stopped;
})

document.getElementById("MuteButton").addEventListener("click", () => {
    ipcRenderer.send("model-mute");

    if(muted) {
        //Unmute
        DOMtext.innerText = "Unmuted";
        UpdateButton("MuteButton", "Unmuted", "green", "red");
    } else {
        //Mute
        DOMtext.innerText = "Muted";
        UpdateButton("MuteButton", "Muted", "red", "green");
    }

    muted = !muted;
})

document.getElementById("ClearButton").addEventListener("click", () => {
    ipcRenderer.send("model-clear");
})

document.getElementById("NoEnglishButton").addEventListener("click", () => {
    ipcRenderer.send("model-nonEnglish");

    if(nonEnglish) {
        //Disable it
        UpdateButton("NoEnglishButton", "Non English", "red", "green");
    } else {
        //Enable it
        UpdateButton("NoEnglishButton", "Non English", "green", "red");
    }

    nonEnglish = !nonEnglish;
})

//Tab switching buttons
function SetTab(setID, style, buttonID) {
    document.getElementById("MainButton").classList.remove("selected");
    document.getElementById("InputButton").classList.remove("selected");
    document.getElementById("SettingsButton").classList.remove("selected");

    document.getElementById(buttonID).classList.add("selected");

    document.getElementById("MainTab").style.display = "none";
    document.getElementById("InputTab").style.display = "none";
    document.getElementById("SettingsTab").style.display = "none";

    document.getElementById(setID).style.display = style;
}

document.getElementById("MainButton").addEventListener("click", () => {
    SetTab("MainTab", "flex", "MainButton");
})

document.getElementById("InputButton").addEventListener("click", () => {
    SetTab("InputTab", "flex", "InputButton");
})

document.getElementById("SettingsButton").addEventListener("click", () => {
    SetTab("SettingsTab", "unset", "SettingsButton");
})

// Model sizes buttons
function SetModelSize(size, buttonID) {
    document.getElementById("TinyButton").classList.remove("selected");
    document.getElementById("BaseButton").classList.remove("selected");
    document.getElementById("SmallButton").classList.remove("selected");

    document.getElementById(buttonID).classList.add("selected");

    ipcRenderer.send("model-size", size);
}

document.getElementById("TinyButton").addEventListener("click", () => {
    SetModelSize("tiny", "TinyButton");
})

document.getElementById("BaseButton").addEventListener("click", () => {
    SetModelSize("base", "BaseButton");
})

document.getElementById("SmallButton").addEventListener("click", () => {
    SetModelSize("small", "SmallButton");
})

// input
function CompileAndSendText() {
    let DOMelement = document.getElementById("SendText");

    let SendText = DOMelement.value.toString();
    DOMelement.value = "";


    if(SendText.length > 144) {
        let textAr = SendText.match(/.{1,138}/g); //Split it into 144 sized chunks

        SendTextOSC(textAr[0] + "...");

        let i = 1;
        const intervalId = setInterval(() => {
            if (i >= textAr.length - 1) { // Check if this is the last chunk
                SendTextOSC("..." + textAr[i]); // Log the last chunk with ellipses before and after
                clearInterval(intervalId);
                return;
            }

            SendTextOSC("..." + textAr[i] + "...");
            i++;
        }, 6900); //Nice
    } else {
        SendTextOSC(SendText);
    }
}

document.getElementById("SendText").addEventListener("keyup", (e) => {
    if (e.code === "Enter") {
        CompileAndSendText();
    }
})

document.getElementById("SendButton").addEventListener("click", () => {
    CompileAndSendText();
})

