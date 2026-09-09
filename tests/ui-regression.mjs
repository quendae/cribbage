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
