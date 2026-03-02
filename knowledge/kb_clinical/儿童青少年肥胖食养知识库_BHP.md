# 儿童青少年肥胖食养知识库

## BHP行为健康数字平台 · 知识管理系统（KMS）

**来源文献**：《儿童青少年肥胖食养指南（2024年版）》— 国家卫生健康委办公厅  
**知识域**：儿童青少年肥胖（Childhood Obesity, COB）  
**适用人群**：2～17岁肥胖及超重儿童青少年  
**服务对象**：基层卫生工作者、营养指导人员、家长、校医、行为健康教练  
**版本**：v1.0  
**生成日期**：2026-02-26  

---

## 一、健康指标定义（Health Indicators）

```python
# ============================================
# 儿童青少年肥胖相关健康指标
# ============================================

CHILD_OBESITY_INDICATORS = {
    "HI-COB-BMI": HealthIndicator(
        indicator_id="HI-COB-BMI",
        name="儿童青少年BMI",
        description="体质指数，根据年龄性别对照界值判断超重/肥胖",
        unit="kg/m²",
        normal_range={
            "note": "参照WS/T 586《学龄儿童青少年超重与肥胖筛查》及WS/T 423《7岁以下儿童生长标准》",
            "example_10岁男": {"超重": 19.2, "肥胖": 21.9},
            "example_10岁女": {"超重": 19.5, "肥胖": 21.5}
        },
        risk_thresholds={
            "overweight": "≥年龄性别超重界值",
            "obese": "≥年龄性别肥胖界值"
        },
        measurement_method="身高体重计计算",
        frequency="正常体重：每月1次；肥胖儿童：每周1次",
        related_dimensions=[LifeDimension.NUTRITION, LifeDimension.EXERCISE]
    ),
    
    "HI-COB-WAIST": HealthIndicator(
        indicator_id="HI-COB-WAIST",
        name="儿童青少年腰围",
        description="用于判定中心型肥胖，与高血压、高脂血症、糖尿病关系密切",
        unit="cm",
        normal_range={
            "note": "参照WS/T 611《7岁～18岁儿童青少年高腰围筛查界值》",
            "example_10岁男": {"P75": 65.9, "P90_中心型肥胖": 73.1},
            "example_10岁女": {"P75": 62.2, "P90_中心型肥胖": 67.8}
        },
        risk_thresholds={
            "central_overweight": "≥P75且<P90",
            "central_obese": "≥P90"
        },
        measurement_method="软尺测量脐水平",
        frequency="学校每年监测；肥胖儿童每月1次",
        related_dimensions=[LifeDimension.NUTRITION, LifeDimension.EXERCISE]
    ),
    
    "HI-COB-WHtR": HealthIndicator(
        indicator_id="HI-COB-WHtR",
        name="腰围身高比",
        description="辅助判定中心型肥胖的指标",
        unit="无量纲",
        normal_range={
            "6-17岁男生及6-9岁女生": {"中心型肥胖界值": ">0.48"},
            "10-17岁女生": {"中心型肥胖界值": ">0.46"}
        },
        measurement_method="腰围(cm)/身高(cm)",
        frequency="同腰围监测频率",
        related_dimensions=[LifeDimension.NUTRITION]
    ),
    
    "HI-COB-ENERGY": HealthIndicator(
        indicator_id="HI-COB-ENERGY",
        name="每日膳食能量摄入",
        description="根据年龄、性别、身体活动水平确定的能量需要量",
        unit="kcal/天",
        normal_range={
            "6-10岁男": {"range": "1600-2050"},
            "6-10岁女": {"range": "1450-1900"},
            "11-13岁男": {"range": "2200-2600"},
            "11-13岁女": {"range": "2000-2200"},
            "14-17岁男": {"range": "2600-2950"},
            "14-17岁女": {"range": "2200-2350"}
        },
        risk_thresholds={
            "obesity_reduction": "在正常需要量基础上减少约20%"
        },
        measurement_method="膳食记录+计算",
        frequency="日常监测",
        related_dimensions=[LifeDimension.NUTRITION]
    ),
    
    "HI-COB-PA": HealthIndicator(
        indicator_id="HI-COB-PA",
        name="每日身体活动时长",
        description="中高强度身体活动时间",
        unit="分钟/天",
        normal_range={
            "学龄前(2-5岁)": {"总活动": "≥180分钟", "户外": "≥120分钟"},
            "学龄(6-17岁)": {"中高强度": "≥60分钟"},
            "肥胖儿童起始": {"中高强度": "20分钟，逐步增至20-60分钟"}
        },
        measurement_method="运动记录/手环",
        frequency="每日",
        related_dimensions=[LifeDimension.EXERCISE]
    ),
    
    "HI-COB-SLEEP": HealthIndicator(
        indicator_id="HI-COB-SLEEP",
        name="儿童青少年睡眠时长",
        description="根据年龄段推荐的每日睡眠时间",
        unit="小时/天",
        normal_range={
            "5岁以下": {"推荐": "10-13"},
            "6-12岁": {"推荐": "9-12"},
            "13-17岁": {"推荐": "8-10"}
        },
        measurement_method="睡眠日志",
        frequency="每日",
        related_dimensions=[LifeDimension.SLEEP]
    ),
    
    "HI-COB-SCREEN": HealthIndicator(
        indicator_id="HI-COB-SCREEN",
        name="每日视屏时间",
        description="看电视、手机等电子屏幕的时间",
        unit="小时/天",
        normal_range={
            "学龄前": {"上限": "≤1小时"},
            "学龄": {"上限": "≤2小时"}
        },
        risk_thresholds={
            "elevated": "超过年龄段上限"
        },
        measurement_method="家长记录",
        frequency="每日",
        related_dimensions=[LifeDimension.RISK_FACTOR]
    ),
}
```

---

## 二、知识条目（Knowledge Items）

### 2.1 疾病认知与评估

