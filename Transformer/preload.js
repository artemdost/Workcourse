const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("api", {
  onLanesData: (callback) =>
    ipcRenderer.on("lanes-data", (e, lanes) => callback(lanes)),
  submitAddresses: (data) => ipcRenderer.send("addresses-submitted", data),
});
