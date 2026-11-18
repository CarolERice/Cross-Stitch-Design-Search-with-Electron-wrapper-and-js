// contextBridge: Safely exposes specific functions to the browser's global 'window' object
// ipcRenderer: Sends asynchronous messages from the web page to main.js
const { contextBridge, ipcRenderer } = require('electron');

// Creates 'window.desktopAPI' inside the web page's JavaScript environment.
// Only the functions listed here can cross the boundary into Electron's main process.
contextBridge.exposeInMainWorld('desktopAPI', {
    openFolder: (folderPath) => ipcRenderer.send('open-folder', folderPath)
});
