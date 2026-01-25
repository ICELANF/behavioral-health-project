# -*- coding: utf-8 -*-
"""
五大人格测评 PDF 报告生成器
使用 HTML 模板生成可打印的报告
"""

import json
from datetime import datetime
from typing import Dict
import webbrowser
import os


class PDFReportGenerator:
    """PDF 报告生成器（通过 HTML 打印为 PDF）"""

    TRAIT_INFO = {
        'E': {
            'name': '外向性',
            'name_en': 'Extraversion',
            'color': '#3498db',
            'high': '你精力充沛，热情开朗，喜欢社交活动，善于表达自己。你乐于成为人群中的焦点，从与他人的互动中获得能量。',
            'mid': '你在社交和独处之间保持良好的平衡，能够根据情境灵活调整自己的社交风格。',
            'low': '你更喜欢安静的环境和深度的人际关系。你善于倾听和独立思考，从独处中获得能量。'
        },
        'N': {
            'name': '情绪稳定性',
            'name_en': 'Emotional Stability',
            'color': '#9b59b6',
            'high': '你情绪稳定，心态平和，能够从容应对压力和挫折。你很少感到焦虑或情绪波动。',
            'mid': '你的情绪稳定性处于正常水平，能够应对大多数日常压力，偶尔会有情绪起伏。',
            'low': '你情感丰富，对环境变化较为敏感。建议学习一些情绪调节技巧，以更好地应对压力。'
        },
        'C': {
            'name': '尽责性',
            'name_en': 'Conscientiousness',
            'color': '#2ecc71',
            'high': '你做事有条理，自律性强，目标明确。你可靠、勤奋，善于规划和执行任务，是值得信赖的人。',
            'mid': '你在组织性和灵活性之间保持平衡，既能按计划行事，也能适应变化。',
            'low': '你更喜欢灵活自由的方式，不喜欢过多的规则约束。你可能更注重当下体验而非长期规划。'
        },
        'A': {
            'name': '宜人性',
            'name_en': 'Agreeableness',
            'color': '#e74c3c',
            'high': '你善解人意，乐于助人，与人相处融洽。你富有同情心，重视和谐的人际关系，容易赢得他人信任。',
            'mid': '你在合作与坚持自我之间保持平衡，既能体谅他人，也能在必要时坚持自己的立场。',
            'low': '你更注重客观和理性分析，不会轻易被情感左右。你独立思考，敢于表达不同意见。'
        },
        'O': {
            'name': '开放性',
            'name_en': 'Openness',
            'color': '#f39c12',
            'high': '你富有想象力和创造力，喜欢探索新事物和新观点。你对艺术、美学有较高的敏感度，思维活跃开放。',
            'mid': '你在接受新事物方面持平衡态度，既能欣赏创新，也重视传统经验和实际验证。',
            'low': '你更偏好实际和具体的事物，喜欢熟悉的环境和经过验证的方法。你务实稳重，注重实际效果。'
        }
    }

    SCORE_LEVELS = [
        {'range': (28, 40), 'level': '极高水平'},
        {'range': (16, 27), 'level': '高水平'},
        {'range': (4, 15), 'level': '中高水平'},
        {'range': (-3, 3), 'level': '中等水平'},
        {'range': (-15, -4), 'level': '中低水平'},
        {'range': (-27, -16), 'level': '低水平'},
        {'range': (-40, -28), 'level': '极低水平'}
    ]

    def __init__(self):
        pass

    def get_level(self, score: int) -> str:
        for level_info in self.SCORE_LEVELS:
            if level_info['range'][0] <= score <= level_info['range'][1]:
                return level_info['level']
        return '中等水平'

    def get_description(self, trait: str, score: int) -> str:
        info = self.TRAIT_INFO[trait]
        if score >= 16:
            return info['high']
        elif score >= -3:
            return info['mid']
        else:
            return info['low']

    def generate_html_report(self, scores: Dict[str, int], name: str = "") -> str:
        """生成 HTML 格式报告"""

        trait_order = ['E', 'N', 'C', 'A', 'O']
        date_str = datetime.now().strftime('%Y年%m月%d日')

        # 生成各维度结果 HTML
        traits_html = ""
        for trait in trait_order:
            score = scores[trait]
            info = self.TRAIT_INFO[trait]
            level = self.get_level(score)
            description = self.get_description(trait, score)
            position = ((score + 40) / 80) * 100

            traits_html += f'''
            <div class="trait-card">
                <div class="trait-header">
                    <div class="trait-name" style="border-left: 4px solid {info['color']}; padding-left: 12px;">
                        {info['name']} <span class="trait-en">({info['name_en']})</span>
                    </div>
                    <div class="trait-score" style="color: {info['color']}">
                        {'+' if score > 0 else ''}{score}
                    </div>
                </div>
                <div class="trait-bar">
                    <div class="bar-bg">
                        <div class="bar-marker" style="left: {position}%"></div>
                    </div>
                    <div class="bar-labels">
                        <span>-40</span>
                        <span>0</span>
                        <span>+40</span>
                    </div>
                </div>
                <div class="trait-level" style="background: {info['color']}">{level}</div>
                <div class="trait-description">{description}</div>
            </div>
            '''

        # 生成剖面图 HTML
        profile_html = ""
        for trait in trait_order:
            score = scores[trait]
            info = self.TRAIT_INFO[trait]
            position = ((score + 40) / 80) * 100

            profile_html += f'''
            <div class="profile-row">
                <div class="profile-label">{info['name']}</div>
                <div class="profile-bar">
                    <div class="profile-line"></div>
                    <div class="profile-marker" style="left: {position}%; background: {info['color']}"></div>
                </div>
                <div class="profile-score" style="color: {info['color']}">{'+' if score > 0 else ''}{score}</div>
            </div>
            '''

        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>五大人格测评报告</title>
    <style>
        @page {{
            size: A4;
            margin: 20mm;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
            line-height: 1.6;
            color: #333;
            background: white;
            padding: 40px;
        }}

        .report-header {{
            text-align: center;
            border-bottom: 3px solid #667eea;
            padding-bottom: 30px;
            margin-bottom: 30px;
        }}

        .report-title {{
            font-size: 28px;
            color: #2d3748;
            margin-bottom: 10px;
        }}

        .report-subtitle {{
            color: #667eea;
            font-size: 16px;
        }}

        .report-meta {{
            margin-top: 20px;
            color: #666;
            font-size: 14px;
        }}

        .section {{
            margin-bottom: 30px;
        }}

        .section-title {{
            font-size: 18px;
            color: #2d3748;
            border-left: 4px solid #667eea;
            padding-left: 12px;
            margin-bottom: 20px;
        }}

        .trait-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            page-break-inside: avoid;
        }}

        .trait-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}

        .trait-name {{
            font-size: 16px;
            font-weight: bold;
            color: #2d3748;
        }}

        .trait-en {{
            font-weight: normal;
            color: #888;
            font-size: 14px;
        }}

        .trait-score {{
            font-size: 24px;
            font-weight: bold;
        }}

        .trait-bar {{
            margin-bottom: 15px;
        }}

        .bar-bg {{
            position: relative;
            height: 20px;
            background: linear-gradient(90deg, #e74c3c 0%, #f39c12 25%, #2ecc71 50%, #f39c12 75%, #e74c3c 100%);
            border-radius: 10px;
        }}

        .bar-marker {{
            position: absolute;
            top: -3px;
            width: 12px;
            height: 26px;
            background: #2d3748;
            border-radius: 3px;
            transform: translateX(-50%);
        }}

        .bar-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #888;
            margin-top: 5px;
        }}

        .trait-level {{
            display: inline-block;
            color: white;
            padding: 4px 16px;
            border-radius: 20px;
            font-size: 14px;
            margin-bottom: 10px;
        }}

        .trait-description {{
            color: #4a5568;
            font-size: 14px;
            line-height: 1.8;
        }}

        .profile-section {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 30px;
        }}

        .profile-row {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }}

        .profile-label {{
            width: 100px;
            font-size: 14px;
            color: #2d3748;
        }}

        .profile-bar {{
            flex: 1;
            position: relative;
            height: 16px;
            margin: 0 15px;
        }}

        .profile-line {{
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 4px;
            background: #e0e0e0;
            transform: translateY(-50%);
            border-radius: 2px;
        }}

        .profile-marker {{
            position: absolute;
            top: 50%;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            transform: translate(-50%, -50%);
            border: 3px solid white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}

        .profile-score {{
            width: 50px;
            text-align: right;
            font-weight: bold;
            font-size: 14px;
        }}

        .score-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}

        .score-table th, .score-table td {{
            border: 1px solid #e0e0e0;
            padding: 10px;
            text-align: center;
            font-size: 13px;
        }}

        .score-table th {{
            background: #667eea;
            color: white;
        }}

        .score-table tr:nth-child(even) {{
            background: #f8f9fa;
        }}

        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            text-align: center;
            color: #888;
            font-size: 12px;
        }}

        @media print {{
            body {{
                padding: 0;
            }}

            .no-print {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="report-header">
        <h1 class="report-title">五大人格特质测评报告</h1>
        <div class="report-subtitle">Big Five Personality Assessment Report</div>
        <div class="report-meta">
            {f'<div>姓名：{name}</div>' if name else ''}
            <div>测评日期：{date_str}</div>
        </div>
    </div>

    <div class="section">
        <h2 class="section-title">人格剖面图</h2>
        <div class="profile-section">
            {profile_html}
            <div style="display: flex; justify-content: space-between; font-size: 12px; color: #888; margin-top: 10px; padding: 0 115px;">
                <span>-40 (极低)</span>
                <span>0 (中等)</span>
                <span>+40 (极高)</span>
            </div>
        </div>
    </div>

    <div class="section">
        <h2 class="section-title">各维度详细分析</h2>
        {traits_html}
    </div>

    <div class="section">
        <h2 class="section-title">分数等级参照表</h2>
        <table class="score-table">
            <tr>
                <th>分数范围</th>
                <th>水平描述</th>
            </tr>
            <tr><td>+28 到 +40</td><td>极高水平</td></tr>
            <tr><td>+16 到 +27</td><td>高水平</td></tr>
            <tr><td>+4 到 +15</td><td>中高水平</td></tr>
            <tr><td>-3 到 +3</td><td>中等水平</td></tr>
            <tr><td>-15 到 -4</td><td>中低水平</td></tr>
            <tr><td>-27 到 -16</td><td>低水平</td></tr>
            <tr><td>-40 到 -28</td><td>极低水平</td></tr>
        </table>
    </div>

    <div class="footer">
        <p>本测评仅供参考，不作为专业心理诊断依据。</p>
        <p>如需专业心理评估，请咨询持证心理咨询师或临床心理学家。</p>
    </div>

    <div class="no-print" style="text-align: center; margin-top: 30px;">
        <button onclick="window.print()" style="padding: 12px 30px; font-size: 16px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer;">
            打印/保存为 PDF
        </button>
    </div>
</body>
</html>'''

        return html

    def save_and_open(self, scores: Dict[str, int], name: str = "", filename: str = "personality_report.html"):
        """保存 HTML 并在浏览器中打开"""
        html = self.generate_html_report(scores, name)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

        # 在浏览器中打开
        abs_path = os.path.abspath(filename)
        webbrowser.open(f'file://{abs_path}')

        print(f"报告已生成: {filename}")
        print("请在浏览器中使用 Ctrl+P 打印为 PDF")


def demo():
    """演示模式"""
    import random

    # 生成随机分数
    scores = {
        'E': random.randint(-40, 40),
        'N': random.randint(-40, 40),
        'C': random.randint(-40, 40),
        'A': random.randint(-40, 40),
        'O': random.randint(-40, 40)
    }

    print("生成的随机分数:")
    for trait, score in scores.items():
        print(f"  {trait}: {score:+d}")

    generator = PDFReportGenerator()
    generator.save_and_open(scores, name="测试用户")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        print("用法: python generate_pdf_report.py --demo")
        print("或在代码中调用 PDFReportGenerator 类")
