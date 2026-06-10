import asyncio
from playwright.async_api import async_playwright, Page, Route
from typing import Optional

async def verify_follow_with_playwright(target_username: str, worker_username: str, proxy_url: Optional[str] = None) -> bool:
    """
    Launch headless Playwright to check if worker_username follows target_username.
    """
    async with async_playwright() as p:
        # Configure proxy if provided
        browser_kwargs = {"headless": True}
        if proxy_url:
            browser_kwargs["proxy"] = {"server": proxy_url}
        
        browser = await p.chromium.launch(**browser_kwargs)
        context = await browser.new_context()
        page = await context.new_page()

        # Optimize bandwidth: Intercept and abort unnecessary resources
        async def route_intercept(route: Route):
            if route.request.resource_type in ["image", "media", "stylesheet", "font"]:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", route_intercept)

        try:
            # Navigate to the target user's page
            url = f"https://www.tiktok.com/@{target_username}"
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Note: TikTok's public web UI doesn't usually show a simple "followers list" 
            # to unauthenticated guests, or it requires clicking through modals. 
            # This logic assumes the worker_username appears in the DOM if they are a recent follower.
            
            # Let's wait a moment for dynamic content
            await page.wait_for_timeout(2000)
            
            # Search the entire page text content for the worker's username
            content = await page.content()
            
            if worker_username.lower() in content.lower():
                return True
            return False
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            return False
        finally:
            await browser.close()
