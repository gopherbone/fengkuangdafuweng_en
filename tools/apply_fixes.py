import json, glob, sys
for f in sys.argv[1:]:
    fx = json.load(open(f))
    for gid, d in fx.items():
        p = gid[0]; tf = f'/Users/nick/crazyrichman_claude/font/table_p{p}.json'
        t = json.load(open(tf)); key = gid.upper()
        assert t[key] == d['from'], (gid, t[key], d)
        t[key] = d['to']; json.dump(t, open(tf, 'w'), ensure_ascii=False, indent=0)
        print(gid, d['from'], '->', d['to'])
