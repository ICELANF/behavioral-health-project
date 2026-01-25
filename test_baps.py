# -*- coding: utf-8 -*-
"""BAPS系统测试脚本"""

import sys
import os

# 确保项目目录在路径中
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.baps.scoring_engine import BAPSScoringEngine
from core.baps.report_generator import BAPSReportGenerator

def test_baps():
    print("=" * 60)
    print("  行健行为教练 BAPS 系统测试")
    print("=" * 60)

    engine = BAPSScoringEngine()
    generator = BAPSReportGenerator()

    # 1. 测试BPT-6
    print("\n[1] BPT-6 行为分型测试")
    bpt6_answers = {
        'BPT1': 5, 'BPT2': 5, 'BPT3': 5,  # 行动型高分
        'BPT4': 3, 'BPT5': 3, 'BPT6': 3,
        'BPT7': 2, 'BPT8': 2, 'BPT9': 2,
        'BPT10': 3, 'BPT11': 3, 'BPT12': 3,
        'BPT13': 3, 'BPT14': 3, 'BPT15': 3,
        'BPT16': 2, 'BPT17': 2, 'BPT18': 2
    }
    bpt6_result = engine.score_bpt6(bpt6_answers, 'test_user')
    print(f"  主导类型: {bpt6_result.primary_type}")
    print(f"  类型得分: {bpt6_result.type_scores}")
    print(f"  推荐策略: {bpt6_result.intervention_strategies}")

    # 2. 测试SPI
    print("\n[2] SPI 成功可能性测试")
    spi_answers = {f'SPI{i}': 4 for i in range(1, 51)}
    spi_result = engine.score_spi(spi_answers, 'test_user')
    print(f"  SPI指数: {spi_result.spi_score}")
    print(f"  成功水平: {spi_result.success_label} ({spi_result.success_rate})")
    print(f"  建议策略: {spi_result.strategy}")

    # 3. 测试CAPACITY
    print("\n[3] CAPACITY 改变潜力测试")
    capacity_answers = {f'CAP{i}': 4 for i in range(1, 33)}
    capacity_result = engine.score_capacity(capacity_answers, 'test_user')
    print(f"  总分: {capacity_result.total_score}/160")
    print(f"  潜力水平: {capacity_result.potential_label}")
    print(f"  建议策略: {capacity_result.strategy}")

    # 4. 测试大五人格
    print("\n[4] 大五人格测试")
    big_five_answers = {}
    for dim in ['E', 'N', 'C', 'A', 'O']:
        for i in range(1, 11):
            big_five_answers[f'{dim}{i}'] = 2  # 中等偏高
    big_five_result = engine.score_big_five(big_five_answers, 'test_user')
    print(f"  人格画像: {big_five_result.personality_profile}")
    print(f"  主导特质: {big_five_result.dominant_traits}")
    for dim, score in big_five_result.dimension_scores.items():
        print(f"    {score.name}: {score.raw_score} ({score.label})")

    print("\n" + "=" * 60)
    print("  BAPS 系统测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_baps()
