#!/usr/bin/env python3
"""Cek apakah file langflow/*.json mengandung secret.
Jalankan sebelum commit export baru: python3 scripts/check_langflow_secrets.py
"""
import json
import re
import sys
from pathlib import Path

PATTERN = re.compile(
    r'\b(sk-[A-Za-z0-9_-]{16,}'
    r'|AIza[0-9A-Za-z_-]{20,}'
    r'|Bearer [A-Za-z0-9._-]{20,}'
    r'|ghp_[A-Za-z0-9]{20,}'
    r'|gho_[A-Za-z0-9]{20,}'
    r'|AKIA[0-9A-Z]{16})'
)

def walk(obj, path=''):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f'{path}.{k}')
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f'{path}[{i}]')
    elif isinstance(obj, str):
        if PATTERN.search(obj):
            yield path, obj[:120]

def main():
    root = Path('langflow')
    files = sorted(root.glob('*.json'))
    if not files:
        print('Tidak ada file di langflow/. OK.')
        return 0
    found_any = False
    for f in files:
        print(f'Cek {f}...')
        try:
            data = json.loads(f.read_text())
            hits = list(walk(data))
            if hits:
                found_any = True
                print(f'  WARNING: {len(hits)} secret value ditemukan:')
                for path, val in hits[:5]:
                    print(f'    {path}: {val}')
            else:
                print('  OK - bersih')
        except Exception as e:
            print(f'  ERROR: {e}')
            return 2
    if found_any:
        print('\nGAGAL: Ditemukan secret. JANGAN commit.')
        return 1
    print('\nLULUS: Semua file bersih. Aman untuk commit.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
