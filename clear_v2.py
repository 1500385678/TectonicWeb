import sqlite3, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
conn = sqlite3.connect(r'D:\Mac\Mac\workteam\05_space\03_architect\_ArchitectLib\TectonicDb\construction.db')

# 只删 v2 批次(atlas_code 非空 = 本次扫描的)
m1 = conn.execute('SELECT COUNT(*) FROM construction_methods WHERE atlas_code IS NOT NULL').fetchone()[0]
f1 = conn.execute('''
    SELECT COUNT(*) FROM tectonic_files t
    JOIN construction_methods m ON t.method_id = m.id
    WHERE m.atlas_code IS NOT NULL
''').fetchone()[0]
print(f'将清理: {m1} methods + {f1} files')

conn.execute('DELETE FROM tectonic_files WHERE method_id IN (SELECT id FROM construction_methods WHERE atlas_code IS NOT NULL)')
conn.execute('DELETE FROM construction_methods WHERE atlas_code IS NOT NULL')
conn.commit()

m = conn.execute('SELECT COUNT(*) FROM construction_methods').fetchone()[0]
f = conn.execute('SELECT COUNT(*) FROM tectonic_files').fetchone()[0]
print(f'清理后: methods={m}, files={f} (应为 v1 原始数据)')
