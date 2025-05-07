const { app, BrowserWindow, ipcMain, dialog, Menu } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");
const { exec } = require("child_process");

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

function openAddressInputWindow(lanes) {
  const inputWindow = new BrowserWindow({
    width: 500,
    height: 100 + lanes.length * 80,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
    },
    modal: true,
    parent: mainWindow,
  });

  inputWindow.loadFile("input.html");

  inputWindow.webContents.once("did-finish-load", () => {
    inputWindow.webContents.send("lanes-data", lanes);
  });
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
      console.log("JSON generation completed.");
      const jsonPath = path.join(__dirname, "Temp", "result.json");
      const jsonData = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
      if (jsonData.lanes && jsonData.lanes.length > 0) {
        openAddressInputWindow(jsonData.lanes);
      } else {
        console.error("No lanes found in JSON.");
      }
    } else {
      console.error("Error in generating JSON.");
    }
  });
}

function runHardhatDeploy() {
  // Поднимемся на одну папку выше
  process.chdir(path.join(__dirname, ".."));

  // Перейдем в папку Hardhat
  process.chdir("Hardhat");

  const hardhatProcess = exec(
    "npx hardhat run scripts/deploy.ts --network arbitrum_sepolia"
  );

  hardhatProcess.stdout.on("data", (data) => {
    console.log(`[Hardhat stdout]:\n${data}`);
  });

  hardhatProcess.stderr.on("data", (data) => {
    console.error(`[Hardhat stderr]:\n${data}`);
  });

  hardhatProcess.on("close", (code) => {
    if (code === 0) {
      console.log("Hardhat deploy completed successfully.");
    } else {
      console.error(`Hardhat process exited with code ${code}`);
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
      runHardhatDeploy(); // <-- Переносим сюда!
    } else {
      console.error("Error in generating Solidity contract.");
    }
  });
}

ipcMain.on("addresses-submitted", (event, data) => {
  const fs = require("fs");
  const jsonPath = path.join(__dirname, "Temp", "result.json");
  const jsonData = JSON.parse(fs.readFileSync(jsonPath, "utf8"));

  jsonData.lanes = jsonData.lanes.map((lane) => ({
    ...lane,
    address:
      data[lane.lane_name] || "0x0000000000000000000000000000000000000000",
  }));

  fs.writeFileSync(jsonPath, JSON.stringify(jsonData, null, 2));
  console.log("Updated addresses in result.json");

  runPythonToSol(); // Продолжение обработки
});

// Остальное:
app.whenReady().then(createWindow);
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
