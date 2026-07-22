import requests, json
print('=== /api/mcp/dispatch (keyword=屋面) ===')
r = requests.post('http://127.0.0.1:5189/api/mcp/dispatch', json={'keyword': '屋面', 'target_model': 'sketchup'})
d = r.json()
print('status:', d['status'])
print('matched:')
for m in d['matched_methods']:
    print('  #' + str(m['id']) + ' | ' + (m['name'] or '')[:50] + ' | files=' + str(m['file_count']) + ' | part=' + str(m.get('part') or '-') + ' | atlas=' + str(m.get('atlas') or '-'))
print('mcp_call.callable:', d['mcp_call']['callable'])
print('mcp_call.todo:', d['mcp_call']['todo'])
