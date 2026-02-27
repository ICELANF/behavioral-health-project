import re
path = 'core/agents/specialist_agents.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Fix 1: add missing keywords to CRITICAL_KW
old_critical = 'CRITICAL_KW = ["自杀", "自残", "不想活", "结束生命", "去死", "跳楼", "割腕", "遗书"]'
new_critical = 'CRITICAL_KW = ["自杀", "自残", "不想活", "结束生命", "去死", "跳楼", "割腕", "遗书", "安眠药", "安眠药过量"]'
c = c.replace(old_critical, new_critical)

# Fix 2: add hotline to CRITICAL response
c = c.replace(
    'recommendations=["立即升级至人工专业支持"],',
    'recommendations=["请立即拨打心理援助热线寻求专业帮助: 400-161-9995", "如有危险请拨打120急救电话"],',
)

# Fix 3: add hotline to WARNING response
c = c.replace(
    'recommendations=["提供共情支持", "评估是否需要升级"],',
    'recommendations=["我们很关心你，建议拨打危机热线获得专业支持: 400-161-9995", "提供共情支持", "评估是否需要升级"],',
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

# Verify
with open(path, 'r', encoding='utf-8') as f:
    v = f.read()
print('安眠药过量 in CRITICAL:', '安眠药过量' in v)
print('400-161-9995 in file:', '400-161-9995' in v)
print('专业支持 in WARNING:', '专业支持' in v)
