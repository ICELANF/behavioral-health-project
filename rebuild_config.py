import yaml

config_path = 'config.yaml'

# 定义标准的配置结构
base_config = {
    'project_name': '行健行为教练 [八爪鱼引擎版]',
    'version': '1.0.0',
    'agents': {
        'mental_health': {
            'path': 'xingjian-agent/prompts/mental_health.txt',
            'model': 'qwen2.5:7b'
        },
        'nutrition': {
            'path': 'xingjian-agent/prompts/nutrition.txt',
            'model': 'qwen2.5:7b'
        },
        'sports_rehab': {
            'path': 'xingjian-agent/prompts/sports_rehab.txt',
            'model': 'qwen2.5:7b'
        },
        'tcm_wellness': {
            'path': 'xingjian-agent/prompts/tcm_wellness.txt',
            'model': 'qwen2.5:7b'
        }
    },
    'server': {
        'host': '0.0.0.0',
        'port': 8000
    }
}

try:
    with open(config_path, 'w', encoding='utf-8') as f:
        # 使用 standard flow style 为 False 确保生成易读的缩进格式
        yaml.dump(base_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print('[OK] config.yaml 已成功重建，格式已标准化')
except Exception as e:
    print(f'[Error] 写入失败: {e}')
