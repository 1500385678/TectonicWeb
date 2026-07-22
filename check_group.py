import sqlite3, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
conn = sqlite3.connect(r'D:\Mac\Mac\workteam\05_space\03_architect\_ArchitectLib\TectonicDb\construction.db')
conn.row_factory = sqlite3.Row
print('=== D07 节点所有文件(应同组) ===')
for f in conn.execute("""
    SELECT t.filename, t.ext, t.group_key
    FROM tectonic_files t
    WHERE t.group_key LIKE 'D07%'
    ORDER BY t.group_key, t.filename
"""):
    print('  ' + f['ext'].ljust(4) + ' group=' + f['group_key'].ljust(50) + ' | ' + f['filename'])
print()
print('=== D07 method 详情 ===')
for m in conn.execute("""
    SELECT m.id, m.name, m.atlas_code, m.file_count
    FROM construction_methods m
    WHERE m.atlas_code = 'D07'
    ORDER BY m.id
"""):
    print('  #' + str(m['id']) + ' ' + m['name'] + ' files=' + str(m['file_count']))
