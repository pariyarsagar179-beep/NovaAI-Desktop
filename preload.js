// -------------------------------------------------------------
// Nova AI Desktop - Preload Script
// Secure IPC Bridge (No Node Access in Frontend)
// -------------------------------------------------------------

const { contextBridge, ipcRenderer } = require("electron");

// Expose safe APIs to the frontend
contextBridge.exposeInMainWorld("novaAPI", {
    // Send messages to backend (if needed later)
    send: (channel, data) => {
        ipcRenderer.send(channel, data);
    },

    // Receive messages from main process
    on: (channel, callback) => {
        ipcRenderer.on(channel, (event, data) => callback(data));
    },

    // Auto-update events
    onUpdateAvailable: (callback) => {
        ipcRenderer.on("update_available", () => callback());
    },

    onUpdateDownloaded: (callback) => {
        ipcRenderer.on("update_downloaded", () => callback());
    }
});