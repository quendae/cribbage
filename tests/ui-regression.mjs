import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const html = fs.readFileSync(path.join(here, '..', 'index.html'), 'utf8');

const checks = [
  ['reference-inspired two-lane board is installed', html.includes('two-lane-reference-v2')],
  ['selected cards no longer move vertically', /\.card\.selected\s*\{[^}]*transform\s*:\s*none/i.test(html)],
  ['card backs use the SKAT-family navy stripe palette', html.includes('#19375d') && html.includes('#244d80')],
  ['developer tuning panel exists', html.includes('id="devUiPanel"')],
  ['developer tuning values persist locally', html.includes('cribbage.devUI.v1')],
  ['developer tuning values can be copied', html.includes('id="devUiCopy"')],
  ['new board path generator exists', html.includes('boardTrackPathV2')],
  ['main menu exposes one multiplayer entry', html.includes('data-action="multiplayer-choice"') && !html.includes('data-action="new-local"') && !html.includes('data-action="multiplayer-p2p"')],
  ['multiplayer choice offers local and online', html.includes('id="multiplayerChoiceModal"') && html.includes('data-action="multiplayer-local"') && html.includes('data-action="multiplayer-online"')],
  ['bot setup no longer offers local mode selector', html.includes('id="gameMode" type="hidden"') && !html.includes('<select id="gameMode"')],
  ['offline scoring modal waits for card flights', html.includes('afterCardFlights(()=>openShowItem())') && html.includes('afterCardFlights(()=>showGameOverModal(p))')],
  ['31 reset waits for the played card to land', html.includes('afterCardFlights(()=>resetPegSequence(1-p))')],
  ['table log uses themed scrollbar', html.includes('.log::-webkit-scrollbar') && html.includes('scrollbar-color:rgba(215,180,94')],
  ['count orb has independent developer tuning', html.includes('--dev-count-x:0px') && html.includes("{key:'countX',label:'Licznik X'") && html.includes("{key:'countY',label:'Licznik Y'") && html.includes("{key:'countScale',label:'Licznik scale'")],
  ['count orb defaults to the table center between cards and controls', html.includes('.felt>.count-orb{position:absolute;left:50%;top:68%;transform:translate(-50%,-50%)') && html.includes('translate:var(--dev-count-x) var(--dev-count-y);scale:var(--dev-count-scale)') && html.includes('</div><div id="countOrb" class="count-orb">0<small>/ 31</small></div>')],
  ['approved dev tuning values are baked in', html.includes('starterX:-40,starterY:60,cribX:40,cribY:60') && html.includes('controlsY:-50')],
];

let failed = 0;
for (const [name, ok] of checks) {
  if (ok) console.log(`PASS  ${name}`);
  else {
    console.error(`FAIL  ${name}`);
    failed += 1;
  }
}

if (failed) {
  console.error(`\n${failed} UI regression check(s) failed.`);
  process.exit(1);
}

console.log('\nAll UI regression checks passed.');
