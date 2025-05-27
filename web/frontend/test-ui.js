const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

async function testUI() {
  console.log('🚀 Starting UI test with Puppeteer...');
  
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const page = await browser.newPage();
    
    // Set viewport for desktop testing
    await page.setViewport({ width: 1920, height: 1080 });
    
    // Collect console messages
    const consoleMessages = [];
    page.on('console', msg => {
      consoleMessages.push({
        type: msg.type(),
        text: msg.text(),
        location: msg.location()
      });
    });
    
    // Collect page errors
    const pageErrors = [];
    page.on('pageerror', error => {
      pageErrors.push({
        message: error.message,
        stack: error.stack
      });
    });
    
    // Collect failed requests
    const failedRequests = [];
    page.on('requestfailed', request => {
      failedRequests.push({
        url: request.url(),
        failure: request.failure()
      });
    });
    
    console.log('📱 Navigating to http://localhost:3000...');
    const response = await page.goto('http://localhost:3000', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });
    
    console.log(`📊 Response status: ${response.status()}`);
    
    // Wait a bit for any async rendering
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Take screenshot
    const screenshotDir = path.join(__dirname, 'test-screenshots');
    await fs.mkdir(screenshotDir, { recursive: true });
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    await page.screenshot({
      path: path.join(screenshotDir, `page-${timestamp}.png`),
      fullPage: true
    });
    console.log('📸 Screenshot saved');
    
    // Check page content
    const pageContent = await page.content();
    const bodyText = await page.evaluate(() => document.body.innerText);
    
    console.log('\n📋 Page Analysis:');
    console.log(`- Body text length: ${bodyText.length} characters`);
    console.log(`- HTML length: ${pageContent.length} characters`);
    
    // Check for specific elements
    const hasCanvas = await page.evaluate(() => !!document.querySelector('canvas'));
    const hasDashboard = await page.evaluate(() => !!document.querySelector('[class*="dashboard"]'));
    
    console.log(`- Has canvas element: ${hasCanvas}`);
    console.log(`- Has dashboard elements: ${hasDashboard}`);
    
    // Report errors
    if (consoleMessages.length > 0) {
      console.log('\n❌ Console messages:');
      consoleMessages.forEach(msg => {
        if (msg.type === 'error') {
          console.log(`  ERROR: ${msg.text}`);
          if (msg.location.url) {
            console.log(`    at ${msg.location.url}:${msg.location.lineNumber}`);
          }
        }
      });
    }
    
    if (pageErrors.length > 0) {
      console.log('\n❌ Page errors:');
      pageErrors.forEach(error => {
        console.log(`  ${error.message}`);
      });
    }
    
    if (failedRequests.length > 0) {
      console.log('\n❌ Failed requests:');
      failedRequests.forEach(req => {
        console.log(`  ${req.url} - ${req.failure.errorText}`);
      });
    }
    
    // Save detailed report
    const report = {
      timestamp: new Date().toISOString(),
      responseStatus: response.status(),
      bodyTextLength: bodyText.length,
      hasCanvas,
      hasDashboard,
      consoleMessages,
      pageErrors,
      failedRequests,
      bodyPreview: bodyText.substring(0, 500)
    };
    
    await fs.writeFile(
      path.join(screenshotDir, `report-${timestamp}.json`),
      JSON.stringify(report, null, 2)
    );
    
    console.log('\n✅ Test complete. Check test-screenshots directory for results.');
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await browser.close();
  }
}

// Run the test
testUI().catch(console.error);