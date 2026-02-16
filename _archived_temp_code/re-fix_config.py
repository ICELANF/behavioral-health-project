import yaml

config_path = 'config.yaml'
try:
    # 1. 尝试读取（即使格式有点乱）
    with open(config_path, 'r', encoding='utf-8') as f:
        # 如果 safe_load 失败，我们进行字符串清理
        lines = f.readlines()
    
    # 清理每一行，确保路径被正确替换，且没有非法字符
    new_lines = []
    for line in lines:
        if 'J:/xingjian-agent/prompts' in line:
            line = line.replace('J:/xingjian-agent/prompts', 'xingjian-agent/prompts')
        new_lines.append(line)
    
    # 写回文件
    with open(config_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print('[OK] config.yaml 已尝试通过字符串模式修复')
except Exception as e:
    print(f'[Error] 修复失败: {e}')
