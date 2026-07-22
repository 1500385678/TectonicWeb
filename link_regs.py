import sqlite3
c = sqlite3.connect(r'D:\Mac\Mac\workteam\05_space\03_architect\_ArchitectLib\TectonicDb\construction.db')
c.row_factory = sqlite3.Row

# 找法规
regs = {r['code']: r['id'] for r in c.execute('SELECT id, code FROM regulations').fetchall()}
methods = c.execute('SELECT id, name FROM construction_methods').fetchall()

# 给屋面/幕墙做法关联 GB 50345、GB 50176
# 屋面规范: GB 50345 + GB 50176 + GB 55015
# 墙体规范: GB 50016 + JGJ 149 + JGJ/T 480
# 楼地面规范: GB 50118 + GB 50209
# 幕墙规范: GB 50016 + GB 50345
# 防水通用: GB 50345

mapping = [
    # method_code_prefix, [regulation_codes]
    ('ROOF_', ['GB 50345-2012', 'GB 50176-2016', 'GB 55015-2021', 'GB 50016-2014']),
    ('WALL_', ['GB 50016-2014', 'GB 55015-2021', 'JGJ 149-2017', 'JGJ/T 480-2019']),
    ('FLOOR_', ['GB 50118-2010', 'GB 50209-2010', 'GB 50010-2010']),
    ('FOUNDATION_', ['GB 50007-2011', 'GB 50010-2010']),
    ('JOINT_', ['GB 50003-2011', 'GB 50011-2010', 'GB 50007-2011']),
    ('CURTAIN_', ['GB 50016-2014', 'GB 50345-2012', 'JGJ 102-2003']),
    ('WINDOW_', ['GB 50016-2014', 'JGJ 113-2015']),
]

# 绿化屋面加 JGJ 155
# 防水楼面加 JGJ 298

count = 0
for m in methods:
    prefix = m['name'][:5]  # 不靠谱，简单用 id 范围
    mid = m['id']

    # 用 category_id 决定
    cat_id = c.execute('SELECT category_id FROM construction_methods WHERE id=?', [mid]).fetchone()['category_id']
    cat_code_row = c.execute('SELECT code FROM categories WHERE id=?', [cat_id]).fetchone()
    cat_code = cat_code_row['code'] if cat_code_row else ''

    codes = []
    if cat_code == 'roof':
        codes = ['GB 50345-2012', 'GB 50176-2016', 'GB 55015-2021', 'GB 50016-2014']
        if '绿化' in m['name']:
            codes.append('JGJ 155-2013')
    elif cat_code == 'wall':
        codes = ['GB 50016-2014', 'GB 55015-2021']
        if 'EPS' in m['name']:
            codes.append('JGJ 149-2017')
        if '岩棉' in m['name']:
            codes.append('JGJ/T 480-2019')
        if '砌' in m['name'] or '砖' in m['name']:
            codes.append('GB 50003-2011')
        if '混凝土' in m['name'] or '剪力' in m['name']:
            codes.append('GB 50010-2010')
    elif cat_code == 'floor':
        codes = ['GB 50118-2010', 'GB 50209-2010', 'GB 50010-2010']
        if '卫生间' in m['name'] or '防水' in m['name']:
            codes.append('JGJ 298-2013')
    elif cat_code == 'foundation':
        codes = ['GB 50007-2011', 'GB 50010-2010', 'GB 50016-2014']
    elif cat_code == 'joint':
        codes = ['GB 50003-2011', 'GB 50011-2010']
    elif cat_code == 'curtain':
        codes = ['GB 50016-2014', 'GB 50345-2012']
    elif cat_code == 'door_win':
        codes = ['GB 50016-2014']

    for code in codes:
        if code in regs:
            # 检查是否已存在
            exist = c.execute('SELECT 1 FROM method_regulations WHERE method_id=? AND regulation_id=?', [mid, regs[code]]).fetchone()
            if not exist:
                c.execute('INSERT INTO method_regulations (method_id, regulation_id, clause_ref, clause_summary) VALUES (?, ?, ?, ?)',
                          [mid, regs[code], '相关章节', f'{m["name"]}相关条文'])
                count += 1

c.commit()
print(f'新增规范关联: {count} 条')

# 验证
total = c.execute('SELECT COUNT(*) FROM method_regulations').fetchone()[0]
print(f'总关联数: {total}')