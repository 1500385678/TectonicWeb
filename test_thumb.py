import requests, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
BASE = 'http://127.0.0.1:5189'

# 1. D07 PDF 应返回同组 PNG
r = requests.get(BASE + '/api/files', params={'q': 'D07 Interseccion', 'ext': 'pdf'})
d = r.json()
print('D07 PDF 共', d['total'], '个')
if d['items']:
    fid = d['items'][0]['id']
    r = requests.get(BASE + '/api/media/thumb/' + str(fid))
    ct = r.headers.get('content-type', '')
    print('  thumb/' + str(fid) + ': status=' + str(r.status_code) + ', type=' + ct + ', size=' + str(len(r.content)))
    print('  -> ' + ('返回了同组 PNG!' if 'png' in ct else ('返回 SVG 占位' if 'svg' in ct else '其他')))

# 2. D07 SKP 应返回同组 PNG
r = requests.get(BASE + '/api/files', params={'q': 'D07+Interseccion', 'ext': 'skp'})
d = r.json()
print('D07 SKP 共', d['total'], '个')
if d['items']:
    fid = d['items'][0]['id']
    r = requests.get(BASE + '/api/media/thumb/' + str(fid))
    ct = r.headers.get('content-type', '')
    print('  thumb/' + str(fid) + ': status=' + str(r.status_code) + ', type=' + ct + ', size=' + str(len(r.content)))
    print('  -> ' + ('返回了同组 PNG!' if 'png' in ct else ('返回 SVG 占位' if 'svg' in ct else '其他')))

# 3. MD 文件(无 PNG),应返回 SVG 占位
r = requests.get(BASE + '/api/files', params={'ext': 'md'})
d = r.json()
if d['items']:
    fid = d['items'][0]['id']
    r = requests.get(BASE + '/api/media/thumb/' + str(fid))
    ct = r.headers.get('content-type', '')
    print('  thumb/' + str(fid) + ' (MD): status=' + str(r.status_code) + ', type=' + ct + ', size=' + str(len(r.content)))
    print('  -> ' + ('返回 SVG 占位 (预期)' if 'svg' in ct else '其他'))

# 4. 综合验证
r = requests.get(BASE + '/api/files')
d = r.json()
print('\n=== 综合 ===')
print('总文件:', d['total'])
# 看哪些 PNG 自己是 PNG(直接返回)
png_self = sum(1 for f in d['items'] if f['ext'] == 'png')
print('PNG 自身:', png_self, '(每个都直接显示)')
# 看 MD/SKP/PDF 是否能通过同组 PNG 拿到缩略图
needing_thumb = [f for f in d['items'] if f['ext'] != 'png']
print('需同组 PNG 的文件:', len(needing_thumb))
# 统计有 PNG 同组的数量(粗估:看 thumbnail_url 返回 content-type)
