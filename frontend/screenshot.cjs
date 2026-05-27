/* eslint-disable */
const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  if (!fs.existsSync('test-results')) {
    fs.mkdirSync('test-results');
  }
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 1024 } });
  
  const routes = ['/', '/mail', '/calendar', '/tasks', '/projects', '/search', '/data', '/ai-hub', '/security', '/settings'];
  
  for (const route of routes) {
    const url = `http://localhost:3000${route}`;
    console.log(`Taking screenshot for ${url}...`);
    try {
      await page.goto(url, { waitUntil: 'load', timeout: 30000 });
      await page.waitForTimeout(2000);
      const name = route === '/' ? 'home' : route.slice(1);
      await page.screenshot({ path: `test-results/${name}-screenshot.png`, fullPage: true });
      console.log(`Saved test-results/${name}-screenshot.png`);
    } catch (e) {
      console.error(`Failed to capture ${route}:`, e);
    }
  }

  await browser.close();
  console.log('All screenshots completed.');
})();