```python
KnowledgeItem(
    knowledge_id="KI-COB-001",
    title="儿童青少年肥胖的定义、分型与判定标准",
    content="""
一、肥胖的定义

肥胖是人体脂肪积聚过多达到危害健康程度的一种慢性代谢性疾病，是因能量摄入超过能量消耗或机体代谢改变而导致体重过度增长的一种状态。

原发性肥胖（单纯性肥胖）是排除继发于下丘脑-垂体-肾上腺轴病变、肿瘤、创伤、皮质醇增多症、遗传性疾病等原因，主要由不健康生活方式（如高能量摄入、身体活动不足）造成的肥胖。

二、判定标准

1. 2～5岁儿童
   评价方法：身高别体重或年龄别BMI标准差法
   - ≥+1SD且<+2SD → 超重
   - ≥+2SD且<+3SD → 肥胖
   - ≥+3SD → 重度肥胖
   参照标准：WS/T 423《7岁以下儿童生长标准》

2. 6～17岁儿童青少年
   评价方法：BMI对照年龄性别界值
   - BMI≥超重界值且<肥胖界值 → 超重
   - BMI≥肥胖界值 → 肥胖
   参照标准：WS/T 586《学龄儿童青少年超重与肥胖筛查》

3. 中心型肥胖判定（6～17岁）
   方法一：腰围≥P90 → 中心型肥胖
   方法二：腰围身高比
   - 6-17岁男生、6-9岁女生 >0.48 → 中心型肥胖
   - 10-17岁女生 >0.46 → 中心型肥胖

三、中心型肥胖的意义

中心型肥胖主要是腹腔内和腹壁脂肪蓄积过多，与高血压、高脂血症、糖尿病等疾病的关系更为密切，需要特别关注。

四、我国流行现状

- 6岁以下儿童肥胖率：3.6%
- 6～17岁儿童青少年肥胖率：7.9%（1982年仅0.2%）
- 城市高于农村，但农村增长迅速
""",
    category=KnowledgeCategory.BASIC_KNOWLEDGE,
    life_dimension=LifeDimension.MEDICAL_INFO,
    behavior_types=["awareness"],
    applicable_stages=[BehaviorStage.PRECONTEMPLATION, BehaviorStage.CONTEMPLATION],
    indicator_ids=["HI-COB-BMI", "HI-COB-WAIST", "HI-COB-WHtR"],
    evidence_sources=[
        EvidenceSource(
            source_type="guideline",
            title="儿童青少年肥胖食养指南（2024年版）",
            publication="国家卫生健康委办公厅",
            year=2024,
            evidence_level=EvidenceLevel.LEVEL_1A
        ),
        EvidenceSource(
            source_type="guideline",
            title="学龄儿童青少年超重与肥胖筛查（WS/T 586）",
            publication="国家卫生健康标准",
            year=2018,
            evidence_level=EvidenceLevel.LEVEL_1A
        )
    ],
    tags=["儿童肥胖", "BMI", "中心型肥胖", "腰围", "判定标准", "流行病学"]
),
```

```python
KnowledgeItem(
    knowledge_id="KI-COB-002",
    title="儿童青少年肥胖的中医辨证分型",
    content="""
中医学将肥胖归属于"脂人""膏人""肥人"等范畴，记载最早见于《黄帝内经》。

一、病因病机

肥胖病因多与年龄、体质、饮食、情志、劳逸因素有关。中医认为肥胖属本虚标实证，辨证涉及痰、湿、热等病理因素，常兼夹痰湿、血瘀、气郁等标实之证，病位多在脾胃，与肾气虚关系密切，并可涉及五脏。

儿童青少年体弱、饮食不节、先天禀赋、缺乏运动、情志所伤，酿生痰湿，可致气机运行不畅、血行瘀滞、痰瘀内聚、留着不行。

二、常见辨证分型

1. 胃热火郁证
   临床表现：多食，消谷善饥，大便不爽甚或干结，尿黄，或有口干口苦，喜饮水
   舌脉：舌质红，苔黄，脉数
   食药物质：鲜芦根、淡竹叶、葛根、甘草

2. 痰湿内盛证
   临床表现：形体肥胖，身体沉重，肢体困倦，脘痞胸满，可伴头晕，口干而不欲饮，大便黏滞不爽，嗜食肥甘，喜卧懒动
   舌脉：舌淡胖或大，苔白腻或白滑，脉滑
   食药物质：橘皮、茯苓、薏苡仁、赤小豆、砂仁

3. 气郁血瘀证
   临床表现：肥胖懒动，喜太息，胸闷胁满，面晦唇暗，肢端色泽不鲜甚或青紫，可伴便干、失眠
   舌脉：舌质暗或有瘀斑瘀点，舌苔薄，脉弦或涩
   食药物质：佛手、山楂、桃仁、薤白

4. 脾虚不运证
   临床表现：肥胖臃肿，神疲乏力，身体困重，脘腹痞闷，或有四肢轻度浮肿（晨轻暮重），饮食如常或偏少，既往多有暴饮暴食史，小便不利，大便溏或便秘
   舌脉：舌淡胖，边有齿印，苔薄白或白腻，脉濡细
   食药物质：茯苓、山药、芡实、白扁豆、莲子、大枣

5. 脾肾阳虚证
   临床表现：形体肥胖，易于疲劳，四肢不温甚或四肢厥冷，喜食热饮，小便清长
   舌脉：舌淡胖，舌苔薄白，脉沉细
   食药物质：益智仁、刀豆、肉桂、黑胡椒、丁香、生姜

三、食养原则

辨证施食遵循首重脾胃的原则，兼顾合并症，因人因时因地施食。
""",
    category=KnowledgeCategory.BASIC_KNOWLEDGE,
    life_dimension=LifeDimension.NUTRITION,
    behavior_types=["awareness", "skill_learning"],
    applicable_stages=[BehaviorStage.CONTEMPLATION, BehaviorStage.PREPARATION],
    indicator_ids=["HI-COB-BMI"],
    evidence_sources=[
        EvidenceSource(
            source_type="guideline",
            title="儿童青少年肥胖食养指南（2024年版）",
            publication="国家卫生健康委办公厅",
            year=2024,
            evidence_level=EvidenceLevel.LEVEL_1A
        )
    ],
    tags=["中医辨证", "胃热火郁", "痰湿内盛", "气郁血瘀", "脾虚不运", "脾肾阳虚", "食药物质"]
),
```

### 2.2 营养管理知识

