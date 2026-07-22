#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建筑构造数据库 API 服务
运行: python api_server.py
访问: http://localhost:5189
"""

import os
import json
import sqlite3
from pathlib import Path

from flask import Flask, g, request, jsonify, send_from_directory

BASE_DIR   = Path(__file__).parent
DB_PATH    = BASE_DIR / 'construction.db'
STATIC_DIR = BASE_DIR.parent / 'TectonicWeb'

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path='/')
app.config['JSON_AS_ASCII'] = False

# ============================================================
# 数据库
# ============================================================
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(str(DB_PATH))
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def row_to_dict(row):
    if row is None: return None
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, str):
            try: d[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError): pass
    return d

def rows_to_list(rows):
    return [row_to_dict(r) for r in rows]

# ============================================================
# 路由
# ============================================================
@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')

# ── 分类 ──
@app.route('/api/categories')
def get_categories():
    db = get_db()
    rows = db.execute('SELECT * FROM categories ORDER BY sort_order').fetchall()
    return jsonify(rows_to_list(rows))

# ── 构造做法列表 ──
@app.route('/api/methods')
def get_methods():
    db = get_db()
    query = request.args
    sql = '''
        SELECT m.*, c.name AS category_name
        FROM construction_methods m
        LEFT JOIN categories c ON m.category_id = c.id
        WHERE m.status = 'active'
    '''
    params = []
    if query.get('category'):
        sql += ' AND c.code = ?'
        params.append(query['category'])
    if query.get('cost_tier'):
        sql += ' AND m.cost_tier = ?'
        params.append(query['cost_tier'])
    if query.get('keyword'):
        sql += ' AND (m.name LIKE ? OR m.short_desc LIKE ? OR m.applicable LIKE ?)'
        kw = f"%{query['keyword']}%"
        params.extend([kw, kw, kw])
    sql += ' ORDER BY c.sort_order, m.name'
    rows = db.execute(sql, params).fetchall()
    return jsonify(rows_to_list(rows))

# ── 单个做法详情（含层次） ──
@app.route('/api/methods/<int:method_id>')
def get_method(method_id):
    db = get_db()
    row = db.execute('''
        SELECT m.*, c.name AS category_name
        FROM construction_methods m
        LEFT JOIN categories c ON m.category_id = c.id
        WHERE m.id = ?
    ''', [method_id]).fetchone()
    if not row:
        return jsonify({'error': '构造做法不存在'}), 404
    d = row_to_dict(row)

    layers = db.execute('''
        SELECT * FROM layers WHERE method_id = ? ORDER BY seq
    ''', [method_id]).fetchall()
    d['layers'] = rows_to_list(layers)

    # 关联规范
    regs = db.execute('''
        SELECT r.code, r.name, r.category, r.key_clauses, mr.clause_ref, mr.clause_summary, r.is_mandatory
        FROM method_regulations mr
        JOIN regulations r ON mr.regulation_id = r.id
        WHERE mr.method_id = ?
    ''', [method_id]).fetchall()
    d['regulations'] = rows_to_list(regs)

    return jsonify(d)

# ── 易错点 ──
@app.route('/api/pitfalls')
def get_pitfalls():
    db = get_db()
    rows = db.execute('''
        SELECT p.*, c.name AS category_name, c.code AS category_code
        FROM pitfalls p
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.exam_relevance DESC, p.importance DESC
    ''').fetchall()
    return jsonify(rows_to_list(rows))

# ── 规范 ──
@app.route('/api/regulations')
def get_regulations():
    db = get_db()
    rows = db.execute('SELECT * FROM regulations ORDER BY issue_year DESC').fetchall()
    return jsonify(rows_to_list(rows))

# ── 考试知识点 ──
@app.route('/api/exam')
def get_exam():
    db = get_db()
    rows = db.execute('SELECT * FROM exam_knowledge ORDER BY chapter, section').fetchall()
    return jsonify(rows_to_list(rows))

@app.route('/api/exam/chapter/<chapter>')
def get_exam_by_chapter(chapter):
    db = get_db()
    rows = db.execute('SELECT * FROM exam_knowledge WHERE chapter = ? ORDER BY section', [chapter]).fetchall()
    return jsonify(rows_to_list(rows))

# ── 决策推荐（按场景查推荐做法） ──
@app.route('/api/recommend')
def recommend():
    db = get_db()
    query = request.args
    category = query.get('category')  # 'roof' / 'wall' / 'floor'
    building = query.get('building', '住宅')
    climate  = query.get('climate', '')
    traffic  = query.get('traffic', '')

    sql = '''
        SELECT m.*, c.name AS category_name, dr.reason
        FROM decision_rules dr
        JOIN construction_methods m ON dr.recommended_method_id = m.id
        LEFT JOIN categories c ON m.category_id = c.id
        WHERE 1=1
    '''
    params = []
    if category:
        sql += ' AND dr.category_id = (SELECT id FROM categories WHERE code = ?)'
        params.append(category)
    if building:
        sql += ' AND dr.building_type LIKE ?'
        params.append(f'%{building}%')
    if climate:
        sql += ' AND (dr.climate_zone LIKE ? OR dr.climate_zone IS NULL)'
        params.append(f'%{climate}%')
    if traffic:
        sql += ' AND (dr.is_trafficable LIKE ? OR dr.is_trafficable IS NULL)'
        params.append(f'%{traffic}%')
    sql += ' ORDER BY dr.priority DESC LIMIT 5'
    rows = db.execute(sql, params).fetchall()

    if not rows:
        # 回退：返回该 category 下的所有方法
        if category:
            rows = db.execute('''
                SELECT m.*, c.name AS category_name, NULL AS reason
                FROM construction_methods m
                LEFT JOIN categories c ON m.category_id = c.id
                WHERE c.code = ? AND m.status = 'active'
                ORDER BY m.cost_tier
                LIMIT 5
            ''', [category]).fetchall()
        else:
            rows = db.execute('''
                SELECT m.*, c.name AS category_name, NULL AS reason
                FROM construction_methods m
                LEFT JOIN categories c ON m.category_id = c.id
                WHERE m.status = 'active'
                ORDER BY m.cost_tier LIMIT 5
            ''').fetchall()

    return jsonify(rows_to_list(rows))

# ============================================================
# 媒体服务（图片展示 + CAD 文件下载）
# ============================================================
MEDIA_DIR  = BASE_DIR / 'media'
IMAGES_DIR = MEDIA_DIR / 'images'
CAD_DIR    = MEDIA_DIR / 'cad'
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(CAD_DIR, exist_ok=True)

@app.route('/api/media/images/<path:filename>')
def serve_image(filename):
    """提供构造示意图"""
    return send_from_directory(str(IMAGES_DIR), filename)

@app.route('/api/media/cad/<path:filename>')
def download_cad(filename):
    """下载 CAD 文件（DWG/SKP/PDF/DXF）"""
    return send_from_directory(
        str(CAD_DIR),
        filename,
        as_attachment=True,
        download_name=filename
    )

@app.route('/api/media/list/<int:method_id>')
def list_media(method_id):
    """列出某构造做法的所有媒体文件"""
    db = get_db()
    row = db.execute(
        'SELECT image_urls, cad_files FROM construction_methods WHERE id = ?',
        [method_id]
    ).fetchone()
    if not row:
        return jsonify({'error': '构造做法不存在'}), 404
    return jsonify({
        'images': row['image_urls'] if row['image_urls'] else [],
        'cad_files': row['cad_files'] if row['cad_files'] else []
    })

# ============================================================
# 07-Tectonic 三维度索引接口(v2)
# ============================================================

@app.route('/api/dim/<dim_type>')
def get_dim(dim_type):
    """
    维度列表:dim_type = 'part' | 'skill' | 'atlas'
    返回该维度下所有分类 + 每个分类下的 method 数
    """
    db = get_db()
    # dim_part 用 name_zh 列,dim_skill/dim_atlas 用 name 列,各写各的
    if dim_type == 'part':
        rows = db.execute('''
            SELECT d.id, d.code, d.name_zh AS name,
                   (SELECT COUNT(*) FROM construction_methods m WHERE m.dim_part_id = d.id AND m.file_count > 0) AS method_count
            FROM dim_part d
            ORDER BY d.sort_order, d.id
        ''').fetchall()
    elif dim_type == 'skill':
        rows = db.execute('''
            SELECT d.id, d.code, d.name AS name,
                   (SELECT COUNT(*) FROM construction_methods m WHERE m.dim_skill_id = d.id AND m.file_count > 0) AS method_count
            FROM dim_skill d
            ORDER BY d.sort_order, d.id
        ''').fetchall()
    elif dim_type == 'atlas':
        rows = db.execute('''
            SELECT d.id, d.code, d.name AS name,
                   (SELECT COUNT(*) FROM construction_methods m WHERE m.dim_atlas_id = d.id AND m.file_count > 0) AS method_count
            FROM dim_atlas d
            ORDER BY d.sort_order, d.id
        ''').fetchall()
    else:
        return jsonify({'error': f'未知维度: {dim_type}，仅支持 part/skill/atlas'}), 400
    return jsonify(rows_to_list(rows))


@app.route('/api/methods/by-dim/<dim_type>/<dim_code>')
def methods_by_dim(dim_type, dim_code):
    """按维度 + 维度 code 查 method 列表"""
    db = get_db()
    if dim_type == 'part':
        rows = db.execute('''
            SELECT m.id, m.name, m.atlas_code, m.file_count,
                   d.code AS dim_code, d.name_zh AS dim_name
            FROM construction_methods m
            JOIN dim_part d ON m.dim_part_id = d.id
            WHERE d.code = ? AND m.file_count > 0
            ORDER BY m.atlas_code, m.name
        ''', [dim_code]).fetchall()
    elif dim_type == 'skill':
        rows = db.execute('''
            SELECT m.id, m.name, m.atlas_code, m.file_count,
                   d.code AS dim_code, d.name AS dim_name
            FROM construction_methods m
            JOIN dim_skill d ON m.dim_skill_id = d.id
            WHERE d.code = ? AND m.file_count > 0
            ORDER BY m.atlas_code, m.name
        ''', [dim_code]).fetchall()
    elif dim_type == 'atlas':
        rows = db.execute('''
            SELECT m.id, m.name, m.atlas_code, m.file_count,
                   d.code AS dim_code, d.name AS dim_name
            FROM construction_methods m
            JOIN dim_atlas d ON m.dim_atlas_id = d.id
            WHERE d.code = ? AND m.file_count > 0
            ORDER BY m.atlas_code, m.name
        ''', [dim_code]).fetchall()
    else:
        return jsonify({'error': f'未知维度: {dim_type}，仅支持 part/skill/atlas'}), 400
    return jsonify(rows_to_list(rows))


@app.route('/api/method/<int:method_id>/files')
def method_files(method_id):
    """某 method 的所有原始文件(含预览链接)"""
    db = get_db()
    method = db.execute('SELECT id, name, atlas_code FROM construction_methods WHERE id = ?', [method_id]).fetchone()
    if not method:
        return jsonify({'error': '方法不存在'}), 404
    files = db.execute('''
        SELECT id, filename, rel_path, abs_path, ext, source_type, role, size_kb, group_key
        FROM tectonic_files WHERE method_id = ?
        ORDER BY source_type, filename
    ''', [method_id]).fetchall()
    return jsonify({
        'method': row_to_dict(method),
        'files': rows_to_list(files)
    })


@app.route('/api/files/by-ext/<ext>')
def files_by_ext(ext):
    """按扩展名查所有文件: ext=skp / dwg / rvt / pdf / png"""
    db = get_db()
    rows = db.execute('''
        SELECT t.id, t.filename, t.rel_path, t.ext, t.size_kb, t.role,
               m.id AS method_id, m.name AS method_name
        FROM tectonic_files t
        LEFT JOIN construction_methods m ON t.method_id = m.id
        WHERE t.ext = ?
        ORDER BY t.filename
    ''', [ext.lower()]).fetchall()
    return jsonify(rows_to_list(rows))


# ============================================================
# BIMcontent 风格的"构件库"主接口(2026-07-13 重构)
# 粒度:单文件 = 单卡片
# ============================================================

@app.route('/api/files')
def list_files():
    """
    文件列表(构件库主接口)
    Query: ext, dim, role, q, sort, limit, offset
    返回: { total, items: [{..., thumbnail_url, open_url}] }
    """
    db = get_db()
    q = request.args
    ext_filter = (q.get('ext') or '').lower().strip()
    dim_filter = (q.get('dim') or '').strip()        # 'part:001_Walls' | 'skill:archi-roof' | 'atlas:墙体节点'
    role_filter = (q.get('role') or '').strip()
    kw = (q.get('q') or '').strip()
    sort = (q.get('sort') or 'newest').lower()       # 'newest' | 'name' | 'size'
    limit = int(q.get('limit') or 100)
    offset = int(q.get('offset') or 0)

    where = ['1=1']
    params = []
    if ext_filter:
        exts = [e.strip() for e in ext_filter.split(',') if e.strip()]
        if exts:
            placeholders = ','.join('?' for _ in exts)
            where.append(f't.ext IN ({placeholders})')
            params.extend(exts)
    if dim_filter:
        # dim 可选前缀: part / skill / atlas
        if ':' in dim_filter:
            dim_type, dim_code = dim_filter.split(':', 1)
            col_map = {'part': 'dim_part_id', 'skill': 'dim_skill_id', 'atlas': 'dim_atlas_id'}
            fk = col_map.get(dim_type)
            if fk:
                where.append(f'm.{fk} = (SELECT id FROM dim_{dim_type} WHERE code = ?)')
                params.append(dim_code)
    if role_filter:
        where.append('t.role = ?')
        params.append(role_filter)
    if kw:
        where.append('(t.filename LIKE ? OR m.name LIKE ?)')
        kw_pat = f'%{kw}%'
        params.extend([kw_pat, kw_pat])

    where_sql = ' AND '.join(where)

    # 排序
    if sort == 'name':
        order_sql = 'ORDER BY t.filename'
    elif sort == 'size':
        order_sql = 'ORDER BY t.size_kb DESC'
    else:  # newest = 按 mtime 倒序
        order_sql = 'ORDER BY t.mtime DESC, t.id DESC'

    # 总数
    total = db.execute(f'''
        SELECT COUNT(*) AS n
        FROM tectonic_files t
        LEFT JOIN construction_methods m ON t.method_id = m.id
        WHERE {where_sql}
    ''', params).fetchone()['n']

    rows = db.execute(f'''
        SELECT t.id, t.filename, t.rel_path, t.ext, t.source_type, t.role,
               t.size_kb, t.mtime, t.group_key,
               m.id AS method_id, m.name AS method_name, m.atlas_code,
               p.code AS part_code,  p.name_zh AS part_name,
               s.code AS skill_code, s.name AS skill_name,
               a.code AS atlas_code_name, a.name AS atlas_name
        FROM tectonic_files t
        LEFT JOIN construction_methods m ON t.method_id = m.id
        LEFT JOIN dim_part  p ON m.dim_part_id  = p.id
        LEFT JOIN dim_skill s ON m.dim_skill_id = s.id
        LEFT JOIN dim_atlas a ON m.dim_atlas_id = a.id
        WHERE {where_sql}
        {order_sql}
        LIMIT ? OFFSET ?
    ''', params + [limit, offset]).fetchall()

    items = []
    for r in rows:
        d = dict(r)
        # 缩略图:直接给 /api/media/thumb/<id> 端点(后端自动选 PNG 或 SVG 占位)
        d['thumbnail_url'] = '/api/media/thumb/' + str(d['id'])
        d['open_url']      = '/api/file/open/' + str(d['id'])
        items.append(d)

    return jsonify({
        'total':  total,
        'limit':  limit,
        'offset': offset,
        'items':  items,
    })


@app.route('/api/files/filters')
def files_filters():
    """
    筛选项统计(给 UI 渲染左侧多维筛选 + 各选项的计数)
    返回: { ext_counts, role_counts, dims: {part, skill, atlas} }
    """
    db = get_db()

    # ext 统计
    ext_counts = {r['ext']: r['n'] for r in db.execute('''
        SELECT ext, COUNT(*) AS n FROM tectonic_files GROUP BY ext ORDER BY n DESC
    ''').fetchall()}

    # role 统计
    role_counts = {r['role']: r['n'] for r in db.execute('''
        SELECT role, COUNT(*) AS n FROM tectonic_files GROUP BY role ORDER BY n DESC
    ''').fetchall()}

    # 维度统计(每个 dim 下每个分类的方法数 + 该 dim 下的文件数)
    dims = {'part': [], 'skill': [], 'atlas': []}

    # part 维度(dim_part 用 name_zh)
    for r in db.execute('''
        SELECT d.code, d.name_zh AS name,
               (SELECT COUNT(DISTINCT t.id) FROM tectonic_files t
                JOIN construction_methods m2 ON t.method_id = m2.id
                WHERE m2.dim_part_id = d.id) AS file_count
        FROM dim_part d
        ORDER BY file_count DESC, d.id
    ''').fetchall():
        dims['part'].append({'code': r['code'], 'name': r['name'], 'count': r['file_count']})

    # skill 维度(dim_skill 用 name)
    for r in db.execute('''
        SELECT d.code, d.name AS name,
               (SELECT COUNT(DISTINCT t.id) FROM tectonic_files t
                JOIN construction_methods m2 ON t.method_id = m2.id
                WHERE m2.dim_skill_id = d.id) AS file_count
        FROM dim_skill d
        ORDER BY file_count DESC, d.id
    ''').fetchall():
        dims['skill'].append({'code': r['code'], 'name': r['name'], 'count': r['file_count']})

    # atlas 维度(dim_atlas 用 name)
    for r in db.execute('''
        SELECT d.code, d.name AS name,
               (SELECT COUNT(DISTINCT t.id) FROM tectonic_files t
                JOIN construction_methods m2 ON t.method_id = m2.id
                WHERE m2.dim_atlas_id = d.id) AS file_count
        FROM dim_atlas d
        ORDER BY file_count DESC, d.id
    ''').fetchall():
        dims['atlas'].append({'code': r['code'], 'name': r['name'], 'count': r['file_count']})

    return jsonify({
        'total_files': sum(ext_counts.values()),
        'ext_counts':  ext_counts,
        'role_counts': role_counts,
        'dims':        dims,
    })


@app.route('/api/media/thumb/<int:file_id>')
def serve_thumb(file_id):
    """
    提供缩略图(本期实现:
      - 如果该 file 自己就是 PNG → 直接返回
      - 否则查同 group_key 的 PNG → 返回
      - 没有 PNG → 返回 SVG 占位图标(按 ext)
    )
    """
    db = get_db()
    row = db.execute('SELECT filename, ext, group_key, abs_path FROM tectonic_files WHERE id = ?', [file_id]).fetchone()
    if not row:
        return jsonify({'error': 'file not found'}), 404

    # 自己就是 png → 返回
    if row['ext'] == 'png':
        return send_from_directory(str(Path(row['abs_path']).parent), row['filename'])

    # 同组 png
    png_row = db.execute('''
        SELECT filename, abs_path FROM tectonic_files
        WHERE group_key = ? AND ext = 'png' AND id != ?
        ORDER BY id LIMIT 1
    ''', [row['group_key'], file_id]).fetchone()
    if png_row:
        return send_from_directory(str(Path(png_row['abs_path']).parent), png_row['filename'])

    # 没 png → 返回 SVG 占位(根据 ext 给颜色)
    ext = row['ext'].lower()
    color_map = {
        'skp': '#059669', 'rvt': '#2563eb',
        'dwg': '#dc2626', 'pdf': '#ff9e4a',
        'md':  '#64748b', 'docx': '#1d4ed8', 'doc': '#1d4ed8',
    }
    color = color_map.get(ext, '#64748b')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 160" width="220" height="160">
  <rect width="220" height="160" fill="#1a1a1a"/>
  <rect x="20" y="30" width="180" height="100" rx="8" fill="{color}" opacity="0.18"/>
  <rect x="20" y="30" width="180" height="100" rx="8" fill="none" stroke="{color}" stroke-width="2"/>
  <text x="110" y="78" text-anchor="middle" font-family="Arial,sans-serif" font-size="22" font-weight="700" fill="{color}">{ext.upper()}</text>
  <text x="110" y="106" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="#94a3b8">{(row['filename'] or '')[:24]}</text>
</svg>'''
    return svg, 200, {'Content-Type': 'image/svg+xml; charset=utf-8'}


# ============================================================
# 07-Tectonic 文件本地预览(SKP/PDF/DWG/RVT/PNG/SVG)
# 不做转换,直接给一个"用本机默认应用打开"的链接
# ============================================================

@app.route('/api/file/open/<int:file_id>')
def open_file(file_id):
    """打开本机文件(返回 file:// URL + 提示用户用本机应用打开)"""
    db = get_db()
    row = db.execute('SELECT abs_path, filename, ext FROM tectonic_files WHERE id = ?', [file_id]).fetchone()
    if not row:
        return jsonify({'error': '文件不存在'}), 404
    return jsonify({
        'abs_path': row['abs_path'],
        'filename': row['filename'],
        'ext':      row['ext'],
        'open_url': 'file:///' + row['abs_path'].replace('\\', '/'),
        'note':     '请用本机默认应用打开(如 SKP 用 SketchUp,DWG 用 AutoCAD)'
    })


# ============================================================
# MCP 调度接口(骨架,见 mcp_dispatch.py)
# ============================================================

@app.route('/api/mcp/dispatch', methods=['POST'])
def mcp_dispatch():
    """
    概念图 → AI 识别 → 构造推荐 → MCP 生成(待实现)
    入参: { image_url?, keyword?, target_model: 'sketchup'|'rhino'|'revit' }
    出参: { status, matched_methods, mcp_call_id, todo }
    """
    from mcp_dispatch import dispatch
    return jsonify(dispatch(request.json or {}))


@app.route('/api/mcp/status')
def mcp_status():
    """MCP 调度模块状态(可用性 + 待办)"""
    from mcp_dispatch import get_status
    return jsonify(get_status())

# ============================================================
if __name__ == '__main__':
    print(f"建筑构造数据库 API")
    print(f"数据库: {DB_PATH}")
    print(f"前端:   {STATIC_DIR}")
    print(f"访问:   http://localhost:5189")
    app.run(host='0.0.0.0', port=5189, debug=True)