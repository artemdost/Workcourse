const { app, BrowserWindow, ipcMain, dialog, Menu } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, "preload.js"),
    },
    frame: true,
  });

  mainWindow.loadURL("https://demo.bpmn.io/");

  mainWindow.on("closed", () => {
    mainWindow = null;
  });

  const menu = Menu.buildFromTemplate([
    {
      label: "Transform",
      click: () => {
        openFileDialog();
      },
    },
  ]);

  Menu.setApplicationMenu(menu);
}

async function openFileDialog() {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ["openFile"],
    filters: [{ name: "BPMN Files", extensions: ["bpmn"] }],
  });

  if (!result.canceled) {
    const filePath = result.filePaths[0];
    runPythonToJson(filePath);
  }
}

function runPythonToJson(bpmnFilePath) {
  const pythonProcess = spawn("python", [
    path.join(__dirname, "Converters", "toJson.py"),
    bpmnFilePath,
  ]);

  pythonProcess.stdout.on("data", (data) => {
    console.log(`stdout: ${data}`);
  });

  pythonProcess.stderr.on("data", (data) => {
    console.error(`stderr: ${data}`);
  });

  pythonProcess.on("close", (code) => {
    if (code === 0) {
      console.log(
        "JSON generation completed. Now generating Solidity contract..."
      );
      runPythonToSol();
    } else {
      console.error("Error in generating JSON.");
    }
  });
}

function runPythonToSol() {
  const pythonProcess = spawn("python", [
    path.join(__dirname, "Converters", "toSol.py"),
  ]);

  pythonProcess.stdout.on("data", (data) => {
    console.log(`stdout: ${data}`);
  });

  pythonProcess.stderr.on("data", (data) => {
    console.error(`stderr: ${data}`);
  });

  pythonProcess.on("close", (code) => {
    if (code === 0) {
      console.log("Solidity contract generated successfully.");
      // Убираем вызов функции деплоя
      // runHardhatDeploy(); // Эта строка теперь не нужна
    } else {
      console.error("Error in generating Solidity contract.");
    }
  });
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