```python
KnowledgeItem(
    knowledge_id="KI-COB-003",
    title="肥胖儿童青少年膳食结构与能量管理",
    content="""
一、膳食结构基本要求

儿童青少年正处于生长发育的重要阶段，应保证平衡膳食，达到能量和营养素摄入量及比例适宜。

1. 食物多样化
   - 每天摄入12种以上食物
   - 每周摄入25种以上食物
   - 每天食物应包括：谷薯类、蔬菜水果、禽畜鱼蛋奶类、大豆坚果类

2. 选择小份量实现食物多样
   - 根据不同年龄能量需要量控制食物摄入总量
   - 增加新鲜蔬菜水果、全谷物和杂豆比重
   - 保证优质蛋白质食物摄入

3. 奶类摄入
   - 学龄前（2-5岁）：每天350-500mL或相当量
   - 学龄（6-17岁）：每天300mL以上或相当量

二、肥胖儿童的能量管理

1. 核心原则
   - 控制膳食总能量摄入，吃饭八分饱
   - 减重期间建议能量在正常体重需要量基础上减少约20%

2. 宏量营养素比例（以10岁肥胖儿童为例）
   - 碳水化合物：占总能量52%-62%
   - 脂肪：占总能量20%-30%
   - 蛋白质：占总能量15%-20%（约60-85g）

3. 优选策略
   - 提高鱼类、蔬菜、大豆及其制品的摄入量
   - 控制精白米面，增加全谷物和杂豆摄入
   - 减少高油、高盐、高糖及能量密度较高的食物

4. 增加饱腹感的策略
   - 适当增加微量营养素密度较高的食物
   - 膳食结构应有利于减轻饥饿感、增加饱腹感
   - 必要时补充复合营养素补充剂

三、不同年龄段每日能量需要量（中等活动水平）

| 年龄 | 男（kcal） | 女（kcal） |
|------|-----------|-----------|
| 2-3岁 | 1100-1250 | 1000-1150 |
| 4-5岁 | 1300-1400 | 1250-1300 |
| 6-10岁 | 1600-2050 | 1450-1900 |
| 11-13岁 | 2200-2600 | 2000-2200 |
| 14-17岁 | 2600-2950 | 2200-2350 |

四、10岁肥胖儿童食谱能量参考

不同地区食谱提供能量1550-1800kcal，即在正常需要量基础上适当减少。
""",
    category=KnowledgeCategory.PRACTICE_GUIDE,
    life_dimension=LifeDimension.NUTRITION,
    behavior_types=["tracking", "adjustment", "habit_building"],
    applicable_stages=[BehaviorStage.PREPARATION, BehaviorStage.ACTION, BehaviorStage.MAINTENANCE],
    indicator_ids=["HI-COB-BMI", "HI-COB-ENERGY"],
    evidence_sources=[
        EvidenceSource(
            source_type="guideline",
            title="儿童青少年肥胖食养指南（2024年版）",
            publication="国家卫生健康委办公厅",
            year=2024,
            evidence_level=EvidenceLevel.LEVEL_1A
        ),
        EvidenceSource(
            source_type="guideline",
            title="中国居民膳食指南（2022）",
            publication="中国营养学会",
            year=2022,
            evidence_level=EvidenceLevel.LEVEL_1A
        )
    ],
    tags=["膳食结构", "能量管理", "食物多样", "小份多样", "宏量营养素"]
),
```

```python
KnowledgeItem(
    knowledge_id="KI-COB-004",
    title="肥胖儿童青少年食物选择指南",
    content="""
食物选择遵循适量性、可及性、适宜性三原则，优先选择能量较低、微量营养素密度较高和血糖生成指数较低的食物。

一、各类食物选择（优选/限量/不宜）

1. 谷薯类
   优选：蒸煮烹饪、粗细搭配的杂米饭、杂粮面等
   限量：精白米面类、粉丝、年糕等
   不宜：油条、炸薯条、方便面、干脆面、面制辣条、奶油蛋糕等

2. 蔬菜类
   优选：叶菜类、瓜茄类、鲜豆类、花芽类、菌藻类
   限量：高淀粉含量蔬菜（如莲藕）
   不宜：炸藕夹、油焖茄子、油炸果蔬脆等

3. 水果类
   优选：柚子、蓝莓、草莓、苹果、樱桃等浆果类、核果类、瓜果类
   限量：冬枣、山楂、榴莲、香蕉、荔枝、甘蔗、龙眼、芒果等高糖水果
   不宜：高糖分水果罐头、果脯

4. 畜禽类
   优选：里脊、腱子肉等低脂部位；胸脯肉、去皮腿肉等少脂禽类
   限量：牛排、小排等脂肪含量相对高的部位；带皮禽类
   不宜：肥肉、五花肉、蹄膀、牛腩、肥鹅肝、大肠等

5. 水产类
   优选：绝大部分清蒸或水煮水产类
   限量：煎带鱼、糖醋鱼等较多油盐糖烹饪的水产
   不宜：油炸、腌制的水产类及蟹黄蟹膏等富含脂肪胆固醇部位

6. 豆类
   优选：豆腐、无糖豆浆等大豆和杂豆制品
   限量：添加少量糖和/或油的豆制品
   不宜：兰花豆、油炸豆腐、豆腐乳、豆制辣条

7. 蛋乳类
   优选：蒸煮蛋类、脱脂及低脂乳制品、无糖酸奶
   限量：少油煎蛋、含少量添加糖的乳制品
   不宜：含有大量添加糖的乳制品

8. 饮料类
   优选：白水、矿泉水、纯净水
   限量：不加糖的鲜榨果汁
   不宜：含糖及甜味饮料、加入植脂末或糖的奶茶、果汁饮料

9. 坚果类
   优选：无添加油盐糖的原味坚果
   限量：添加少量油盐糖调味的坚果
   不宜：添加大量油盐糖等调味的坚果

二、烹饪方式建议

优先选择蒸、煮、炖、拌等低油烹饪方式，减少煎、炸、烧烤等高油高温烹饪。
""",
    category=KnowledgeCategory.PRACTICE_GUIDE,
    life_dimension=LifeDimension.NUTRITION,
    behavior_types=["skill_learning", "adjustment"],
    applicable_stages=[BehaviorStage.PREPARATION, BehaviorStage.ACTION, BehaviorStage.MAINTENANCE],
    indicator_ids=["HI-COB-BMI", "HI-COB-ENERGY"],
    evidence_sources=[
        EvidenceSource(
            source_type="guideline",
            title="儿童青少年肥胖食养指南（2024年版）",
            publication="国家卫生健康委办公厅",
            year=2024,
            evidence_level=EvidenceLevel.LEVEL_1A
        ),
        EvidenceSource(
            source_type="consensus",
            title="中国儿童肥胖诊断评估与管理专家共识",
            publication="中华儿科杂志",
            year=2022,
            evidence_level=EvidenceLevel.LEVEL_2A
        )
    ],
    tags=["食物选择", "优选食物", "限量食物", "不宜食物", "烹饪方式", "低GI"]
),
```

