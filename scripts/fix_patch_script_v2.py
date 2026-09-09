from pathlib import Path
import re
p=Path('scripts/apply_server_multiplayer_b1.py')
s=p.read_text(encoding='utf-8')
replacement='''new_tick = "  function networkTick(){if(mp.role!==\\'host\\'||!mp.connected||!mp.inGame||!mp.client||!state)return;const view=guestView(),signature=JSON.stringify(view);if(signature===mp.lastSignature)return;mp.lastSignature=signature;mp.revision=(mp.revision||0)+1;mp.client.commit(mp.revision,state);const guest=mp.roomData?.players?.find(p=>p.id!==mp.client.session?.id);if(guest)mp.client.publish(mp.revision,guest.id,view)}\\n  function sendGuestAction(action,payload={}){if(mp.role!==\\'guest\\'||!mp.connected||!mp.client)return;mp.client.action(action,payload)}"
s, n = re.subn(r"  function networkTick\\(\\)\\{.*?\\}\\n  function sendGuestAction\\(action,payload=\\{\\}\\)\\{.*?\\}", lambda _m: new_tick, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('network tick replace failed')

'''
pattern=r"old_tick = r\".*?if old_tick not in s:\n    raise SystemExit\('network tick marker missing'\)\ns = s\.replace\(old_tick, new_tick, 1\)\n\n"
s2,n=re.subn(pattern,lambda _m:replacement,s,count=1,flags=re.S)
if n!=1:
    raise SystemExit('old network tick patch code not found')
p.write_text(s2,encoding='utf-8')
print('Fixed network tick patch logic.')
