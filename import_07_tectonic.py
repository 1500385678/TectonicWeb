#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07-Tectonic 文件扫描入库
运行: python import_07_tectonic.py [--dry-run] [--root <path>]

设计原则:
- 不动 07-Tectonic 下的源文件
- 只在 SQLite 建索引(rel_path + abs_path)
- 三套分类维度各管各的(dim_part / dim_skill / dim_atlas)
- 同一节点的不同格式(同名 + 扩展名不同)归到同一 method(group_key)
- 同一文件可能命中多个维度(预留 xref 表)

典型输出:
  method: dim_part='001_Walls', name='D07+Interseccion+con+angulo+igual+a+90'
  files:  [.skp, .png, .pdf]  → file_count=3, group_key='D07+Interseccion+con+angulo+igual+a+90'
"""

import os
import re
import sys
import json
import io
import sqlite3
import argparse
import hashlib
from pathlib import Path
from collections import defaultdict

# 强制 UTF-8 stdout(Windows GBK 兼容)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR     = Path(__file__).parent
DB_PATH      = BASE_DIR / 'construction.db'
SCHEMA_V2    = BASE_DIR / 'init_schema_v2.sql'
DEFAULT_ROOT = BASE_DIR.parent.parent / 'defense' / '07-Tectonic'

# 维度 1: 10 大部件(目录名前缀是 NN_)
PART_PREFIXES = {
    '001_Walls', '101_Door', '201_Windows', '301_Columns', '401_Roofs',
    '501_Ceiling', '601_Floors', '701_Curtain', '801_Railing', '901_Stairs',
}

# 维度 2: 技能库
SKILL_CODES = {'archi-tectonic', 'archi-door-window', 'archi-roof'}

# 维度 3: 构造图集
ATLAS_DIRS = {
    '变形缝节点', '基础节点', '墙体节点',
    '屋面节点', '幕墙节点', '楼地面节点', '门窗节点',
}

# 文件扩展名 → source_type 映射
EXT_TYPE = {
    '.dwg': 'dwg', '.dxf': 'dwg',
    '.skp': 'skp',
    '.rvt': 'rvt',
    '.pdf': 'pdf',
    '.png': 'png', '.jpg': 'png', '.jpeg': 'png', '.webp': 'png',
    '.svg': 'svg',
    '.md':  'md',
    '.docx': 'doc', '.doc': 'doc',
}

# role 推断(基于扩展名 + 文件名关键字)
def guess_role(filename: str, ext_type: str) -> str:
    fn = filename.lower()
    if ext_type == 'skp' or ext_type == 'rvt':
        return '三维模型'
    if ext_type == 'pdf':
        if '节点' in fn or 'detail' in fn or 'detail' in fn.lower():
            return '节点详图'
        if '案例' in fn or 'case' in fn.lower():
            return '案例'
        if '规范' in fn or 'code' in fn.lower():
            return '规范'
        return '说明文档'
    if ext_type == 'png':
        return '示意图'
    if ext_type == 'dwg':
        return '节点详图'
    if ext_type == 'svg':
        return '示意图'
    if ext_type == 'md':
        return '说明文档'
    return 'other'

# 从文件名提取 group_key(去掉扩展名,统一 + 和 空格 为 _,去 .N 后缀)
# 规则:
#   - + → _
#   - 空格 → _  (关键!否则 'D07 Interseccion' 和 'D07_Interseccion' 会被分两组)
#   - 尾部 .数字 去掉
#   - atlas_code 后的描述只取前 5 段(让 D07+...+a+90 跟 D07 ... esquina muro 归同组)
def extract_group_key(filename: str) -> str:
    stem = Path(filename).stem
    stem = stem.replace('+', '_').replace(' ', '_')
    stem = re.sub(r'\.\d+$', '', stem)
    # 截到 atlas_code + 后续 5 段
    parts = stem.split('_')
    for i, p in enumerate(parts):
        if re.match(r'^[A-Z]\d+$', p):
            keep = parts[:i+1+5]
            return '_'.join(keep)
    return stem.strip()

# 从 group_key 提取 atlas_code(开头的字母+数字,如 D07 / D08)
def extract_atlas_code(group_key: str) -> str:
    m = re.match(r'^([A-Z]\d+)', group_key, re.IGNORECASE)
    return m.group(1).upper() if m else None

def ensure_schema(conn: sqlite3.Connection):
    """应用 v2 增量 schema(幂等:列已存在则跳过)"""
    sql = SCHEMA_V2.read_text(encoding='utf-8')
    # SQLite 不支持 ADD COLUMN IF NOT EXISTS,手工处理
    # 把 ALTER TABLE ... ADD COLUMN 拆出来单独 try
    lines = sql.split('\n')
    safe_sql = []
    for line in lines:
        if 'ALTER TABLE' in line and 'ADD COLUMN' in line:
            # 提取列名
            m = re.search(r'ADD COLUMN\s+(\w+)', line, re.IGNORECASE)
            if m:
                col_name = m.group(1)
                # 检查列是否已存在
                rows = conn.execute(f"PRAGMA table_info(construction_methods)").fetchall()
                existing = [r[1] for r in rows]
                if col_name in existing:
                    continue  # 跳过
        safe_sql.append(line)
    conn.executescript('\n'.join(safe_sql))
    conn.commit()

def get_dim_id(conn, table: str, code: str) -> int | None:
    row = conn.execute(f'SELECT id FROM {table} WHERE code = ?', [code]).fetchone()
    return row['id'] if row else None

def upsert_method(conn, group_key: str, name: str, dim_part: str, dim_skill: str, dim_atlas: str) -> int:
    """
    按 group_key + 三维度 upsert 一条 method。
    已存在则更新 dim 字段,不存在则插入。
    """
    atlas_code = extract_atlas_code(group_key)
    part_id   = get_dim_id(conn, 'dim_part',  dim_part)  if dim_part  else None
    skill_id  = get_dim_id(conn, 'dim_skill', dim_skill) if dim_skill else None
    atlas_id  = get_dim_id(conn, 'dim_atlas', dim_atlas) if dim_atlas else None

    # category_id 后备:从 dim_part 或 dim_atlas 映射到 categories 表
    category_id = map_dim_to_category(conn, dim_part, dim_skill, dim_atlas)

    # 查重:优先用 (name, dim_part_id) 联合查
    row = conn.execute('''
        SELECT id FROM construction_methods
        WHERE name = ? AND (dim_part_id IS ? OR (dim_part_id IS NULL AND ? IS NULL))
    ''', [name, part_id, part_id]).fetchone()

    if row:
        return row['id']

    # 插入新 method
    cur = conn.execute('''
        INSERT INTO construction_methods
            (code, name, category_id, dim_part_id, dim_skill_id, dim_atlas_id, atlas_code, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
    ''', [group_key, name, category_id, part_id, skill_id, atlas_id, atlas_code])
    return cur.lastrowid


# 维度 → categories.code 映射(给 07-Tectonic 找最近的 category 后备)
DIM_TO_CATEGORY = {
    '001_Walls':   'wall',
    '101_Door':    'door_win',
    '201_Windows': 'door_win',
    '301_Columns': 'wall',
    '401_Roofs':   'roof',
    '501_Ceiling': 'floor',
    '601_Floors':  'floor',
    '701_Curtain': 'curtain',
    '801_Railing': 'floor',
    '901_Stairs':  'floor',
    # atlas 维度
    '变形缝节点':   'joint',
    '基础节点':     'foundation',
    '墙体节点':     'wall',
    '屋面节点':     'roof',
    '幕墙节点':     'curtain',
    '楼地面节点':   'floor',
    '门窗节点':     'door_win',
}

def map_dim_to_category(conn, dim_part, dim_skill, dim_atlas) -> int:
    """把维度映射到 categories 表的 id;映射不到返回第一个 category(墙)"""
    code = None
    if dim_part and dim_part in DIM_TO_CATEGORY:
        code = DIM_TO_CATEGORY[dim_part]
    elif dim_atlas and dim_atlas in DIM_TO_CATEGORY:
        code = DIM_TO_CATEGORY[dim_atlas]
    elif dim_skill:
        # archi-* 没有明确部位,默认 'wall' (可改为 NULL,但 category_id NOT NULL)
        code = 'wall'
    if code:
        row = conn.execute('SELECT id FROM categories WHERE code = ?', [code]).fetchone()
        if row:
            return row['id']
    # 实在没匹配,返回 categories 第一条(兜底)
    row = conn.execute('SELECT id FROM categories ORDER BY sort_order LIMIT 1').fetchone()
    return row['id'] if row else 1

def register_file(conn, method_id: int, filename: str, rel_path: str, abs_path: str, group_key: str):
    """登记一个文件"""
    ext = Path(filename).suffix.lower()
    ext_type = EXT_TYPE.get(ext, ext.lstrip('.'))
    role = guess_role(filename, ext_type)
    try:
        size_kb = os.path.getsize(abs_path) // 1024
    except OSError:
        size_kb = 0
    try:
        mtime = Path(abs_path).stat().st_mtime
        from datetime import datetime
        mtime_str = datetime.fromtimestamp(mtime).isoformat(sep=' ', timespec='seconds')
    except OSError:
        mtime_str = None

    # 查重:同 method + filename
    row = conn.execute('''
        SELECT id FROM tectonic_files WHERE method_id = ? AND filename = ?
    ''', [method_id, filename]).fetchone()
    if row:
        # 更新路径/大小
        conn.execute('''
            UPDATE tectonic_files
            SET rel_path=?, abs_path=?, size_kb=?, mtime=?, ext=?, source_type=?, role=?, group_key=?
            WHERE id=?
        ''', [rel_path, abs_path, size_kb, mtime_str, ext.lstrip('.'), ext_type, role, group_key, row['id']])
    else:
        conn.execute('''
            INSERT INTO tectonic_files
                (method_id, filename, rel_path, abs_path, ext, size_kb, mtime, source_type, role, group_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [method_id, filename, rel_path, abs_path, ext.lstrip('.'), size_kb, mtime_str, ext_type, role, group_key])

def update_file_count(conn, method_id: int):
    """更新冗余字段 file_count"""
    n = conn.execute('SELECT COUNT(*) AS n FROM tectonic_files WHERE method_id = ?', [method_id]).fetchone()['n']
    conn.execute('UPDATE construction_methods SET file_count = ? WHERE id = ?', [n, method_id])

def scan(root: Path, conn: sqlite3.Connection, dry_run: bool = False) -> dict:
    """
    递归扫描 07-Tectonic 目录,登记文件 + method
    返回统计信息
    """
    if not root.exists():
        print(f'[ERR] 目录不存在: {root}')
        return {'methods': 0, 'files': 0, 'errors': 1}

    stats = {'methods': 0, 'files': 0, 'by_part': defaultdict(int), 'by_skill': defaultdict(int), 'by_atlas': defaultdict(int)}

    # 遍历每个一级子目录,识别其维度
    for first_dir in sorted(root.iterdir()):
        if not first_dir.is_dir():
            continue
        first_name = first_dir.name

        # 识别维度
        dim_part = first_name if first_name in PART_PREFIXES else None
        dim_skill = first_name if first_name in SKILL_CODES else None
        dim_atlas = None

        # 构造图集 下还有二级目录(变形缝节点/基础节点/...)
        if first_name == '构造图集':
            # 进入二级
            for second_dir in sorted(first_dir.iterdir()):
                if not second_dir.is_dir() or second_dir.name in {'02_构造图集', '构造图集模板'}:
                    continue
                if second_dir.name in ATLAS_DIRS:
                    process_dir(second_dir, dim_part=None, dim_skill=None,
                                dim_atlas=second_dir.name, root=root, conn=conn,
                                dry_run=dry_run, stats=stats)
        elif first_name in PART_PREFIXES or first_name in SKILL_CODES:
            process_dir(first_dir, dim_part=dim_part, dim_skill=dim_skill,
                        dim_atlas=None, root=root, conn=conn, dry_run=dry_run, stats=stats)
        else:
            # 其他目录(如 幕墙与外立面库 / 扩初设计 / 施工图设计 / 构造图集模板)
            # 这些是其他组织维度,本期不强行入库
            pass

    return stats

def process_dir(d: Path, dim_part, dim_skill, dim_atlas, root: Path,
                conn: sqlite3.Connection, dry_run: bool, stats: dict):
    """递归处理一个目录,把里面的文件按 group_key 分组入库"""
    # 收集所有文件
    files = []
    for p in d.rglob('*'):
        if p.is_file():
            files.append(p)
    if not files:
        return

    # 按 group_key 分组
    groups = defaultdict(list)
    for p in files:
        group_key = extract_group_key(p.name)
        groups[group_key].append(p)

    for group_key, group_files in groups.items():
        # 跳过 Control.md / README.md / SKILL.md 等元数据
        if group_key.endswith('Control') or group_key == 'README' or group_key == 'SKILL':
            continue
        # method name: 优先用 atlas_code + 描述(从目录名推断)
        atlas_code = extract_atlas_code(group_key)
        if atlas_code:
            # 尝试从父目录/兄弟节点推断中文标题
            method_name = f'{atlas_code} · {group_key}'
        else:
            method_name = group_key

        if dry_run:
            # 仅打印
            for p in group_files:
                rel = p.relative_to(root)
                print(f'  [dry] {dim_part or dim_skill or dim_atlas or "?"} / {group_key} / {p.name}')
                stats['files'] += 1
            stats['methods'] += 1
        else:
            method_id = upsert_method(conn, group_key, method_name, dim_part, dim_skill, dim_atlas)
            for p in group_files:
                rel = p.relative_to(root).as_posix()
                register_file(conn, method_id, p.name, rel, str(p), group_key)
                stats['files'] += 1
            update_file_count(conn, method_id)
            stats['methods'] += 1
            if dim_part:  stats['by_part'][dim_part]  += 1
            if dim_skill: stats['by_skill'][dim_skill] += 1
            if dim_atlas: stats['by_atlas'][dim_atlas] += 1

def main():
    ap = argparse.ArgumentParser(description='07-Tectonic 文件扫描入库')
    ap.add_argument('--dry-run', action='store_true', help='只打印不入库')
    ap.add_argument('--root', type=str, default=str(DEFAULT_ROOT), help='07-Tectonic 根目录')
    args = ap.parse_args()

    root = Path(args.root)
    print(f'扫描根目录: {root}')
    print(f'数据库: {DB_PATH}')
    print(f'模式: {"DRY-RUN(只看不写)" if args.dry_run else "真实入库"}')
    print('---')

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    try:
        stats = scan(root, conn, dry_run=args.dry_run)
        if not args.dry_run:
            conn.commit()
        print('---')
        print(f'[OK] 完成: 方法 {stats["methods"]} 个,文件 {stats["files"]} 个')
        if stats.get('by_part'):
            print('按部件:', dict(stats['by_part']))
        if stats.get('by_skill'):
            print('按技能:', dict(stats['by_skill']))
        if stats.get('by_atlas'):
            print('按图集:', dict(stats['by_atlas']))
    finally:
        conn.close()

if __name__ == '__main__':
    main()