```python
KnowledgeItem(
    knowledge_id="KI-COB-005",
    title="肥胖儿童青少年饮食行为管理",
    content="""
养成健康饮食行为是预防和控制儿童青少年肥胖的重要途径。

一、核心饮食行为规范

1. 进餐习惯
   - 不挑食偏食、不暴饮暴食
   - 细嚼慢咽
   - 进餐结束立即离开餐桌
   - 一日三餐定时定量

2. 用餐时长
   - 早餐约20分钟
   - 午餐或晚餐约30分钟
   - 晚上9点以后尽可能不进食

3. 三餐能量分配
   - 早餐：25%-30%（强调吃好早餐）
   - 午餐：35%-40%
   - 晚餐：30%-35%

4. 进餐顺序（推荐）
   先吃蔬菜 → 然后吃鱼禽肉蛋及豆类 → 最后吃谷薯类

二、零食管理

1. 首选零食
   - 奶及奶制品
   - 新鲜蔬菜水果
   - 原味坚果

2. 零食原则
   - 结合营养标签，少吃高油高盐高糖的过度加工食品
   - 零食提供的能量不超过每日总能量的10%

3. 饮品管理
   - 不喝含糖饮料
   - 足量饮用白水，少量多次

三、在外就餐管理

1. 尽量在家就餐
2. 外出就餐注意：
   - 食物多样、合理搭配
   - 保证适量的新鲜蔬菜、全谷物和杂豆
   - 控制动物性食物、油炸食品、甜食和饮料

四、中医视角

偏食、过食等不健康的饮食行为，易导致脾胃功能受损，运化失常，痰湿停聚，增加肥胖风险。
""",
    category=KnowledgeCategory.INTERVENTION_STRATEGY,
    life_dimension=LifeDimension.NUTRITION,
    behavior_types=["habit_building", "adjustment", "skill_learning"],
    applicable_stages=[BehaviorStage.PREPARATION, BehaviorStage.ACTION, BehaviorStage.MAINTENANCE],
    indicator_ids=["HI-COB-BMI", "HI-COB-ENERGY"],
    evidence_sources=[
        EvidenceSource(
            source_type="guideline",
            title="儿童青少年肥胖食养指南（2024年版）",
            publication="国家卫生健康委办公厅",
            year=2024,
            evidence_level=EvidenceLevel.LEVEL_1A
        )
    ],
    tags=["饮食行为", "进餐顺序", "零食管理", "三餐分配", "含糖饮料"]
),
```

```python
KnowledgeItem(
    knowledge_id="KI-COB-006",
    title="因时因地的食养策略——四季与地域饮食调养",
    content="""
肥胖儿童青少年食养遵循中医整体观、辨证观，因人因时因地施食。

一、四季食养原则

遵循"春夏养阳、秋冬养阴"的调养原则：

1. 春季
   - 阳气开始生发，应当早起，足量运动
   - 饮食宜清淡升发

2. 夏季
   - 人体阳气外发，不可贪凉饮冷
   - 避免损伤阳气
   - 注意清热解暑与护阳并重

3. 秋季
   - 易燥，少食辛辣
   - 适量多吃酸甘多汁的食物：莲藕、苹果、梨、枇杷等
   - 润燥养阴

4. 冬季
   - 天气寒冷，常进食牛羊肉类较多
   - 食用后体内容易积热，常吃导致肺火旺盛
   - 添加"甘寒"食物调剂平衡：白萝卜、大白菜、百合、梨、苹果等

二、地域食养特点

1. 东北地区
   特点：以米面、畜禽肉及奶类为主，炖菜为主，肥厚实在，味重色浓
   肥胖率：较高流行水平
   建议：控制油盐糖摄入
   食谱能量参考：1580-1800kcal（碳水52-57%，脂肪25-30%，蛋白17-20%）

2. 西北地区
   特点：喜食面食，肉类以牛羊为主，瓜果丰富，绿叶蔬菜较少
   肥胖率：中低流行水平
   建议：保证蔬果和全谷物摄入，少用烧烤，保障充足饮水量
   食谱能量参考：1600-1800kcal（碳水53-58%，脂肪24-29%，蛋白15-20%）

3. 中部地区
   特点：水系发达盛产淡水鱼虾，蒸煨为主，汤品繁多，普遍嗜辣
   肥胖率：中流行水平
   建议：控制油盐摄入
   食谱能量参考：1550-1820kcal（碳水57-62%，脂肪20-26%，蛋白15-20%）

4. 西南地区
   特点：大米糯米为主食，口味重，喜辣麻酸
   肥胖率：低流行水平但逐年增加
   建议：强调预防，减少高油高盐
   食谱能量参考：1700-1800kcal（碳水57-60%，脂肪23-25%，蛋白17-18%）

5. 东南地区
   特点：大米为主食，水产品丰富，口味清鲜嫩爽，有喝早茶吃宵夜习惯
   肥胖率：相对较低
   建议：少吃宵夜和甜点
   食谱能量参考：1700-1800kcal（碳水54-60%，脂肪25-29%，蛋白15-18%）

三、西北高原地区特殊考虑

多见寒冷干燥气候，饮食上宜多选择温阳散寒的牛羊肉等食物。东南沿海地区温暖潮湿，饮食上则宜清淡，可多食蔬菜、水果、鱼虾、豆制品。
""",
    category=KnowledgeCategory.PRACTICE_GUIDE,
    life_dimension=LifeDimension.NUTRITION,
    behavior_types=["skill_learning", "adjustment"],
    applicable_stages=[BehaviorStage.PREPARATION, BehaviorStage.ACTION, BehaviorStage.MAINTENANCE],
    indicator_ids=["HI-COB-BMI", "HI-COB-ENERGY"],
    evidence_sources=[
        EvidenceSource(
            source_type="guideline",
            title="儿童青少年肥胖食养指南（2024年版）",
            publication="国家卫生健康委办公厅",
            year=2024,
            evidence_level=EvidenceLevel.LEVEL_1A
        )
    ],
    tags=["四季食养", "地域饮食", "春夏养阳", "秋冬养阴", "因地制宜"]
),
```

