import sqlite3, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
conn = sqlite3.connect(r'D:\Mac\Mac\workteam\05_space\03_architect\_ArchitectLib\TectonicDb\construction.db')
conn.row_factory = sqlite3.Row
print('=== 001_Walls 维度的 method ===')
for r in conn.execute('''SELECT m.id, m.name, m.atlas_code, m.file_count
    FROM construction_methods m
    WHERE m.dim_part_id = (SELECT id FROM dim_part WHERE code='001_Walls')
    ORDER BY m.id'''):
    print('  #' + str(r['id']) + ' | ' + (r['name'] or '')[:60] + ' | files=' + str(r['file_count']))
    for f in conn.execute('SELECT filename, ext, role FROM tectonic_files WHERE method_id = ?', [r['id']]):
        print('       - ' + f['ext'].ljust(5) + ' ' + f['role'].ljust(8) + ' | ' + f['filename'])
