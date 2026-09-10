import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const html = fs.readFileSync(path.join(here, '..', 'index.html'), 'utf8');

const checks = [
  ['reference-inspired two-lane board is installed', html.includes('two-lane-reference-v2')],
  ['selected cards no longer move vertically', /\.card\.selected\s*\{[^}]*transform\s*:\s*none/i.test(html)],
  ['card backs use the SKAT-family navy stripe palette', html.includes('#19375d') && html.includes('#244d80')],
  ['new board path generator exists', html.includes('boardTrackPathV2')],
  ['main menu exposes one multiplayer entry', html.includes('data-action="multiplayer-choice"') && !html.includes('data-action="new-local"') && !html.includes('data-action="multiplayer-p2p"')],
  ['multiplayer choice offers local and online', html.includes('id="multiplayerChoiceModal"') && html.includes('data-action="multiplayer-local"') && html.includes('data-action="multiplayer-online"')],
  ['bot setup no longer offers local mode selector', html.includes('id="gameMode" type="hidden"') && !html.includes('<select id="gameMode"')],
  ['offline scoring modal waits for card flights', html.includes('afterCardFlights(()=>openShowItem())') && html.includes('afterCardFlights(()=>showGameOverModal(p))')],
  ['31 reset waits for the played card to land', html.includes('afterCardFlights(()=>resetPegSequence(1-p))')],
  ['table log uses themed scrollbar', html.includes('.log::-webkit-scrollbar') && html.includes('scrollbar-color:rgba(215,180,94')],
  ['count orb is fixed at the approved table-center position', html.includes('.felt>.count-orb{position:absolute;left:50%;top:68%;transform:translate(-50%,-50%)') && html.includes('</div><div id="countOrb" class="count-orb">0<small>/ 31</small></div>')],
  ['approved v1 layout values are fixed in CSS', html.includes('--dev-starter-x:-40px;--dev-starter-y:60px') && html.includes('--dev-crib-x:40px;--dev-crib-y:60px') && html.includes('--dev-controls-y:-50px')],
  ['production tab title drops Offline and identifies v1', html.includes('<title>Cribbage</title>') && html.includes('<meta name="application-version" content="1.0.0">') && !html.includes('<title>Cribbage Offline</title>')],
  ['developer tuning UI is removed from production', !html.includes('id="devUiToggle"') && !html.includes('id="devUiPanel"') && !html.includes('cribbageUiV2DevScript') && !html.includes('window.cribbageDevUI') && !html.includes("e.key==='F2'")],
  ['top rules control and legacy rules modal are removed', !html.includes('data-action="rules"') && !html.includes('id="rulesModal"') && !html.includes('function renderRules()') && !html.includes('const ruleItems=')],
  ['left scoring reference covers all show and pegging variants', html.includes('scoreReferenceItems') && html.includes('help.show') && html.includes('help.peg') && html.includes('help.fifteens') && html.includes('help.pairsAll') && html.includes('help.runsAll') && html.includes('help.flushAll') && html.includes('help.nobs') && html.includes('help.heels') && html.includes('help.peg15') && html.includes('help.peg31') && html.includes('help.pegPairs') && html.includes('help.pegRuns') && html.includes('help.last')],
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
