// Import core Electron modules:
// - app: Controls the application's lifecycle (startup, quit)
// - BrowserWindow: Creates and manages native desktop windows
// - ipcMain: Listens for messages sent from the web page (via preload.js)
// - shell: Interacts with the operating system (e.g., opening folders in the file manager)
const { app, BrowserWindow, ipcMain, shell } = require('electron');

// Import Node.js built-in utilities:
// - spawn: Launches external programs (used to run Python/Django)
// - path: Safely builds file paths across operating systems
// - http: Used to check when the local Django server is ready
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

// Keep global references so JavaScript's garbage collector doesn't close them early
let mainWindow;
let djangoProcess;
const DJANGO_URL = 'http://127.0.0.1:8000';

/**
 * Starts the local Python Django server in the background.
 */
function startDjangoServer() {
    // Build exact paths to the virtual environment's Python binary and manage.py
    const pythonPath = path.join(__dirname, '.venv', 'bin', 'python');
    const managePyPath = path.join(__dirname, 'manage.py');

    // Launch Django on localhost port 8000.
    // '--noreload' prevents Django from spawning a second watcher process that would
    // stay stuck running in memory after the Electron window closes.
    djangoProcess = spawn(pythonPath, [managePyPath, 'runserver', '127.0.0.1:8000', '--noreload']);

    // Forward any Django console errors to the terminal for easier debugging
    djangoProcess.stderr.on('data', (data) => {
        console.error(`Django: ${data}`);
    });
}

/**
 * Repeatedly pings the local Django URL until it responds, then triggers the callback.
 * This prevents the desktop window from loading a "Connection Refused" screen while
 * Python is still booting up.
 */
function waitForServer(url, callback) {
    http.get(url, () => {
        callback(); // Server is awake—load the page!
    }).on('error', () => {
        // Server isn't ready yet; wait 250 milliseconds and try again
        setTimeout(() => waitForServer(url, callback), 250);
    });
}

/**
 * Listen for 'open-folder' messages triggered by clicking the "Open Folder" button
 * on a WIP card in the web interface.
 */
ipcMain.on('open-folder', (event, folderPath) => {
    if (folderPath) {
        // Opens the exact directory in the user's native Linux file manager
        shell.openPath(folderPath);
    }
});

/**
 * Creates the main desktop application window and loads the Django web page.
 */
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1100,
        height: 800,
        autoHideMenuBar: true, // Hides the default File/Edit menu bar for a cleaner app look
        webPreferences: {
            // Attach preload.js to securely bridge web JavaScript and Node/Electron APIs
            preload: path.join(__dirname, 'preload.js'),
            // Security best practices: keep Node.js isolated from untrusted web page scripts
            nodeIntegration: false,
            contextIsolation: true
        }
    });

    // Wait until Django is responding before loading the URL into the window
    waitForServer(DJANGO_URL, () => {
        mainWindow.loadURL(DJANGO_URL);
    });

    // Dereference the window object when closed
    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// Electron lifecycle event: runs once Electron has finished initializing
app.whenReady().then(() => {
    startDjangoServer();
    createWindow();
});

// Electron lifecycle event: runs right before the app exits.
// Terminates the background Python server so no orphaned process is left running.
app.on('will-quit', () => {
    if (djangoProcess) {
        djangoProcess.kill();
    }
});

// Quit the application completely when all windows are closed (standard Linux/Windows behavior)
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
