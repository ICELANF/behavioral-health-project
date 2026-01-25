# 评估数据目录 (Assessment Data Directory)

此目录用于存放 HRV 生理数据、心理测评数据和 PDF 报告。

## 目录结构

```
data/assessments/
├── raw/                          # 原始数据 (从设备/平台导出)
│   ├── batch_2026-01-10/         # 按批次日期组织
│   │   ├── 9348/                 # 设备ID作为用户标识
│   │   │   ├── physio.xlsx       # 生理测评数据
│   │   │   ├── psych.xlsx        # 心理测评数据
│   │   │   └── report.pdf        # PDF报告
│   │   ├── BEB2/
│   │   └── ...
│   └── batch_2026-01-15/
│
├── processed/                    # 处理后的标准化数据
│   ├── users/                    # 按用户组织
│   │   ├── FDBC03D79348/         # 完整设备ID
│   │   │   ├── profile.json      # 用户档案
│   │   │   ├── assessments/      # 历次评估
│   │   │   │   ├── 2026-01-10.json
│   │   │   │   └── 2026-01-15.json
│   │   │   └── prescriptions/    # 历次处方
│   │   │       └── 2026-01-10.json
│   │   └── ...
│   └── index.json                # 用户索引
│
├── exports/                      # 导出的报告
│   ├── individual/               # 个人看板导出
│   │   └── FDBC03D79348_2026-01-10.docx
│   └── group/                    # 群体看板导出
│       └── batch_2026-01-10_summary.docx
│
└── README.md
```

## 数据格式

### 标准化评估 JSON (processed/users/{id}/assessments/{date}.json)

```json
{
  "assessment_id": "ASS-20260110-9348",
  "user_id": "FDBC03D79348",
  "assessment_date": "2026-01-10",
  "assessment_time": "11:46-12:08",
  "duration_minutes": 21,
  "device": "海棠心智-C2",

  "physio_data": {
    "heart_rate": {
      "avg": 78,
      "min": 76,
      "max": 81,
      "unit": "bpm"
    },
    "hrv": {
      "sdnn": 50,
      "rmssd": 43,
      "unit": "ms"
    },
    "autonomic_balance": "balanced"
  },

  "psych_data": {
    "stress_index": 55,
    "fatigue_index": 50,
    "mood_index": 47,
    "composite_score": 64,
    "emotion_distribution": {
      "calm": 0.33,
      "relaxed": 0.33,
      "peaceful": 0.33
    }
  },

  "risk_assessment": {
    "level": "needs_attention",
    "score_range": "61-80",
    "flags": []
  },

  "source_files": {
    "physio_xlsx": "raw/batch_2026-01-10/9348/physio.xlsx",
    "psych_xlsx": "raw/batch_2026-01-10/9348/psych.xlsx",
    "report_pdf": "raw/batch_2026-01-10/9348/report.pdf"
  }
}
```

## 使用方法

### 1. 导入原始数据

```bash
# 从情绪评估报告目录批量导入
python scripts/assessment_importer.py --source "D:\情绪评估报告\情绪评估报告" --batch "2026-01-10"
```

### 2. 生成个人处方

```bash
# 为单个用户生成处方
python scripts/prescription_engine.py --user FDBC03D79348 --date 2026-01-10
```

### 3. 生成看板

```bash
# 个人看板
python scripts/dashboard_generator.py --type individual --user FDBC03D79348

# 群体看板
python scripts/dashboard_generator.py --type group --batch 2026-01-10
```
