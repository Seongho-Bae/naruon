/* eslint-disable */
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 1024 } });
  
  await page.goto('http://localhost:18080/settings');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'test-results/settings-screenshot.png', fullPage: true });
  await browser.close();
  console.log('Screenshot saved to test-results/settings-screenshot.png');
})();
