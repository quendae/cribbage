from pathlib import Path
p=Path('scripts/apply_server_multiplayer_b1.py')
s=p.read_text(encoding='utf-8')
old="s, n = re.subn(r'  const mpEl=id=>document\\.getElementById\\(id\\);.*?  function hiddenCards', transport, s, count=1, flags=re.S)"
new="s, n = re.subn(r'  const mpEl=id=>document\\.getElementById\\(id\\);.*?  function hiddenCards', lambda _m: transport, s, count=1, flags=re.S)"
if old not in s:
    raise SystemExit('target replacement not found')
p.write_text(s.replace(old,new,1),encoding='utf-8')
print('Fixed literal regex replacement.')
