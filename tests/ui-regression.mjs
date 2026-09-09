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
  ['played destination card is withheld while its flight ghost is active', html.includes('flightCardIds') && /pegHistory\.filter\([^)]*flightCardIds/i.test(html)],
  ['all gameplay and result cards share one player-card size token', html.includes('--game-card-w:94px') && html.includes('--game-card-h:134px') && html.includes('#resultCards') && html.includes('var(--game-card-w)')],
  ['illegal cards stay colored and become transparent instead of desaturated', /\.card\.illegal\s*\{[^}]*opacity\s*:\s*\.2[0-9][^}]*filter\s*:\s*none/i.test(html)],
  ['result cards have explicit breathing room above Done', /#resultModal\s+#resultCards\s*\{[^}]*margin-bottom\s*:\s*(2[4-9]|[3-9][0-9])px/i.test(html)],
  ['QQND shared server multiplayer client is loaded', html.includes('multiplayer-server.js') && !html.includes('new RTCPeerConnection(')],
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
