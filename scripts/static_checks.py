#!/usr/bin/env python3
"""CI 静态安全检查"""
import os, re, sys

errors = []

# Check 1: No f-string SQL (injection risk)
for root, _, files in os.walk('.'):
    if '.git' in root or 'node_modules' in root or '__pycache__' in root or 'venv' in root:
        continue
    for f in files:
        if not f.endswith('.py'):
            continue
        path = os.path.join(root, f)
        try:
            for i, line in enumerate(open(path, encoding='utf-8', errors='ignore'), 1):
                if re.search(r'\.execute\(f["\']', line):
                    errors.append(f'  {path}:{i}: f-string SQL (use parameterized queries)')
        except:
            pass

# Check 2: CORS wildcard
for f in ['api/main.py', 'main.py']:
    if os.path.exists(f):
        content = open(f, encoding='utf-8', errors='ignore').read()
        if 'allow_origins=["*"]' in content or "allow_origins=['*']" in content:
            errors.append(f'  {f}: CORS allow_origins=["*"] detected')

if errors:
    print(f'FAIL: {len(errors)} issues found:')
    for e in errors:
        print(e)
    sys.exit(1)

print('PASS: Static checks clean')