```python
KnowledgeItem(
    knowledge_id="KI-COB-007",
    title="肥胖儿童青少年中医辨证食养方",
    content="""
以下食养方以10岁儿童为例，供参考。食药物质在限定使用范围和用量内使用，食用方法请咨询专业人员。

一、不同证型食养方

1. 胃热火郁证——芦根竹叶饮
   材料：鲜芦根30g，淡竹叶5g，荸荠6个
   制法：将鲜芦根、淡竹叶洗净，荸荠去皮洗净打碎入锅，加清水煮约20分钟
   用法：代茶饮，每周3-4次

2. 痰湿内盛证——赤小豆薏苡仁粥
   材料：赤小豆15g，薏苡仁20g，橘皮5g，粳米50g
   制法：赤小豆、薏苡仁洗净浸泡2小时，橘皮稍加浸泡。与粳米一起放入锅内加清水，大火滚沸后中小火煮约30分钟
   用法：可代替部分主食，每周2-3次

3. 气郁血瘀证——百合佛手粥
   材料：佛手10g，百合10g，大枣2枚，粳米50g
   制法：佛手洗净切片放入锅中加清水，大火煮开10分钟去渣取汁，放入粳米、大枣、百合加清水，大火煮开5分钟转中小火煮30分钟成粥
   用法：可代替部分主食，每周2-3次

4. 脾虚不运证——山药莲子饼
   材料：鲜山药50g，莲子15g，枸杞粉5g，面粉50g，牛奶50mL，鸡蛋1个
   制法：山药莲子蒸20分钟晾凉，筛入面粉和枸杞粉，加牛奶鸡蛋酵母搅拌成糊状揉面团，擀成面片发酵后电饼铛烙熟
   用法：可代替部分主食，每周2-3次

5. 脾肾阳虚证——益智核桃猪肚汤
   材料：益智仁10g，核桃仁50g，生姜10g，猪肚100g
   制法：猪肚焯水切块，核桃仁对半分，所有食材放入煲内大火煮沸后中小火煮40分钟
   用法：佐餐食用，每周2-3次

二、其他常见症状食养方

1. 茯苓眉豆煲扇骨
   功效：健脾安神、利水渗湿
   适用：脾胃虚弱、身体困重或肢体轻度浮肿者
   用法：佐餐食用，每周2-3次

2. 山楂竹菊饮
   功效：清热、消积、除烦、疏肝明目
   适用：目赤肿胀、口舌生疮、肉食积滞者
   用法：代茶饮，每周2-3次

3. 三仁馒头（核桃仁、甜杏仁、桃仁）
   功效：止咳平喘、润肠通便、活血化瘀
   适用：大便干结、咳嗽喘息、气血不畅者
   用法：可代替部分主食，每周2-3次

4. 西瓜皮荷叶滚丝瓜
   功效：清热利湿、利尿消肿
   适用：中心型肥胖、浮肿、大便不畅者
   用法：佐餐食用，每周1-2次

5. 薏苡仁茯苓鲫鱼汤
   功效：健脾祛湿、理气化痰
   适用：脾虚湿盛所致水肿、腹胀者
   用法：佐餐食用，每周1-2次
""",
    category=KnowledgeCategory.INTERVENTION_STRATEGY,
    life_dimension=LifeDimension.NUTRITION,
    behavior_types=["skill_learning", "habit_building"],
    applicable_stages=[BehaviorStage.PREPARATION, BehaviorStage.ACTION, BehaviorStage.MAINTENANCE],
    indicator_ids=["HI-COB-BMI"],
    evidence_sources=[
        EvidenceSource(
            source_type="guideline",
            title="儿童青少年肥胖食养指南（2024年版）",
            publication="国家卫生健康委办公厅",
            year=2024,
            evidence_level=EvidenceLevel.LEVEL_1A
        )
    ],
    tags=["食养方", "辨证施食", "中医食疗", "食药物质", "药膳"]
),
```

### 2.3 运动管理知识

```python
KnowledgeItem(
    knowledge_id="KI-COB-008",
    title="肥胖儿童青少年身体活动与运动处方",
    content="""
充足的身体活动不仅促进儿童青少年健康成长，也能预防和控制肥胖。

一、不同年龄段运动推荐

1. 学龄前儿童（2-5岁）
   - 每天身体活动总时长≥3小时
   - 包括至少2小时户外活动
   - 以游戏为主的活动方式

2. 学龄儿童青少年（6-17岁）
   - 每天至少60分钟中高强度有氧运动
   - 如快走、骑车、游泳、球类运动等
   - 每周至少3天高强度/抗阻运动
   - 如跳绳、跳远、攀爬器械、弹力带运动等

二、肥胖儿童的运动原则

1. 循序渐进
   - 在运动处方师等专业人员安全评估和指导下
   - 从每天20分钟中高强度身体活动开始
   - 逐渐增加到每天20-60分钟
   - 养成长期运动习惯

2. 运动方案
   - 每周至少3-4次
   - 每次20-60分钟中高强度运动
   - 每周至少3天强化肌肉力量和/或骨健康的抗阻运动
   - 鼓励多种运动方式结合

3. 传统健身方式
   - 健身长拳
   - 八段锦
   - 增加运动的趣味性和多样性

三、学校/机构运动建议

利用体育课、课间操、课后体育活动或户外活动时间：
- 集体游戏：圆圈接力、踩影子、穿梭跑等
- 其他多种形式的运动

四、家庭运动建议

- 家长创造积极运动的家庭氛围
- 与孩子共同运动
- 培养运动技能
- 鼓励每天校外身体活动时间达到60分钟

五、久坐行为控制

- 每次久坐行为限制在1小时以内
- 学龄前每天视屏时间≤1小时
- 学龄每天视屏时间≤2小时，越少越好
""",
    category=KnowledgeCategory.PRACTICE_GUIDE,
    life_dimension=LifeDimension.EXERCISE,
    behavior_types=["habit_building", "tracking", "skill_learning"],
    applicable_stages=[BehaviorStage.PREPARATION, BehaviorStage.ACTION, BehaviorStage.MAINTENANCE],
    indicator_ids=["HI-COB-PA", "HI-COB-BMI", "HI-COB-SCREEN"],
    evidence_sources=[
        EvidenceSource(
            source_type="guideline",
            title="儿童青少年肥胖食养指南（2024年版）",
            publication="国家卫生健康委办公厅",
            year=2024,
            evidence_level=EvidenceLevel.LEVEL_1A
        )
    ],
    tags=["身体活动", "运动处方", "有氧运动", "抗阻运动", "久坐", "视屏时间"]
),
```

### 2.4 睡眠管理知识

