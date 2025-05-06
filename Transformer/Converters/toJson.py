import re
import json
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
import sys

grouped_functions = {}

# Регулярное выражение для извлечения адреса (например, адрес в формате 0x...)
address_regex = r"=\s*(0x[a-fA-F0-9]{40})"

def extract_bpmn_actions_with_comments(bpmn_file, output_json='result.json'):
    tree = ET.parse(bpmn_file)
    root = tree.getroot()

    namespaces = {
        'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'
    }

    actions = []
    annotations = {}
    lanes = {}

    # Извлекаем комментарии
    for text_annotation in root.findall('.//bpmn:textAnnotation', namespaces):
        annotation_id = text_annotation.get('id')
        text = text_annotation.find('.//bpmn:text', namespaces)
        if text is not None:
            annotations[annotation_id] = text.text

    # Извлекаем данные о lane и их адресах
    for lane in root.findall('.//bpmn:lane', namespaces):
        lane_id = lane.get('id')  # Получаем ID лейны
        lane_name = lane.get('name', 'Unnamed Lane').strip()  # Убираем пробелы с обеих сторон имени лейны

        # Разделяем строку по " = " и сохраняем части
        split_lane_name = lane_name.split(" = ")

        lanes[lane_id] = {
            'lane_name': split_lane_name[0],  # Сохраняем имя роли до " = "
            'address': split_lane_name[1] if len(split_lane_name) > 1 else ""  # Сохраняем адрес после " = ", если есть
        }


    for task in root.findall('.//bpmn:task', namespaces):
        task_name = task.get('name') or 'Unnamed Function'
        task_id = task.get('id')
        assignee = 'Unknown'

        for lane_id, lane_info in lanes.items():
            for flowNodeRef in root.findall(f'.//bpmn:lane[@id="{lane_id}"]/bpmn:flowNodeRef', namespaces):
                if flowNodeRef.text == task_id:
                    assignee = lane_info['lane_name']
                    break

        comment = ''
        for association in root.findall('.//bpmn:association', namespaces):
            if association.get('sourceRef') == task_id:
                target_ref = association.get('targetRef')
                if target_ref in annotations:
                    comment = annotations[target_ref]
                    break

        blocks = {}
        current_block = None
        for line in comment.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.endswith(':'):
                current_block = line[:-1].strip()
                blocks[current_block] = []
            elif current_block:
                blocks[current_block].append(line)

        parsed_actions = {
            "Set": [],
            "Get": [],
            "Pay": [],
            "End": []
        }

        if task_name in grouped_functions:
            if assignee not in grouped_functions[task_name]["assignees"]:
                grouped_functions[task_name]["assignees"].append(assignee)
        else:
            grouped_functions[task_name] = {
                "assignees": [assignee],
                "actions": parsed_actions
            }

        for action_type, lines in blocks.items():
            if action_type.lower() == 'pay':
                for line in lines:
                    if 'to' in line:
                        parts = line.replace(';', '').split('to')
                        amount = parts[0].strip()
                        to = parts[1].strip()
                        parsed_actions["Pay"].append({
                            "amount": amount,
                            "to": to
                        })
            if action_type.lower() == 'end':
                for line in lines:
                    if 'Success' or 'Failed' in line:
                        parsed_actions["End"].append({
                            "status": line,
                        })    
            else:
                for line in lines:
                    line = line.replace(';', '').strip()
                    if '=' in line:
                        left, value = line.split('=', 1)
                        var_parts = left.strip().split(' ')
                        var_type = var_parts[0]
                        var_name = var_parts[1] if len(var_parts) > 1 else var_parts[0]
                        parsed_actions[action_type].append({
                            "type": var_type,
                            "name": var_name,
                            "variable": value.strip() if value.strip() else "null"
                        })
                    else:
                        parts = line.split(' ')
                        if len(parts) >= 2:
                            var_type, var_name = parts[0], parts[1]
                        else:
                            var_type = var_name = parts[0]
                        parsed_actions[action_type].append({
                            "type": var_type,
                            "name": var_name,
                            "variable": "null"
                        })

        action_entry = {
            "function_name": task_name,
            "assignee": assignee,
            "actions": parsed_actions
        }

        actions.append(action_entry)

    result = {
        "lanes": [
            {'lane_name': lane_info['lane_name'], 'address': lane_info['address']}
            for lane_info in lanes.values()
        ],
        "functions": []
    }

    for func_name, data in grouped_functions.items():
        result["functions"].append({
            "function_name": func_name,
            "assignee": data["assignees"],
            "actions": data["actions"]
        })

    # Получаем путь к папке Temp, которая находится на один уровень выше
    output_dir = Path(__file__).parent.parent / 'Temp'
    output_dir.mkdir(parents=True, exist_ok=True)  # Создаем папку Temp, если она не существует
    output_path = output_dir / 'result.json'

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print(f"JSON file saved to: {output_path}")
    return result

def main():
    if len(sys.argv) < 2:
        print("Usage: python toJson.py <input_bpmn_file>")
        sys.exit(1)

    input_bpmn = sys.argv[1]
    extract_bpmn_actions_with_comments(input_bpmn, 'result.json')
    print("JSON extraction completed successfully.")

if __name__ == "__main__":
    main()
