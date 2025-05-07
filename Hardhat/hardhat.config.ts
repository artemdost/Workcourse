import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import "dotenv/config";

const config: HardhatUserConfig = {
  solidity: "0.8.28",
  networks: {
    sepolia: {
      url: `${process.env.SEPOLIA_URL}`,
      accounts: [`0x${process.env.PRIVATE_KEY}`],
    },
    arbitrum_sepolia: {
      url: `${process.env.ARBITRUM_SEPOLIA_URL}`,
      accounts: [`0x${process.env.PRIVATE_KEY}`],
    },
  },
  etherscan: {
    apiKey: {
      arbitrumSepolia: `${process.env.ARBITRUMSCAN_KEY}`,
    },
    customChains: [
      {
        network: "arbitrumSepolia",
        chainId: 421614,
        urls: {
          apiURL: "https://api-sepolia.arbiscan.io/api",
          browserURL: "https://sepolia.arbiscan.io",
        },
      },
    ],
  },
};

export default config;