```python
KnowledgeItem(
    knowledge_id="KI-COB-009",
    title="肥胖儿童青少年睡眠与作息管理",
    content="""
以"天人相应"理论指导儿童青少年规律作息，保证充足睡眠。

一、各年龄段睡眠推荐

| 年龄 | 推荐睡眠时长 |
|------|-------------|
| 5岁以下 | 10-13小时/天 |
| 6-12岁 | 9-12小时/天 |
| 13-17岁 | 8-10小时/天 |

二、核心要求

1. 早睡早起，规律作息
2. 保证充足睡眠时间
3. 睡眠质量与体重管理密切相关

三、睡眠不足对体重的影响

- 影响生长激素分泌
- 增加饥饿感，降低饱腹感
- 增加高能量食物的渴望
- 降低身体活动水平和运动动力
- 影响情绪调节，增加情绪性进食风险

四、视屏时间管理

1. 学龄前：每天≤1小时
2. 学龄：每天≤2小时
3. 越少越好
4. 睡前减少电子设备使用

五、中医"天人相应"的作息指导

- 顺应自然规律安排作息
- 春夏宜晚睡早起
- 秋冬宜早睡早起
- 午间适当休息
""",
    category=KnowledgeCategory.PRACTICE_GUIDE,
    life_dimension=LifeDimension.SLEEP,
    behavior_types=["habit_building", "tracking"],
    applicable_stages=[BehaviorStage.PREPARATION, BehaviorStage.ACTION, BehaviorStage.MAINTENANCE],
    indicator_ids=["HI-COB-SLEEP", "HI-COB-SCREEN"],
    evidence_sources=[
        EvidenceSource(
            source_type="guideline",
            title="儿童青少年肥胖食养指南（2024年版）",
            publication="国家卫生健康委办公厅",
            year=2024,
            evidence_level=EvidenceLevel.LEVEL_1A
        )
    ],
    tags=["睡眠", "作息", "视屏时间", "天人相应", "生长发育"]
),
```

### 2.5 心理健康与社会支持

```python
KnowledgeItem(
    knowledge_id="KI-COB-010",
    title="肥胖儿童青少年心理健康与社会支持体系",
    content="""
一、心理健康关注

1. 情绪管理
   - 重视提升肥胖儿童青少年情绪和行为管理能力
   - 解决肥胖带来的焦虑、抑郁等心理问题
   - 指导正确认识体型

2. 不良饮食行为关注
   - 情绪性进食：因情绪而非饥饿进食
   - 限制性进食：过度限制导致的反弹
   - 需结合心理和情绪干预

3. 心理干预原则
   - 避免肥胖歧视
   - 建立正面的自我形象
   - 培养自我管理能力
   - 关注身心整体健康

二、家庭支持环境

1. 家长角色
   - 提高营养健康素养
   - 为孩子提供营养均衡的食物
   - 培养科学饮食习惯
   - 参与、言传身教
   - 与孩子共同运动

2. 家庭监测
   - 正常体重儿童：至少每月测量记录1次身高和晨起空腹体重
   - 观察变化趋势
   - 异常变化主动咨询专业人员

三、学校支持环境

1. 营养教育课程
   - 根据不同年龄段特点设置
   - 每学期不少于2课时
   - 开足、上好体育课

2. 教育方式
   - 以儿童青少年为中心的自主学习
   - 同伴教育
   - 中医药进校园

3. 学校监测
   - 每年监测身高、体重和腰围
   - 计算BMI和腰围身高比
   - 及时向家长反馈并采取干预

四、社区支持环境

1. 宣传教育
   - 讲座、入户示范、壁报等多种形式
   - 宣传肥胖防控知识

2. 设施支持
   - 配备充足、适宜的儿童青少年运动场所

3. 产业支持
   - 鼓励研制有助于体重管理的产品
   - 减少高油高盐高糖食品生产和营销

五、体重管理流程

1. 专业指导下管理
   - 在医生或营养指导人员指导下进行
   - 每周测量1次身高和晨起空腹体重
   - 制定体重管理目标

2. 综合评估
   - 评估膳食、运动、睡眠、心理状况
   - 制定膳食加运动的个体方案

3. 长期坚持
   - 形成能够长期坚持的健康行为习惯
   - 逐步达到健康体重

⚠️ 特别提醒
- 儿童青少年单纯性肥胖不建议药物和手术治疗
- 重度肥胖或伴有代谢性疾病者可在多学科协作下临床治疗
""",
    category=KnowledgeCategory.INTERVENTION_STRATEGY,
    life_dimension=LifeDimension.SOCIAL,
    behavior_types=["awareness", "skill_learning", "habit_building"],
    applicable_stages=[BehaviorStage.CONTEMPLATION, BehaviorStage.PREPARATION,
                     BehaviorStage.ACTION, BehaviorStage.MAINTENANCE],
    indicator_ids=["HI-COB-BMI", "HI-COB-WAIST"],
    evidence_sources=[
        EvidenceSource(
            source_type="guideline",
            title="儿童青少年肥胖食养指南（2024年版）",
            publication="国家卫生健康委办公厅",
            year=2024,
            evidence_level=EvidenceLevel.LEVEL_1A
        )
    ],
    tags=["心理健康", "社会支持", "家庭", "学校", "社区", "体重管理", "肥胖歧视"]
),
```

---

## 三、干预模板（Intervention Templates）

