import sqlite3, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
conn = sqlite3.connect(r'D:\Mac\Mac\workteam\05_space\03_architect\_ArchitectLib\TectonicDb\construction.db')
conn.row_factory = sqlite3.Row

print('=== dim_part ===')
for r in conn.execute('SELECT * FROM dim_part ORDER BY sort_order'):
    print('  ' + r['code'].ljust(15) + ' | ' + r['name_zh'])

print('=== dim_atlas ===')
for r in conn.execute('SELECT * FROM dim_atlas ORDER BY sort_order'):
    print('  ' + r['code'].ljust(15) + ' | ' + r['name'])

print('=== method 样本 ===')
for r in conn.execute('''
    SELECT m.id, m.name, m.atlas_code, m.file_count, p.name_zh AS part, a.name AS atlas
    FROM construction_methods m
    LEFT JOIN dim_part p ON m.dim_part_id = p.id
    LEFT JOIN dim_atlas a ON m.dim_atlas_id = a.id
    WHERE m.file_count > 0
    ORDER BY m.id LIMIT 8
'''):
    print('  #' + str(r['id']).ljust(2) + ' | ' + (r['name'] or '')[:50].ljust(50) + ' | part=' + str(r['part'] or '-') + ' | atlas=' + str(r['atlas'] or '-') + ' | files=' + str(r['file_count']))

print('=== file 样本 ===')
for r in conn.execute('SELECT id, filename, ext, source_type, role, group_key FROM tectonic_files LIMIT 5'):
    print('  ' + r['ext'].ljust(5) + ' ' + r['source_type'].ljust(6) + ' ' + r['role'].ljust(8) + ' | ' + r['filename'][:60])

print('=== 统计 ===')
print('  methods(with files):', conn.execute('SELECT COUNT(*) AS n FROM construction_methods WHERE file_count > 0').fetchone()['n'])
print('  files total       :', conn.execute('SELECT COUNT(*) AS n FROM tectonic_files').fetchone()['n'])
print('  skp                :', conn.execute("SELECT COUNT(*) AS n FROM tectonic_files WHERE ext='skp'").fetchone()['n'])
print('  pdf                :', conn.execute("SELECT COUNT(*) AS n FROM tectonic_files WHERE ext='pdf'").fetchone()['n'])
print('  png                :', conn.execute("SELECT COUNT(*) AS n FROM tectonic_files WHERE ext='png'").fetchone()['n'])
print('  md                 :', conn.execute("SELECT COUNT(*) AS n FROM tectonic_files WHERE ext='md'").fetchone()['n'])
