const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

async function testMobileUI() {
  console.log('📱 Testing Mobile UI...');
  
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const page = await browser.newPage();
    
    // Test mobile viewport (iPhone 12 Pro)
    await page.setViewport({ width: 390, height: 844 });
    
    // Navigate to page
    await page.goto('http://localhost:3000', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });
    
    // Wait for page to stabilize
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Take mobile screenshot
    const screenshotDir = path.join(__dirname, 'test-screenshots');
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    await page.screenshot({
      path: path.join(screenshotDir, `mobile-${timestamp}.png`),
      fullPage: true
    });
    
    // Test tablet viewport (iPad)
    await page.setViewport({ width: 820, height: 1180 });
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    await page.screenshot({
      path: path.join(screenshotDir, `tablet-${timestamp}.png`),
      fullPage: true
    });
    
    console.log('✅ Mobile/Tablet screenshots saved');
    
    // Test interactions
    const clickableElements = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      return buttons.map(btn => btn.innerText);
    });
    
    console.log('🔘 Found buttons:', clickableElements);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await browser.close();
  }
}

testMobileUI().catch(console.error);