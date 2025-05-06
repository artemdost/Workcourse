import json
import shutil
from pathlib import Path

def get_type_with_storage(t):
    if t == "string":
        return "string memory"
    elif t.startswith("bytes"):
        return f"{t} memory"
    elif "[]" in t:
        return f"{t} memory"
    return t

def generate_solidity_contract(json_data):
    solidity_code = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract GeneratedContract {\n"""

    variables = {}
    functions = json_data["functions"]
    lanes = json_data["lanes"]

    for function in functions:
        for action in function["actions"]["Set"]:
            variables[action["name"]] = action["type"]
        for action in function["actions"]["Get"]:
            variables[action["name"]] = action["type"]

    for var_name, var_type in variables.items():
        solidity_code += f"    {var_type} public {var_name};\n"

    solidity_code += "\n    enum Status {\n"
    solidity_code += "        Started,\n"
    solidity_code += "        Failed,\n"
    solidity_code += "        Success\n"
    solidity_code += "    }\n\n"
    solidity_code += "    Status public currentStatus = Status.Started;\n"

    solidity_code += "\n    // Role addresses\n"
    for lane in lanes:
        # Задание адреса роли прямо в коде
        solidity_code += f"    address public {lane['lane_name']} = {lane['address']};\n"

    solidity_code += "\n    // Role modifiers\n"
    for lane in lanes:
        solidity_code += f"    modifier only{lane['lane_name'].capitalize()}() {{\n"
        solidity_code += f"        require(msg.sender == {lane['lane_name']}, \"Caller is not the {lane['lane_name']}\");\n"
        solidity_code += "        _;\n    }\n"

    solidity_code += "\n    modifier onlyWhenStarted() {\n"
    solidity_code += "        require(currentStatus == Status.Started, \"Contract is not in Started status\");\n"
    solidity_code += "        _;\n    }\n"

    for function in functions:
        func_name = function["function_name"].replace(" ", "_")
        modifiers = []

        assignees = function.get("assignee", [])
        if isinstance(assignees, str):  # Если assignees это строка, обернуть в список
            assignees = [assignees]
        for assignee in assignees:
            # Убедимся, что assignee — это строка
            if isinstance(assignee, str):
                modifiers.append(f"only{assignee.capitalize()}()")
        
        if assignees:
            modifiers.append("onlyWhenStarted")
        if function["actions"]["Pay"]:
            modifiers.append("payable")

        params = []
        for action in function["actions"]["Set"]:
            if action["variable"] == "null":
                param_type = get_type_with_storage(action["type"])
                params.append(f"{param_type} _{action['name']}")

        return_types = [get_type_with_storage(a["type"]) for a in function["actions"]["Get"]]

        signature = f"\n    function {func_name}({', '.join(params)}) external"
        if modifiers:
            signature += f" {' '.join(modifiers)}"
        if return_types:
            signature += f" returns ({', '.join(return_types)})"

        solidity_code += signature + " {\n"

        for action in function["actions"]["Set"]:
            value = action["variable"]
            if value == "null":
                value = f"_{action['name']}"
            elif action["type"] == "string" and not value.startswith('"'):
                value = f'"{value}"'
            solidity_code += f"        {action['name']} = {value};\n"

        for action in function["actions"]["Pay"]:
            if "amount" in action and "to" in action:
                solidity_code += f"        require(msg.value == {action['amount']}, \"Incorrect payment amount\");\n"
                solidity_code += f"        payable({action['to']}).transfer(msg.value);\n"

        if "End" in function["actions"]:
            end_lines = function["actions"]["End"]
            if isinstance(end_lines, list) and end_lines:
                status = end_lines[0].get("status")
                if status == "Success":
                    solidity_code += "        currentStatus = Status.Success;\n"
                elif status == "Failed":
                    solidity_code += "        currentStatus = Status.Failed;\n"

        if function["actions"]["Get"]:
            returns = [a["name"] for a in function["actions"]["Get"]]
            if len(returns) == 1:
                solidity_code += f"        return {returns[0]};\n"
            else:
                solidity_code += f"        return ({', '.join(returns)});\n"

        solidity_code += "    }\n"

    solidity_code += "}\n"
    return solidity_code

def main():
    input_file_parent = Path(__file__).parent.parent / 'result.json'  # Путь к родительской папке
    input_file_temp = Path(__file__).parent.parent / 'Temp' / 'result.json'  # Путь к папке Temp
    output_file = 'output.sol'

    try:
        # Попробуем открыть result.json из родительской папки или из папки Temp
        if input_file_parent.exists():
            input_file = input_file_parent
        elif input_file_temp.exists():
            input_file = input_file_temp
        else:
            raise FileNotFoundError("Error: 'result.json' file not found in both parent or Temp folders.")

        with open(input_file) as f:
            data = json.load(f)

        contract = generate_solidity_contract(data)

        with open(output_file, 'w') as f:
            f.write(contract)

        print(f"Contract generated successfully: {output_file}")

        # Перемещение в Hardhat/contracts/GeneratedContract.sol
        target_dir = Path(__file__).parent.parent.parent / 'Hardhat' / 'contracts'
        target_dir.mkdir(parents=True, exist_ok=True)
        final_path = target_dir / "GeneratedContract.sol"

        shutil.move(output_file, final_path)
        print(f"Contract moved to {final_path}")

    except FileNotFoundError as e:
        print(e)
    except json.JSONDecodeError:
        print(f"Error: '{input_file}' is not a valid JSON file.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
