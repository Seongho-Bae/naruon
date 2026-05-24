const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 1024 } });
  
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));

  await page.route('**/api/**', async (route) => {
    if (route.request().method() === 'OPTIONS') return route.fulfill({ status: 204, headers: {'Access-Control-Allow-Origin': '*'} });
    return route.fulfill({ status: 200, contentType: 'application/json', body: '{"emails": [], "tasks": []}', headers: {'Access-Control-Allow-Origin': '*'} });
  });

  await page.goto('http://localhost:18080/');
  await page.waitForTimeout(2000);
  
  await browser.close();
})();
