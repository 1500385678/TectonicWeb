import sqlite3, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
conn = sqlite3.connect(r'D:\Mac\Mac\workteam\05_space\03_architect\_ArchitectLib\TectonicDb\construction.db')
conn.row_factory = sqlite3.Row
print('=== D07 所有文件 + 截断后的 group_key ===')
for f in conn.execute("""
    SELECT t.filename, t.ext, t.group_key, t.id
    FROM tectonic_files t
    WHERE t.method_id IN (SELECT id FROM construction_methods WHERE atlas_code = 'D07')
    ORDER BY t.id
"""):
    gk = f['group_key']
    print('  id=' + str(f['id']).ljust(3) + f['ext'].ljust(4) + ' gk="' + gk + '" (len=' + str(len(gk)) + ') | ' + f['filename'])
