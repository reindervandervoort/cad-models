const { chromium } = require('playwright');

/**
 * View a CAD-AI model with authentication
 * Usage: node view_model.js <model> <version>
 * Example: node view_model.js keyboard 1.1.125
 */

(async () => {
  const model = process.argv[2] || 'keyboard';
  const version = process.argv[3] || '1.1.125';

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Login with stored credentials
  console.log('Logging in...');

  // Listen for console messages and errors
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));

  await page.goto('https://d261sntojya397.cloudfront.net/login');
  await page.waitForLoadState('networkidle');

  // Wait for form to be visible
  await page.waitForSelector('input[type="email"]', { state: 'visible' });

  await page.fill('input[type="email"]', 'reindervandervoort@gmail.com');
  await page.fill('input[type="password"]', 'CadAi2025!');

  // Click and wait for navigation
  await Promise.all([
    page.waitForNavigation({ timeout: 10000 }).catch(() => console.log('No navigation after login')),
    page.click('button:has-text("Sign In")')
  ]);

  console.log('After login attempt, current URL:', page.url());
  await page.waitForTimeout(3000);

  // Navigate to model
  console.log(`Loading ${model} v${version}...`);
  await page.goto(`https://d261sntojya397.cloudfront.net/viewer?model=${model}&version=${version}`);
  await page.waitForLoadState('networkidle');

  // Wait for model to render
  console.log('Waiting for 3D model to render...');
  await page.waitForTimeout(10000);

  // Screenshot
  const screenshotPath = `/tmp/model_${model}_${version.replace(/\./g, '_')}.png`;
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`Screenshot saved: ${screenshotPath}`);

  // Get scene info
  const sceneInfo = await page.evaluate(() => {
    if (!window.scene) return { error: 'No scene available' };

    return {
      childrenCount: window.scene.children.length,
      children: window.scene.children.map((c, i) => ({
        index: i,
        type: c.type,
        name: c.name || 'unnamed',
        visible: c.visible,
        position: c.position ? {
          x: Math.round(c.position.x * 10) / 10,
          y: Math.round(c.position.y * 10) / 10,
          z: Math.round(c.position.z * 10) / 10
        } : null,
        childrenCount: c.children ? c.children.length : 0
      }))
    };
  });

  console.log('\n=== Scene Info ===');
  console.log(JSON.stringify(sceneInfo, null, 2));

  await browser.close();
})();
