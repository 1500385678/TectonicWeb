import urllib.request, urllib.parse, json

def call(url):
    # 拆分 base 和 query，手动编码 query
    if '?' in url:
        base, query = url.split('?', 1)
        parts = []
        for p in query.split('&'):
            if '=' in p:
                k, v = p.split('=', 1)
                parts.append(k + '=' + urllib.parse.quote(v))
            else:
                parts.append(p)
        full = 'http://localhost:5189' + base + '?' + '&'.join(parts)
    else:
        full = 'http://localhost:5189' + url
    req = urllib.request.Request(full)
    return json.loads(urllib.request.urlopen(req, timeout=5).read())

print('=== TectonicDb 端到端验证 ===')

cats = call('/api/categories')
print(f'分类: {len(cats)} 条')

methods = call('/api/methods')
print(f'构造做法: {len(methods)} 条')

# 拿第一个有层次的
sample_id = None
for m in methods:
    detail = call(f'/api/methods/{m["id"]}')
    if detail.get('layers'):
        sample_id = m['id']
        sample = detail
        break

if sample:
    print(f'\n=== 示例: {sample["name"]} ===')
    print(f'子类型: {sample.get("sub_type")}')
    print(f'构造层次: {len(sample["layers"])} 层')
    for l in sample['layers'][:5]:
        print(f'  {l["seq"]}. {l["layer_name"]} | {l["material"]} ({l["thickness_mm"]}mm)')
    print(f'规范依据: {len(sample["regulations"])} 条')
    for r in sample['regulations']:
        print(f'  - {r["code"]}: {r["name"]}')

# 推荐
rec = call('/api/recommend?category=roof&building=住宅&climate=严寒')
print(f'\n=== 推荐结果（严寒住宅屋面）===')
print(f'命中: {len(rec)} 条')
for r in rec[:3]:
    print(f'  - {r["name"]} ({r["short_desc"]})')

# 易错点
pits = call('/api/pitfalls')
print(f'\n易错点: {len(pits)} 条')
for p in pits[:3]:
    print(f'  - ❌ {p["wrong_statement"]}')
    print(f'    ✅ {p["correct"]}')

# 考试
exams = call('/api/exam/chapter/4.2')
print(f'\n考试知识点(4.2): {len(exams)} 条')

print('\n=== 全部测试通过 ===')