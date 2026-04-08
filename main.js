// -------------------------------------------------------------
// Nova AI Desktop - Electron Main Process
// Acrylic Transparent Window + Backend Lifecycle + Auto-Update
// -------------------------------------------------------------

const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const { autoUpdater } = require("electron-updater");
const { spawn } = require("child_process");

let mainWindow = null;
let backendProcess = null;

// ------------------------------
// Start Backend (PowerShell Script)
// ------------------------------
function startBackend() {
    return new Promise((resolve, reject) => {
        const scriptPath = path.join(__dirname, "start-backend.ps1");

        const ps = spawn("powershell.exe", [
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            scriptPath
        ]);

        let backendPID = null;

        ps.stdout.on("data", (data) => {
            const output = data.toString().trim();
            if (!isNaN(output)) {
                backendPID = parseInt(output);
                resolve(backendPID);
            }
        });

        ps.stderr.on("data", (data) => {
            console.error("Backend Error:", data.toString());
        });

        ps.on("close", () => {
            if (!backendPID) reject("Backend failed to start");
        });
    });
}

// ------------------------------
// Create Acrylic Window
// ------------------------------
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        frame: false,
        transparent: true,
        vibrancy: "acrylic", // Windows 11 Mica-style blur
        visualEffectState: "active",
        backgroundColor: "#00000000",
        webPreferences: {
            preload: path.join(__dirname, "preload.js"),
            contextIsolation: true,
            nodeIntegration: false
        }
    });

    mainWindow.loadFile(path.join(__dirname, "../frontend/index.html"));

    mainWindow.on("closed", () => {
        mainWindow = null;
    });
}

// ------------------------------
// Auto-Updater Setup
// ------------------------------
autoUpdater.setFeedURL({
    provider: "github",
    owner: "nova-dev",
    repo: "NovaAI-Desktop"
});

autoUpdater.on("update-available", () => {
    if (mainWindow) mainWindow.webContents.send("update_available");
});

autoUpdater.on("update-downloaded", () => {
    if (mainWindow) mainWindow.webContents.send("update_downloaded");
});

// ------------------------------
// App Lifecycle
// ------------------------------
app.whenReady().then(async () => {
    try {
        console.log("Starting backend...");
        const pid = await startBackend();
        backendProcess = pid;
        console.log("Backend started with PID:", pid);

        createWindow();
        autoUpdater.checkForUpdatesAndNotify();

    } catch (err) {
        console.error("Backend failed:", err);
        createWindow();
    }
});

// ------------------------------
// Kill Backend on Exit
// ------------------------------
app.on("before-quit", () => {
    if (backendProcess) {
        try {
            spawn("taskkill", ["/PID", backendProcess, "/F"]);
        } catch (e) {
            console.error("Failed to kill backend:", e);
        }
    }
});

app.on("window-all-closed", () => {
    if (process.platform !== "darwin") app.quit();
});