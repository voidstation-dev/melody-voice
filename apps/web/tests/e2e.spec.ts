import { test, expect } from '@playwright/test'

test('should render homepage and allow text entry', async ({ page }) => {
  await page.goto('http://localhost:3000')
  await expect(page.locator('h1')).toContainText('Text to Speech Studio')
  const textarea = page.locator('textarea')
  await textarea.fill('Xin chào CapVoice Studio')
  await expect(textarea).toHaveValue('Xin chào CapVoice Studio')
})
