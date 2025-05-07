import hre, { ethers } from "hardhat";

async function main() {
  console.log("Deploying contract...");

  const [owner] = await ethers.getSigners();

  const GeneratedContract = await ethers.getContractFactory(
    "GeneratedContract",
    owner
  );

  const generatedContract = await GeneratedContract.deploy();

  console.log(
    "GeneratedContract deployed to:",
    await generatedContract.getAddress()
  );

  // Верификация контракта на Arbiscan
  console.log("Verifying contract on Arbiscan...");

  await hre.run("verify:verify", {
    address: await generatedContract.getAddress(),
    constructorArguments: [],
  });
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

// 0x9c43FF350fF9216c3e4dDa777506471E5A6DfdBd
