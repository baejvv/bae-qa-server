// Playwright 내장 chromium 사용
const { chromium } = require('playwright');
const path = require('path');
const url = process.env.url;

(async () => {
    const browser = await chromium.launch();
    const context = await browser.newContext();
    const page = await context.newPage();
    const screenshotPath = path.join(__dirname, 'test_screenshots');

    try {
        console.log('*** 헬스체크 e2e 테스트 시작');
        await page.goto(url);
        // Start RTC Test
        try {
            console.log('Start RTC Test...');
            // await page.click('button:has-text("Start RTC Test")');
            await page.click('button:has-text("Start RTC Test")');
            await page.waitForSelector('text=RTC Test Success', { timeout: 5000 });
            console.log('RTC Test completed successfully.');
        } catch (error) {
            console.error('RTC Test failed:', error);
        }
        // Start RTM Test
        try {
            console.log('Start RTM Test...');
            await page.click('button:has-text("Start RTM Test")');
            await page.waitForSelector('text=RTM Test Success', { timeout: 5000 });
            console.log('RTM Test completed successfully.');
            console.log('*** 헬스체크 e2e 테스트 성공.');
        } catch (error) {
            console.error('RTM Test failed:', error);
        }

    } catch (error) {
        console.error('Test setup failed:', error);
    } finally {
        await page.screenshot({ path: path.join(screenshotPath, 'screenshot.png') });
        await browser.close();
    }
})();
