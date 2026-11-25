import io, json, re, sys, os
sys.stdout.reconfigure(encoding='utf-8')
M = sys.argv[1]; CFG = json.load(open(M + '/' + sys.argv[2], encoding='utf-8')); sys.path.insert(0, M)
from cities import C
t = io.open('C:/Claude/family-tree/index.html', encoding='utf-8', newline='').read()
BS = chr(92); QQ = chr(34)

def field(L, k):
    for pre in ('{', ','):
        a = L.find(pre + k + ':' + QQ)
        if a >= 0: break
    else: return ''
    q = a + len(k) + 3; r = []
    while True:
        c = L[q]
        if c == BS: r.append(L[q+1] if L[q+1] != 'n' else ' '); q += 2; continue
        if c == QQ: break
        r.append(c); q += 1
    return ''.join(r)

ids = [i for i in open(M + '/' + CFG['ids'], encoding='utf-8').read().strip().split(',') if i and i not in CFG.get('exclude', [])]
people = []
for i in ids:
    m = re.search(r'\n[ \t]+' + re.escape(i) + r':\{', t)
    if not m: print('  missing card', i); continue
    k = m.start()
    L = t[k+1:t.find('\n', k+1)]
    people.append(dict(id=i, s=field(L, 's'), b=field(L, 'b'), d=field(L, 'd'), place=field(L, 'place')))

a = t.find('const Y={'); ytxt = t[a:t.find('\n', a)]
Ymap = {m.group(1): (m.group(2), m.group(3)) for m in re.finditer(r"([a-z_0-9]+):\['([^']*)','([^']*)'\]", ytxt)}
AL = sorted([(al, k) for k, v in C.items() for al in v[4]], key=lambda x: -len(x[0]))
HEB = re.compile('[\u05d0-\u05ea]')
UNC = ('כנראה', ' או ', 'ככל הנראה')

def find(text):
    res = []; s = text
    for al, k in AL:
        i = 0
        while True:
            j = s.find(al, i)
            if j < 0: break
            pre = s[j-1] if j > 0 else ' '
            post = s[j+len(al)] if j+len(al) < len(s) else ' '
            pre2 = s[j-2] if j > 1 else ' '
            if pre in 'בוול' and not HEB.match(pre2): pre = ' '
            if (HEB.match(al[0]) and HEB.match(pre)) or (HEB.match(al[-1]) and HEB.match(post)):
                i = j + 1; continue
            sa = max(s.rfind('←', 0, j), s.rfind('·', 0, j), 0)
            ends = [x for x in (s.find('←', j), s.find('·', j)) if x >= 0]
            seg = s[sa:(min(ends) if ends else len(s))]
            unc = any(w in seg for w in UNC)
            res.append((k, unc, j)); s = s[:j] + '#' * len(al) + s[j+len(al):]; i = j + len(al)
    return [(k, u) for k, u, j in sorted(res, key=lambda x: x[2])]

def strip_burial(x):
    # drop only the parts (between · or after a full stop) that speak of burial
    parts = re.split(r'·|\.\s', x)
    return ' · '.join(p for p in parts if not re.search('נקבר|קבורה|קבור ', p + ' '))

cities = {k: {'k': k, 'he': v[0], 'en': v[1], 'lat': v[2], 'lon': v[3], 'b': [], 'l': [], 'd': []} for k, v in C.items()}
for p in people:
    i = p['id']
    if re.search(r'_kids$|_sibs$|_sib$', i): continue
    y = Ymap.get(i, ('?', '?'))
    yr = '' if y == ('?', '?') else (y[0] + '–' + y[1]).replace('?', '')
    e = {'id': i, 'n': p['s'], 'y': yr}
    for role, txt in (('b', p['b']), ('d', strip_burial(p['d'])), ('l', strip_burial(p['place']))):
        seen = set()
        for k, u in find(txt):
            if k in seen: continue
            if role == 'l' and k == 'auschwitz': continue  # a death camp is never a place where someone lived (Esti, 24.11.2026)
            seen.add(k)
            cities[k][role].append(dict(e, u=1) if u else e)
# each person's route in order: birth city, then the residence chain, then the death city
ROUTES = []
for p in people:
    i = p['id']
    if re.search(r'_kids$|_sibs$|_sib$', i): continue
    y = Ymap.get(i, ('?', '?'))
    yr = '' if y == ('?', '?') else (y[0] + '–' + y[1]).replace('?', '')
    steps = []
    def add(k, role, note, u):
        note = note.strip()[:90]
        if steps and steps[-1]['k'] == k:
            s = steps[-1]
            if role not in s['r']: s['r'] += role
            if note and note not in s['t']: s['t'].append(note)
            if u: s['u'] = 1
            return
        steps.append({'k': k, 'r': role, 't': [note] if note else [], 'u': 1 if u else 0})
    for k, u in find(p['b'])[:1]: add(k, 'b', p['b'], u)
    for seg in strip_burial(p['place']).split('←'):
        for k, u in find(seg):
            if k == 'auschwitz': continue
            add(k, 'l', seg, u)
    dd = strip_burial(p['d'])
    for k, u in find(dd)[:1]: add(k, 'd', dd, u)
    for s in steps:
        names = set([C[s['k']][0]] + C[s['k']][4])
        s['t'] = [t for t in s['t'] if t.strip(' ,.') not in names]
    if steps: ROUTES.append({'n': p['s'], 'y': yr, 's': steps})
print('routes', len(ROUTES))
used = {k: v for k, v in cities.items() if v['b'] or v['l'] or v['d']}
print('people', len(people), 'cities used', len(used))
for k, v in sorted(used.items(), key=lambda kv: -(len(kv[1]['b']) + len(kv[1]['l']) + len(kv[1]['d']))):
    print(' ', v['he'], len(v['b']), len(v['l']), len(v['d']))
tpl = io.open(M + '/template.html', encoding='utf-8').read()
cfg = {kk: CFG[kk] for kk in ('view', 'lim')}
html = (tpl.replace('/*DATA*/[]', json.dumps(list(used.values()), ensure_ascii=False))
           .replace('/*LAND*/{}', io.open(M + '/land.json', encoding='utf-8').read())
           .replace('/*CFG*/{}', json.dumps(cfg))
           .replace('/*PEOPLE*/[]', json.dumps(ROUTES, ensure_ascii=False))
           .replace('__TREE__', CFG['tree']).replace('__HOME__', CFG['home']))
out = 'C:/Claude/family-tree/' + CFG['dir']
os.makedirs(out, exist_ok=True)
io.open(out + '/index.html', 'w', encoding='utf-8', newline='\n').write(html)
print('written', out, len(html))
