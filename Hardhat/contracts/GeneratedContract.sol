// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract GeneratedContract {
    string public conditions;
    uint public deadline;
    address public partner;
    string public answer;

    enum Status {
        Started,
        Failed,
        Success
    }

    Status public currentStatus = Status.Started;

    // Role addresses
    address public Worker = 0x9c43FF350fF9216c3e4dDa777506471E5A6DfdBd;
    address public Moderator = 0x9c43FF350fF9216c3e4dDa777506471E5A6DfdBd;
    address public Administator = 0x9c43FF350fF9216c3e4dDa777506471E5A6DfdBd;

    // Role modifiers
    modifier onlyWorker() {
        require(msg.sender == Worker, "Caller is not the Worker");
        _;
    }
    modifier onlyModerator() {
        require(msg.sender == Moderator, "Caller is not the Moderator");
        _;
    }
    modifier onlyAdministator() {
        require(msg.sender == Administator, "Caller is not the Administator");
        _;
    }

    modifier onlyWhenStarted() {
        require(currentStatus == Status.Started, "Contract is not in Started status");
        _;
    }

    function Create_conditions(string memory _conditions, uint _deadline, address _partner) external onlyWorker() onlyWhenStarted {
        conditions = _conditions;
        deadline = _deadline;
        partner = _partner;
    }

    function Check_answer() external onlyWorker() onlyWhenStarted returns (string memory) {
        return answer;
    }

    function Check_conditions() external onlyModerator() onlyAdministator() onlyWhenStarted returns (string memory, uint) {
        return (conditions, deadline);
    }

    function Answer(string memory _answer) external onlyModerator() onlyWhenStarted {
        answer = _answer;
    }

    function Decline() external onlyWorker() onlyAdministator() onlyWhenStarted {
        currentStatus = Status.Failed;
    }

    function Approve() external onlyAdministator() onlyWhenStarted {
        currentStatus = Status.Success;
    }
}
