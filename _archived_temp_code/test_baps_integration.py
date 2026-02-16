# -*- coding: utf-8 -*-
"""
BAPS系统完整集成测试
验证评估流程从问卷获取到报告生成的完整链路
"""

import requests
import json
import sys

BAPS_API_URL = "http://localhost:8001"

def test_baps_integration():
    print("=" * 70)
    print("  XingJian BAPS System Integration Test")
    print("=" * 70)

    # 1. 测试服务健康状态
    print("\n[Step 1] Check BAPS API status...")
    try:
        r = requests.get(f"{BAPS_API_URL}/health", timeout=5)
        if r.status_code == 200:
            print(f"  [OK] Service healthy: {r.json()}")
        else:
            print(f"  [FAIL] Service error: {r.status_code}")
            return False
    except Exception as e:
        print(f"  [FAIL] Connection failed: {e}")
        return False

    # 2. 获取问卷列表
    print("\n[Step 2] 获取可用问卷列表...")
    r = requests.get(f"{BAPS_API_URL}/questionnaires")
    questionnaires = r.json()["questionnaires"]
    for q in questionnaires:
        print(f"  - {q['name']} ({q['total_items']}题, 约{q['estimated_minutes']}分钟)")

    # 3. 获取BPT-6问卷题目
    print("\n[Step 3] 获取BPT-6问卷题目...")
    r = requests.get(f"{BAPS_API_URL}/questionnaires/bpt6")
    bpt6_data = r.json()
    print(f"  问卷名称: {bpt6_data['name']}")
    print(f"  题目数量: {bpt6_data['total_items']}")
    print(f"  量表类型: {bpt6_data['scale']['type']} ({bpt6_data['scale']['range']})")
    print(f"  前3题示例:")
    for item in bpt6_data['items'][:3]:
        print(f"    {item['id']}: {item['text']}")

    # 4. 模拟用户作答并提交BPT-6评估
    print("\n[Step 4] 提交BPT-6评估...")
    bpt6_answers = {
        "user_id": "integration_test_user",
        "answers": {
            "BPT1": 5, "BPT2": 4, "BPT3": 5,  # 行动型高分
            "BPT4": 4, "BPT5": 4, "BPT6": 4,  # 知识型中高
            "BPT7": 2, "BPT8": 2, "BPT9": 2,  # 情绪型低
            "BPT10": 3, "BPT11": 3, "BPT12": 3,  # 关系型中
            "BPT13": 3, "BPT14": 3, "BPT15": 3,  # 环境型中
            "BPT16": 2, "BPT17": 2, "BPT18": 2   # 矛盾型低
        }
    }

    r = requests.post(f"{BAPS_API_URL}/assess/bpt6", json=bpt6_answers)
    bpt6_result = r.json()
    print(f"  主导类型: {bpt6_result['summary']['primary_type_name']}")
    print(f"  类型得分:")
    for label, value in zip(bpt6_result['visualization_data']['labels'],
                           bpt6_result['visualization_data']['values']):
        bar = "#" * (value // 2) + "." * (7 - value // 2)
        print(f"    {label}: {bar} {value}分")
    print(f"  推荐策略: {', '.join(bpt6_result['intervention']['recommended_strategies'])}")

    # 5. 测试SPI评估
    print("\n[Step 5] 提交SPI成功可能性评估...")
    spi_answers = {
        "user_id": "integration_test_user",
        "answers": {f"SPI{i}": 4 for i in range(1, 51)}  # 所有题目答4分
    }

    r = requests.post(f"{BAPS_API_URL}/assess/spi", json=spi_answers)
    spi_result = r.json()
    print(f"  SPI指数: {spi_result['summary']['spi_score']}")
    print(f"  成功水平: {spi_result['summary']['success_label']} ({spi_result['summary']['success_rate']})")
    print(f"  建议策略: {spi_result['summary']['strategy']}")
    print(f"  各维度分析:")
    for dim, data in spi_result['dimensions'].items():
        status = data['analysis']
        print(f"    {data['name']}: {data['raw_score']}分 ({status})")

    # 6. 测试完整综合评估
    print("\n[Step 6] 执行完整综合评估...")
    r = requests.post(f"{BAPS_API_URL}/test/full-assessment")
    full_result = r.json()

    print(f"\n  === 综合评估报告 ===")
    print(f"  {full_result['executive_summary']}")

    print(f"\n  === 交叉分析 ===")
    cross = full_result['cross_analysis']
    print(f"  人格-行为匹配: {cross['personality_behavior_match']}")
    print(f"  改变准备度: {cross['change_readiness']}")
    if cross['key_strengths']:
        print(f"  关键优势: {', '.join(cross['key_strengths'])}")
    if cross['key_barriers']:
        print(f"  关键障碍: {', '.join(cross['key_barriers'])}")

    print(f"\n  === 核心建议 ===")
    for i, rec in enumerate(full_result['overall_recommendations'], 1):
        print(f"  {i}. {rec}")

    # 7. 测试Dify集成Schema
    print("\n[Step 7] 获取Dify集成Schema...")
    r = requests.get(f"{BAPS_API_URL}/openapi-tools.json")
    schema = r.json()
    print(f"  Schema版本: {schema['info']['version']}")
    print(f"  可用端点:")
    for path, methods in schema['paths'].items():
        for method, details in methods.items():
            print(f"    {method.upper()} {path}: {details.get('summary', '')}")

    print("\n" + "=" * 70)
    print("  [OK] BAPS 系统集成测试全部通过!")
    print("=" * 70)

    # 打印Dify集成说明
    print("""
  [Info] Dify集成说明:
  -----------------
  1. 在Dify中创建「自定义工具」
  2. 从URL导入Schema: http://localhost:8001/openapi-tools.json
  3. 在工作流中使用HTTP请求节点调用评估API
  4. 使用LLM节点解读评估结果

  可用API端点:
  - POST /assess/bpt6     - 行为模式分型 (18题)
  - POST /assess/spi      - 成功可能性评估 (50题)
  - POST /assess/capacity - 改变潜力诊断 (32题)
  - POST /assess/big_five - 大五人格测评 (50题)
  - POST /assess/comprehensive - 综合评估 (全部)
    """)

    return True


if __name__ == "__main__":
    success = test_baps_integration()
    sys.exit(0 if success else 1)
