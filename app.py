import asyncio
from playwright.async_api import async_playwright
import random
import json

TEST_URL = "http://localhost:3000"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
]

TIMEZONES = ["America/New_York", "America/Fortaleza", "America/Sao_Paulo", "BET", "America/Noronha"]
LANGUAGES = ["en-US", "pt-BR"]

REVERSE_PROXY = "http://127.0.0.1:8080"

fingerprint_data = []

def store_fingerprint_data(data):
    with open("fingerprint_data.json", "w") as f:
        json.dump(data, f, indent=2)

async def test_fingerprint(url):
    async with async_playwright() as p:
        for i in range(10):  

            user_agent = USER_AGENTS[i % len(USER_AGENTS)]
            print(f"Testing request {i+1} with User-Agent: {user_agent}")
            
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=user_agent,
                viewport={"width": random.randint(800, 1920), "height": random.randint(600, 1080)},
                timezone_id=random.choice(TIMEZONES),
                locale=random.choice(LANGUAGES),
            )

            page = await context.new_page()

            await page.goto(url)
            await page.wait_for_function(
                "document.querySelector('#visitorData') && document.querySelector('#visitorData').innerText.trim().length > 0",
                timeout=10000
            )

            visitor_data_json = await page.locator("#visitorData").inner_text()

            print(f"visitor data {visitor_data_json}")
            
            try:
                visitor_data = json.loads(visitor_data_json)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON data: {e}")
                continue  

            visitor_id = visitor_data.get("visitorId", None)
            if not visitor_id:
                print("Visitor ID not found in data.")
                continue

            print(f"Visitor ID: {visitor_id}")

            fingerprint = None
            for f in fingerprint_data:
                if f["fingerprint"] == visitor_id:
                    fingerprint = f
                    break

            if fingerprint:
                # If fingerprint exists, append the visitor_data
                fingerprint["visitorData"].append(visitor_data)
            else:
                # If fingerprint doesn't exist, create a new entry and add it to fingerprint_data
                fingerprint_data.append({
                    "fingerprint": visitor_id,
                    "visitorData": [visitor_data]  # Wrap the first data in a list
                })
            await browser.close()

        store_fingerprint_data(fingerprint_data)

asyncio.run(test_fingerprint(TEST_URL))
