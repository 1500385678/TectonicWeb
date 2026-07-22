import requests, json
BASE = 'http://127.0.0.1:5189'

print('=== /api/files (默认) ===')
r = requests.get(BASE + '/api/files')
d = r.json()
print(f'total: {d["total"]}')
print('前 3 条:')
for f in d['items'][:3]:
    print(f'  - {f["ext"].upper():4s} {f["filename"][:50]:50s} thumb={f["thumbnail_url"]}')

print('\n=== /api/files?ext=skp ===')
r = requests.get(BASE + '/api/files', params={'ext': 'skp'})
d = r.json()
print(f'共 {d["total"]} 个 SKP:')
for f in d['items']:
    print(f'  - {f["filename"]} (part={f.get("part_name", "-")}, atlas={f.get("atlas_name", "-")})')

print('\n=== /api/files?dim=part:001_Walls ===')
r = requests.get(BASE + '/api/files', params={'dim': 'part:001_Walls'})
d = r.json()
print(f'001_Walls 维度下 {d["total"]} 个文件:')
for f in d['items'][:5]:
    print(f'  - {f["ext"].upper():4s} {f["filename"][:60]}')

print('\n=== /api/files/filters ===')
r = requests.get(BASE + '/api/files/filters')
d = r.json()
print(f'总文件: {d["total_files"]}')
print(f'ext 分布: {d["ext_counts"]}')
print(f'role 分布: {d["role_counts"]}')
print(f'部件(part)分类数: {len(d["dims"]["part"])}')
print(f'技能(skill)分类数: {len(d["dims"]["skill"])}')
print(f'图集(atlas)分类数: {len(d["dims"]["atlas"])}')

print('\n=== /api/files?q=D07 ===')
r = requests.get(BASE + '/api/files', params={'q': 'D07'})
d = r.json()
print(f'关键字 D07 命中 {d["total"]} 个:')
for f in d['items'][:5]:
    print(f'  - {f["ext"].upper():4s} {f["filename"]}')

print('\n=== /api/media/thumb/85 (D07.pdf 应找同组 PNG) ===')
# 找 D07 PDF 的 file_id
r = requests.get(BASE + '/api/files', params={'q': 'D07', 'ext': 'pdf'})
d = r.json()
if d['items']:
    fid = d['items'][0]['id']
    r = requests.get(BASE + f'/api/media/thumb/{fid}')
    print(f'  thumb 响应: status={r.status_code}, type={r.headers.get("content-type")}, size={len(r.content)} bytes')
    if r.status_code == 200 and 'image' in r.headers.get('content-type', ''):
        print(f'  -> 返回的是真实图片(同组 PNG)')
    elif r.status_code == 200 and 'svg' in r.headers.get('content-type', ''):
        print(f'  -> 返回的是 SVG 占位(无 PNG)')
