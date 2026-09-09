import fs from 'node:fs';
import { chromium } from 'playwright';

fs.mkdirSync('qa', { recursive: true });
const browser = await chromium.launch({ headless: true });
const errors = [];
const warnings = [];
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
page.on('pageerror', err => errors.push(`pageerror: ${err.message}`));
page.on('console', msg => {
  if (msg.type() === 'error') errors.push(`console: ${msg.text()}`);
  if (msg.type() === 'warning') warnings.push(msg.text());
});

await page.goto('http://127.0.0.1:4173/index.html', { waitUntil: 'networkidle' });
const title = await page.title();
if (!title.includes('Cribbage')) throw new Error(`Unexpected title: ${title}`);
if (!(await page.locator('#mainMenu').isVisible())) throw new Error('Main menu did not render.');

await page.locator('[data-action="new-bot"]').click();
await page.locator('[data-action="start-game"]').click();
await page.waitForSelector('#bottomHand .card');
await page.waitForTimeout(120);

const board = page.locator('#cribbageBoard');
const felt = page.locator('.felt');
const boardBox = await board.boundingBox();
const feltBox = await felt.boundingBox();
if (!boardBox || !feltBox) throw new Error('Board or felt is not measurable.');
if (await board.locator('.board-track').count() !== 2) throw new Error('Expected exactly two active scoring tracks.');
if (await board.locator('.board-hole').count() !== 244) throw new Error(`Unexpected hole count: ${await board.locator('.board-hole').count()}`);
if (boardBox.x < feltBox.x - 1 || boardBox.y < feltBox.y - 1 || boardBox.x + boardBox.width > feltBox.x + feltBox.width + 1 || boardBox.y + boardBox.height > feltBox.y + feltBox.height + 1) {
  throw new Error(`Board overflows felt: board=${JSON.stringify(boardBox)} felt=${JSON.stringify(feltBox)}`);
}

const back = page.locator('#topHand .card-back').first();
const backBg = await back.evaluate(el => getComputedStyle(el).backgroundImage);
if (!backBg.includes('rgb(25, 55, 93)') || !backBg.includes('rgb(36, 77, 128)')) throw new Error(`Unexpected card back: ${backBg}`);

const firstCard = page.locator('#bottomHand .card').first();
const before = await firstCard.boundingBox();
await firstCard.evaluate(el => el.click());
await page.waitForTimeout(100);
const selected = page.locator('#bottomHand .card.selected').first();
const after = await selected.boundingBox();
if (!before || !after) throw new Error('Could not measure selected card.');
const selectionShift = { x: after.x - before.x, y: after.y - before.y };
if (Math.abs(selectionShift.y) > 0.75 || Math.abs(selectionShift.x) > 0.75) throw new Error(`Selecting a card moved it: ${JSON.stringify(selectionShift)}`);

await page.screenshot({ path: 'qa/desktop-game.png', fullPage: false });

await page.locator('#devUiToggle').click();
const panel = page.locator('#devUiPanel');
if (!(await panel.isVisible())) throw new Error('Developer UI panel did not open.');
const controlRows = await panel.locator('.dev-ui-row').count();
if (controlRows < 15) throw new Error(`Developer panel has too few controls: ${controlRows}`);
const boardXRange = panel.locator('.dev-ui-row').filter({ hasText: 'Board X' }).locator('input[type="range"]');
await boardXRange.evaluate(el => { el.value = '25'; el.dispatchEvent(new Event('input', { bubbles: true })); });
await page.waitForTimeout(50);
const devState = await page.evaluate(() => ({
  boardX: JSON.parse(localStorage.getItem('cribbage.devUI.v1') || '{}').boardX,
  cssBoardX: getComputedStyle(document.documentElement).getPropertyValue('--dev-board-x').trim(),
}));
if (devState.boardX !== 25 || devState.cssBoardX !== '25px') throw new Error(`Dev tuning did not apply/persist: ${JSON.stringify(devState)}`);
await page.screenshot({ path: 'qa/desktop-dev.png', fullPage: false });
await page.locator('#devUiReset').click();
await page.locator('#devUiClose').click();

await page.setViewportSize({ width: 1366, height: 768 });
await page.waitForTimeout(100);
const desktopOverflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
if (desktopOverflow > 2) throw new Error(`1366px viewport has horizontal overflow: ${desktopOverflow}px`);
await page.screenshot({ path: 'qa/desktop-1366.png', fullPage: false });

const mobile = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
const mobileErrors = [];
mobile.on('pageerror', err => mobileErrors.push(err.message));
mobile.on('console', msg => { if (msg.type() === 'error') mobileErrors.push(msg.text()); });
await mobile.goto('http://127.0.0.1:4173/index.html', { waitUntil: 'networkidle' });
const mobileOverflow = await mobile.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
if (mobileOverflow > 2) throw new Error(`Mobile viewport has horizontal overflow: ${mobileOverflow}px`);
if (!(await mobile.locator('#mainMenu').isVisible())) throw new Error('Mobile main menu did not render.');
await mobile.screenshot({ path: 'qa/mobile-390.png', fullPage: false });
await mobile.close();

if (errors.length || mobileErrors.length) throw new Error(`Browser errors: ${JSON.stringify({ errors, mobileErrors })}`);

console.log('VISUAL_QA_SUMMARY=' + JSON.stringify({
  title,
  url: page.url(),
  viewport: { width: 1366, height: 768 },
  initialDesktop: { width: 1920, height: 1080 },
  boardBox,
  feltBox,
  trackCount: 2,
  holeCount: 244,
  selectionShift,
  cardBack: backBg,
  devControls: controlRows,
  devState,
  desktopOverflow,
  mobileOverflow,
  warnings,
}));

await browser.close();
