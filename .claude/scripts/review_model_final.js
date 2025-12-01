const { chromium } = require('playwright');

/**
 * Review a CAD-AI model with proper error detection and fast failure reporting
 */

(async () => {
  const model = process.argv[2] || 'keyboard';
  const version = process.argv[3] || '2.0.148';

  console.log(`\n=== Reviewing ${model} v${version} ===\n`);

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  // Listen for console messages and errors
  page.on('console', msg => {
    if (msg.type() === 'error' || msg.text().includes('error')) {
      console.log('PAGE ERROR LOG:', msg.text());
    }
  });
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));

  try {
    // Login
    console.log('Logging in...');
    await page.goto('https://d261sntojya397.cloudfront.net/login');
    await page.waitForTimeout(2000);

    await page.waitForSelector('input[type="email"]', { state: 'visible' });
    await page.fill('input[type="email"]', 'reindervandervoort@gmail.com');
    await page.fill('input[type="password"]', 'CadAi2025!');

    await Promise.all([
      page.waitForNavigation({ timeout: 10000 }).catch(() => console.log('No navigation after login')),
      page.click('button:has-text("Sign In")')
    ]);

    console.log('Logged in, current URL:', page.url());
    await page.waitForTimeout(2000);

    // Navigate to model viewer
    console.log(`\nLoading ${model} v${version}...`);
    await page.goto(`https://d261sntojya397.cloudfront.net/viewer?model=${model}&version=${version}`);

    // Wait for initial DOM load
    await page.waitForTimeout(5000);

    // FAST ERROR DETECTION - Check for error states immediately
    console.log('Checking for errors...');
    const errorCheck = await page.evaluate(() => {
      // Check for error messages in DOM
      const bodyText = document.body.innerText;

      // Common error patterns
      const errorPatterns = [
        'Error Loading Status',
        'Failed to fetch',
        'Unauthorized',
        '403',
        '404',
        'Not Found',
        'Model not found',
        'Invalid model',
        'Generation failed'
      ];

      for (const pattern of errorPatterns) {
        if (bodyText.includes(pattern)) {
          return {
            hasError: true,
            errorType: pattern,
            fullText: bodyText.substring(0, 500) // First 500 chars for context
          };
        }
      }

      // Check if there's a loading indicator
      const allDivs = Array.from(document.querySelectorAll('div'));
      const loadingElement = allDivs.find(div => div.textContent.includes('Loading Model'));
      const hasLoadingIndicator = loadingElement !== undefined && loadingElement.offsetParent !== null;

      return {
        hasError: false,
        hasLoadingIndicator,
        bodyPreview: bodyText.substring(0, 200)
      };
    });

    if (errorCheck.hasError) {
      console.log('\n❌ ERROR DETECTED');
      console.log(`Error type: ${errorCheck.errorType}`);
      console.log(`\nPage content:\n${errorCheck.fullText}`);

      // Take error screenshot
      const errorScreenshot = `/tmp/model_${model}_${version.replace(/\./g, '_')}_ERROR.png`;
      await page.screenshot({ path: errorScreenshot, fullPage: true });
      console.log(`\nError screenshot saved: ${errorScreenshot}`);

      await browser.close();
      process.exit(1);
    }

    console.log('No errors detected, checking model load status...');
    console.log(`Loading indicator present: ${errorCheck.hasLoadingIndicator}`);

    // Wait for model to load (with reasonable timeout)
    console.log('Waiting for model to load...');
    let loadingComplete = false;
    let attempts = 0;
    const maxAttempts = 15; // 30 seconds max

    while (!loadingComplete && attempts < maxAttempts) {
      const status = await page.evaluate(() => {
        // Check loading indicator
        const allDivs = Array.from(document.querySelectorAll('div'));
        const loadingElement = allDivs.find(div => div.textContent.includes('Loading Model'));
        const isLoading = loadingElement !== undefined && loadingElement.offsetParent !== null;

        // Check for canvas (indicates viewer is ready)
        const hasCanvas = document.querySelector('canvas') !== null;

        // Check window.scene if available (not critical)
        const hasScene = typeof window.scene !== 'undefined' && window.scene !== null;

        return { isLoading, hasCanvas, hasScene };
      });

      if (!status.isLoading && status.hasCanvas) {
        loadingComplete = true;
        console.log(`✓ Model loaded! (${attempts * 2}s elapsed)`);
      } else {
        console.log(`  Loading... (${attempts * 2}s, canvas=${status.hasCanvas}, loading=${status.isLoading})`);
      }

      if (!loadingComplete) {
        await page.waitForTimeout(2000);
        attempts++;
      }
    }

    if (!loadingComplete) {
      console.log('\n⚠️  WARNING: Model may not be fully loaded after 30 seconds');
      console.log('Taking screenshots anyway...');
    }

    // Extra wait for rendering
    await page.waitForTimeout(2000);

    // Get scene info if available (optional, not critical)
    console.log('\n=== Scene Analysis ===');
    const sceneInfo = await page.evaluate(() => {
      if (!window.scene) return { error: 'No scene available (viewer may use different architecture)' };

      return {
        childrenCount: window.scene.children.length,
        hasObjects: window.scene.children.length > 0
      };
    });
    console.log(JSON.stringify(sceneInfo, null, 2));

    // Take screenshots
    console.log('\n=== Taking Screenshots ===');

    const angles = [
      { name: 'default', description: 'Default view' },
      { name: 'top', position: { x: 0, y: 200, z: 0 }, description: 'Top view' },
      { name: 'side-right', position: { x: 200, y: 0, z: 0 }, description: 'Side view (right)' },
      { name: 'side-left', position: { x: -200, y: 0, z: 0 }, description: 'Side view (left)' },
      { name: 'front', position: { x: 0, y: 0, z: 200 }, description: 'Front view' },
      { name: 'isometric', position: { x: 150, y: 150, z: 150 }, description: 'Isometric view' }
    ];

    for (const angle of angles) {
      console.log(`  ${angle.description}...`);

      if (angle.position) {
        await page.evaluate((pos) => {
          if (window.camera && window.controls) {
            window.camera.position.set(pos.x, pos.y, pos.z);
            window.controls.target.set(0, 0, 0);
            window.controls.update();
          }
        }, angle.position);
        await page.waitForTimeout(500);
      }

      const screenshotPath = `/tmp/model_${model}_${version.replace(/\./g, '_')}_${angle.name}.png`;
      await page.screenshot({ path: screenshotPath, fullPage: false });
      console.log(`    → ${screenshotPath}`);
    }

    console.log('\n✓ Review Complete\n');
    await browser.close();
    process.exit(0);

  } catch (error) {
    console.error('\n❌ SCRIPT ERROR:', error.message);
    console.error(error.stack);

    // Try to take error screenshot
    try {
      const errorScreenshot = `/tmp/model_${model}_${version.replace(/\./g, '_')}_CRASH.png`;
      await page.screenshot({ path: errorScreenshot, fullPage: true });
      console.log(`Error screenshot: ${errorScreenshot}`);
    } catch (e) {
      console.log('Could not capture error screenshot');
    }

    await browser.close();
    process.exit(1);
  }
})();