```python
# ============================================
# 干预模板定义
# ============================================

CHILD_OBESITY_INTERVENTION_TEMPLATES = [

    InterventionTemplate(
        template_id="IT-COB-001",
        name="肥胖儿童膳食结构优化方案",
        description="基于食养指南的膳食结构调整干预方案，适用于2-17岁肥胖儿童青少年",
        life_dimension=LifeDimension.NUTRITION,
        applicable_stages=[BehaviorStage.PREPARATION, BehaviorStage.ACTION],
        duration_weeks=12,
        actions=[
            ActionStep(
                step_id="ACT-COB-001",
                description="膳食能量评估：计算当前膳食能量摄入，确定减少20%的目标能量",
                frequency="初始评估1次",
                tips=["使用食物交换份法进行计算", "参照年龄性别对应的能量需要量表"]
            ),
            ActionStep(
                step_id="ACT-COB-002",
                description="食物多样化：保证每天12种以上食物，每周25种以上",
                frequency="每日",
                tips=["使用小份量策略", "采用粗细搭配、荤素搭配、色彩搭配"]
            ),
            ActionStep(
                step_id="ACT-COB-003",
                description="优化进餐顺序：先蔬菜→再鱼禽肉蛋豆类→最后谷薯类",
                frequency="每餐",
                tips=["先准备好蔬菜", "分盘摆放", "用视觉提示引导"]
            ),
            ActionStep(
                step_id="ACT-COB-004",
                description="全谷物替代：用杂粮饭、杂粮面逐步替代精白米面",
                frequency="每日",
                tips=["从混合1/4全谷物开始", "逐步增加至1/2", "尝试不同杂粮品种"]
            ),
            ActionStep(
                step_id="ACT-COB-005",
                description="饮品管理：以白水替代所有含糖饮料",
                frequency="每日",
                tips=["准备方便取用的水杯", "少量多次饮水", "可用淡茶、柠檬水作为过渡"]
            ),
            ActionStep(
                step_id="ACT-COB-006",
                description="零食升级：用奶制品、水果、原味坚果替代加工零食",
                frequency="每日",
                tips=["提前准备健康零食", "零食能量不超过每日总能量的10%"]
            ),
        ],
        success_metrics=[
            {"metric": "BMI变化趋势", "target": "12周内BMI下降或维持稳定（生长发育期）"},
            {"metric": "膳食多样性评分", "target": "每日≥12种食物"},
            {"metric": "含糖饮料频次", "target": "减至0次/周"},
            {"metric": "全谷物占比", "target": "主食中≥1/3为全谷物"}
        ],
        knowledge_item_ids=["KI-COB-003", "KI-COB-004", "KI-COB-005"]
    ),

    InterventionTemplate(
        template_id="IT-COB-002",
        name="肥胖儿童中医辨证食养方案",
        description="基于中医辨证分型的个性化食养干预，需在专业人员指导下实施",
        life_dimension=LifeDimension.NUTRITION,
        applicable_stages=[BehaviorStage.ACTION, BehaviorStage.MAINTENANCE],
        duration_weeks=8,
        actions=[
            ActionStep(
                step_id="ACT-COB-007",
                description="中医体质辨证评估，确定肥胖证型",
                frequency="初始评估+每4周复评",
                tips=["记录舌象、脉象", "关注主症变化", "需中医师参与"]
            ),
            ActionStep(
                step_id="ACT-COB-008",
                description="根据证型选择食养方，融入日常膳食",
                frequency="每周2-4次",
                tips=[
                    "胃热火郁→芦根竹叶饮（每周3-4次代茶饮）",
                    "痰湿内盛→赤小豆薏苡仁粥（每周2-3次代替主食）",
                    "气郁血瘀→百合佛手粥（每周2-3次代替主食）",
                    "脾虚不运→山药莲子饼（每周2-3次代替主食）",
                    "脾肾阳虚→益智核桃猪肚汤（每周2-3次佐餐）"
                ]
            ),
            ActionStep(
                step_id="ACT-COB-009",
                description="四季食养调整：春升夏清秋润冬补",
                frequency="每季度调整1次",
                tips=["春季重升发", "夏季勿贪凉", "秋季重润燥", "冬季平衡温补"]
            ),
        ],
        success_metrics=[
            {"metric": "证型主症改善", "target": "4-8周内主症缓解"},
            {"metric": "体重趋势", "target": "配合膳食管理体重稳步下降"},
            {"metric": "消化功能", "target": "大便通畅，食欲正常"}
        ],
        knowledge_item_ids=["KI-COB-002", "KI-COB-006", "KI-COB-007"]
    ),

    InterventionTemplate(
        template_id="IT-COB-003",
        name="肥胖儿童运动行为建立方案",
        description="循序渐进建立长期运动习惯的干预方案",
        life_dimension=LifeDimension.EXERCISE,
        applicable_stages=[BehaviorStage.PREPARATION, BehaviorStage.ACTION],
        duration_weeks=12,
        actions=[
            ActionStep(
                step_id="ACT-COB-010",
                description="运动能力安全评估，制定个体化运动方案",
                frequency="初始评估+每4周调整",
                tips=["需运动处方师评估", "考虑关节负荷", "评估心肺功能"]
            ),
            ActionStep(
                step_id="ACT-COB-011",
                description="第1-4周：每天20分钟中等强度有氧运动",
                frequency="每日",
                tips=["快走、骑车、游泳等", "可分段进行", "以能说话但不能唱歌为强度标准"]
            ),
            ActionStep(
                step_id="ACT-COB-012",
                description="第5-8周：增加至每天30-45分钟，加入抗阻运动",
                frequency="有氧每日+抗阻每周3天",
                tips=["跳绳、弹力带、攀爬", "每次15-20分钟抗阻", "鼓励家长共同运动"]
            ),
            ActionStep(
                step_id="ACT-COB-013",
                description="第9-12周：达到每天45-60分钟，多样化运动",
                frequency="每日",
                tips=["球类运动增加趣味性", "八段锦等传统健身", "同伴运动"]
            ),
            ActionStep(
                step_id="ACT-COB-014",
                description="久坐行为控制：每次久坐≤1小时，控制视屏时间",
                frequency="每日",
                tips=["设定久坐提醒", "站立或走动休息5分钟", "用运动替代部分视屏时间"]
            ),
        ],
        success_metrics=[
            {"metric": "每日运动时长", "target": "≥60分钟中高强度"},
            {"metric": "每周运动频次", "target": "≥5天"},
            {"metric": "久坐时间", "target": "单次≤1小时"},
            {"metric": "视屏时间", "target": "学龄≤2小时/天"}
        ],
        knowledge_item_ids=["KI-COB-008"]
    ),

    InterventionTemplate(
        template_id="IT-COB-004",
        name="肥胖儿童家庭-学校-社区综合支持方案",
        description="构建多方协作的支持环境，促进长期体重管理",
        life_dimension=LifeDimension.SOCIAL,
        applicable_stages=[BehaviorStage.ACTION, BehaviorStage.MAINTENANCE],
        duration_weeks=24,
        actions=[
            ActionStep(
                step_id="ACT-COB-015",
                description="家长营养健康素养培训",
                frequency="每月1次培训+日常实践",
                tips=["学习营养标签阅读", "掌握食物交换份法", "学习低油低盐烹饪"]
            ),
            ActionStep(
                step_id="ACT-COB-016",
                description="家庭膳食环境改造：减少不健康食物可及性",
                frequency="持续执行",
                tips=["家中不存放含糖饮料和高油零食", "健康食物放在显眼位置", "全家统一健康饮食"]
            ),
            ActionStep(
                step_id="ACT-COB-017",
                description="学校监测与反馈：每学期身高体重腰围监测",
                frequency="每学期至少1次",
                tips=["计算BMI和腰围身高比", "及时向家长反馈", "配合学校体育课"]
            ),
            ActionStep(
                step_id="ACT-COB-018",
                description="心理支持：关注肥胖儿童情绪状态和自我认知",
                frequency="每月评估+持续关注",
                tips=["避免肥胖歧视", "建立正面体型认知", "识别情绪性进食", "必要时转介心理专业人员"]
            ),
        ],
        success_metrics=[
            {"metric": "家长健康素养评分", "target": "培训后显著提升"},
            {"metric": "家庭饮食环境评分", "target": "不健康食物可及性降低"},
            {"metric": "儿童心理健康评分", "target": "焦虑抑郁评分改善"}
        ],
        knowledge_item_ids=["KI-COB-010"]
    ),
]
```

---

## 四、行为映射（Behavior Mappings）

