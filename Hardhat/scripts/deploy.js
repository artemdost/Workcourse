const hardhat = require("hardhat");
const { ethers } = hardhat;

async function main() {
  console.log("Deploying contract...");

  const [owner] = await ethers.getSigners();

  const GeneratedContract = await ethers.getContractFactory(
    "GeneratedContract",
    owner
  );

  const zeroAddress = ethers.ZeroAddress;

  const generatedContract = await GeneratedContract.deploy();

  await generatedContract.waitForDeployment();

  console.log(
    "GeneratedContract deployed to:",
    await generatedContract.getAddress()
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

module.exports = { deployContract };
