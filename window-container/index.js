const { app, BrowserWindow } = require('electron');

const URL_PATH = 'http://cssbattle.2024.csgames.org';

const create_window = () => {
  const window = new BrowserWindow({
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
    },
    fullscreen: true,
    frame: false,
    kiosk: true,
    resizable: false,
    minimizable: false,
  });

  window.loadURL(URL_PATH);
  window.setMenu(null);

  // -- Set fullscreen
  window.maximize();
  window.setFullScreen(true);

  // -- disable right click
  window.webContents.on('context-menu', (e) => e.preventDefault());

  // -- disable keyboard shortcut
  window.webContents.on('before-input-event', (e, input) => input.key === 'F12'&& e.preventDefault());
}

app.whenReady().then(create_window);

// -- Quit when all windows are closed
app.on('window-all-closed', () => process.platform !== 'darwin' && app.quit());

app.on('activate', () => BrowserWindow.getAllWindows().length === 0 && create_window());