```python
# ============================================
# 行为映射定义
# ============================================

CHILD_OBESITY_BEHAVIOR_MAPPINGS = [

    BehaviorMapping(
        mapping_id="BM-COB-001",
        behavior_id="BHV-COB-DIET-STRUCTURE",
        behavior_name="儿童膳食结构优化行为",
        description="从高能量密度、低营养密度的膳食模式转向平衡膳食",
        knowledge_item_ids=["KI-COB-003", "KI-COB-004", "KI-COB-005"],
        intervention_template_ids=["IT-COB-001"],
        life_dimension=LifeDimension.NUTRITION,
        applicable_user_stages=[BehaviorStage.PREPARATION, BehaviorStage.ACTION, BehaviorStage.MAINTENANCE],
        trigger_tags=["膳食不均衡", "高能量饮食", "精白米面过量", "蔬果不足"]
    ),

    BehaviorMapping(
        mapping_id="BM-COB-002",
        behavior_id="BHV-COB-EATING-BEHAVIOR",
        behavior_name="儿童健康饮食行为养成",
        description="建立定时定量、细嚼慢咽、合理进餐顺序等健康饮食行为",
        knowledge_item_ids=["KI-COB-005"],
        intervention_template_ids=["IT-COB-001"],
        life_dimension=LifeDimension.NUTRITION,
        applicable_user_stages=[BehaviorStage.PREPARATION, BehaviorStage.ACTION],
        trigger_tags=["暴饮暴食", "进食过快", "不吃早餐", "零食过量", "含糖饮料"]
    ),

    BehaviorMapping(
        mapping_id="BM-COB-003",
        behavior_id="BHV-COB-TCM-DIET",
        behavior_name="儿童中医辨证食养行为",
        description="根据中医证型选择适宜的食药物质和食养方",
        knowledge_item_ids=["KI-COB-002", "KI-COB-006", "KI-COB-007"],
        intervention_template_ids=["IT-COB-002"],
        life_dimension=LifeDimension.NUTRITION,
        applicable_user_stages=[BehaviorStage.ACTION, BehaviorStage.MAINTENANCE],
        trigger_tags=["痰湿体质", "脾虚", "胃热", "气郁", "阳虚"]
    ),

    BehaviorMapping(
        mapping_id="BM-COB-004",
        behavior_id="BHV-COB-PHYSICAL-ACTIVITY",
        behavior_name="儿童体力活动习惯建立",
        description="从久坐少动到养成每日60分钟中高强度运动习惯",
        knowledge_item_ids=["KI-COB-008"],
        intervention_template_ids=["IT-COB-003"],
        life_dimension=LifeDimension.EXERCISE,
        applicable_user_stages=[BehaviorStage.PREPARATION, BehaviorStage.ACTION, BehaviorStage.MAINTENANCE],
        trigger_tags=["久坐", "运动不足", "视屏时间过长", "体力下降"]
    ),

    BehaviorMapping(
        mapping_id="BM-COB-005",
        behavior_id="BHV-COB-SLEEP-ROUTINE",
        behavior_name="儿童规律作息与睡眠习惯",
        description="建立早睡早起、充足睡眠、限制视屏的作息习惯",
        knowledge_item_ids=["KI-COB-009"],
        intervention_template_ids=[],
        life_dimension=LifeDimension.SLEEP,
        applicable_user_stages=[BehaviorStage.PREPARATION, BehaviorStage.ACTION],
        trigger_tags=["睡眠不足", "作息不规律", "视屏时间过长", "晚睡"]
    ),

    BehaviorMapping(
        mapping_id="BM-COB-006",
        behavior_id="BHV-COB-FAMILY-SUPPORT",
        behavior_name="家庭肥胖防控支持行为",
        description="家长提升健康素养，营造健康家庭饮食和运动环境",
        knowledge_item_ids=["KI-COB-010"],
        intervention_template_ids=["IT-COB-004"],
        life_dimension=LifeDimension.SOCIAL,
        applicable_user_stages=[BehaviorStage.CONTEMPLATION, BehaviorStage.PREPARATION,
                               BehaviorStage.ACTION, BehaviorStage.MAINTENANCE],
        trigger_tags=["家庭饮食不健康", "家长素养不足", "缺乏运动氛围", "心理问题"]
    ),
]
```

---

## 五、知识库统计与分布

| 维度 | 知识条目数 | 干预模板数 | 行为映射数 | 健康指标数 |
|------|-----------|-----------|-----------|-----------|
| 疾病认知/评估 | 2（KI-COB-001, 002） | — | — | 3（BMI, 腰围, 腰围身高比） |
| 营养管理 | 5（KI-COB-003~007） | 2（IT-COB-001, 002） | 3（BM-COB-001~003） | 1（膳食能量） |
| 运动管理 | 1（KI-COB-008） | 1（IT-COB-003） | 1（BM-COB-004） | 2（活动时长, 视屏时间） |
| 睡眠管理 | 1（KI-COB-009） | — | 1（BM-COB-005） | 1（睡眠时长） |
| 心理与社会支持 | 1（KI-COB-010） | 1（IT-COB-004） | 1（BM-COB-006） | — |
| **合计** | **10** | **4** | **6** | **7** |

---

## 六、与其他KMS模块的衔接

| 关联模块 | 本模块提供 | 本模块接收 |
|---------|-----------|-----------|
| 体重管理知识（KI-WM系列） | 儿童青少年特殊判定标准、食养方 | 通用行为改变策略、体重维持知识 |
| 营养知识（KI-NUT系列） | 儿童特有的食物选择和能量标准 | 通用营养原则（血糖管理、情绪性进食等） |
| 中医体质知识 | 儿童肥胖辨证分型与食药物质 | 九种体质基础理论 |
| BAPS评估引擎 | 儿童肥胖评估标准（BMI界值表） | 用户评估结果 |
| 行为处方引擎 | 食养方、运动处方、作息方案 | 处方执行反馈 |
| 教练端 | 家长指导要点、学校监测流程 | 教练观察记录 |

---

## 七、扩展方向

1. **食物交换份工具**：将附录2的6类食物交换表转化为交互式食物替换推荐引擎
2. **地区食谱库**：将5个地区的食谱示例结构化为可按季节、证型检索的食谱数据库
3. **BMI判定计算器**：整合附录5的年龄性别BMI界值表，自动判定超重/肥胖状态
4. **腰围评估工具**：整合P75/P90腰围值表，自动评估中心型肥胖
5. **生长曲线追踪**：建立身高体重历史记录和可视化生长曲线
6. **家长端行为打卡**：膳食记录、运动记录、睡眠记录的家长辅助打卡系统
