# -*- coding: utf-8 -*-
"""
health_standards.py — 医疗数据交换标准适配层

支持国际主流医疗数据交换标准:
  - FHIR R4 (Fast Healthcare Interoperability Resources)
  - HL7 v2 消息映射
  - ICD-10 疾病编码查询
  - SNOMED CT 临床术语映射
  - LOINC 检验项目编码

本模块作为平台健康数据与标准化接口之间的桥接层。
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# ICD-10 常用行为健康相关编码
# ══════════════════════════════════════════════════════════════

ICD_10_BEHAVIORAL_HEALTH = {
    "E11": "2型糖尿病",
    "E11.65": "2型糖尿病伴高血糖",
    "E66.0": "肥胖 (BMI>=30)",
    "E78.5": "高脂血症",
    "I10": "原发性高血压",
    "F32": "抑郁发作",
    "F41.1": "广泛性焦虑障碍",
    "G47.0": "失眠症",
    "Z71.3": "饮食咨询和监督",
    "Z72.0": "烟草使用",
    "Z72.1": "酒精使用",
    "Z73.0": "过度劳累",
}


# ══════════════════════════════════════════════════════════════
# LOINC 常用检验项目编码
# ══════════════════════════════════════════════════════════════

LOINC_CODES = {
    "4548-4":  {"name": "HbA1c", "unit": "%", "category": "糖化血红蛋白"},
    "2339-0":  {"name": "Glucose", "unit": "mg/dL", "category": "血糖"},
    "2085-9":  {"name": "HDL", "unit": "mg/dL", "category": "高密度脂蛋白"},
    "2089-1":  {"name": "LDL", "unit": "mg/dL", "category": "低密度脂蛋白"},
    "8480-6":  {"name": "Systolic BP", "unit": "mmHg", "category": "收缩压"},
    "8462-4":  {"name": "Diastolic BP", "unit": "mmHg", "category": "舒张压"},
    "29463-7": {"name": "Body Weight", "unit": "kg", "category": "体重"},
    "39156-5": {"name": "BMI", "unit": "kg/m2", "category": "体质指数"},
    "8867-4":  {"name": "Heart Rate", "unit": "bpm", "category": "心率"},
    "55284-4": {"name": "Blood Pressure", "unit": "mmHg", "category": "血压"},
}


# ══════════════════════════════════════════════════════════════
# SNOMED CT 临床术语 (行为健康子集)
# ══════════════════════════════════════════════════════════════

SNOMED_CT_TERMS = {
    "44054006": "Diabetes mellitus type 2",
    "73211009": "Diabetes mellitus",
    "38341003": "Hypertensive disorder",
    "414916001": "Obesity",
    "35489007": "Depressive disorder",
    "197480006": "Anxiety disorder",
    "193462001": "Insomnia",
    "228273003": "Alcohol misuse",
    "365980008": "Tobacco use finding",
}


def to_fhir_observation(
    patient_id: str,
    loinc_code: str,
    value: float,
    timestamp: str = None,
) -> Dict[str, Any]:
    """将平台健康数据转换为 FHIR R4 Observation 资源

    FHIR (Fast Healthcare Interoperability Resources) R4 标准格式
    """
    loinc_info = LOINC_CODES.get(loinc_code, {"name": "Unknown", "unit": "", "category": ""})
    return {
        "resourceType": "Observation",
        "status": "final",
        "category": [{
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs"}]
        }],
        "code": {
            "coding": [{"system": "http://loinc.org", "code": loinc_code,
                        "display": loinc_info["name"]}]
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": timestamp or datetime.now().isoformat(),
        "valueQuantity": {
            "value": value,
            "unit": loinc_info["unit"],
            "system": "http://unitsofmeasure.org",
        },
    }


def to_fhir_condition(
    patient_id: str,
    icd_code: str,
    snomed_code: str = None,
) -> Dict[str, Any]:
    """将诊断映射为 FHIR R4 Condition 资源"""
    icd_display = ICD_10_BEHAVIORAL_HEALTH.get(icd_code, "Unknown")
    coding = [{"system": "http://hl7.org/fhir/sid/icd-10", "code": icd_code,
               "display": icd_display}]
    if snomed_code and snomed_code in SNOMED_CT_TERMS:
        coding.append({"system": "http://snomed.info/sct", "code": snomed_code,
                        "display": SNOMED_CT_TERMS[snomed_code]})
    return {
        "resourceType": "Condition",
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "code": {"coding": coding},
        "subject": {"reference": f"Patient/{patient_id}"},
        "recordedDate": datetime.now().isoformat(),
    }


def parse_hl7_oru(hl7_message: str) -> Dict[str, Any]:
    """解析 HL7 v2 ORU (观察结果) 消息

    HL7 v2 是医院信息系统最常用的消息格式。
    """
    segments = hl7_message.strip().split("\r")
    result = {"message_type": "ORU", "observations": []}
    for seg in segments:
        fields = seg.split("|")
        if fields[0] == "OBX" and len(fields) > 5:
            result["observations"].append({
                "code": fields[3] if len(fields) > 3 else "",
                "value": fields[5] if len(fields) > 5 else "",
                "unit": fields[6] if len(fields) > 6 else "",
            })
    return result


def lookup_icd10(keyword: str) -> List[Dict[str, str]]:
    """ICD-10 编码查询"""
    results = []
    for code, desc in ICD_10_BEHAVIORAL_HEALTH.items():
        if keyword.lower() in desc.lower() or keyword.lower() in code.lower():
            results.append({"code": code, "description": desc})
    return results


def lookup_snomed(keyword: str) -> List[Dict[str, str]]:
    """SNOMED CT 术语查询"""
    results = []
    for code, term in SNOMED_CT_TERMS.items():
        if keyword.lower() in term.lower():
            results.append({"code": code, "term": term})
    return results
