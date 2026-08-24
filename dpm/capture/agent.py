import os
import hashlib
import random
import string
import asyncio
import aiohttp
import re
from typing import Literal
from playwright.async_api import async_playwright, Page
from playwright_stealth import Stealth 
from google import genai
from google.genai import types
from schemas import UnifiedDecision
from PIL import Image

from server.cap.prompts import system_prompt


async def get_temp_email() -> str:
    """Generates a random 1secmail address."""
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{username}@1secmail.com"

async def wait_for_email(email_address: str, timeout: int = 60) -> dict:
    """Polls the 1secmail API every 3 seconds until an email arrives."""
    username, domain = email_address.split('@')
    async with aiohttp.ClientSession() as session:
        for _ in range(timeout // 3):
            check_url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={username}&domain={domain}"
            async with session.get(check_url) as resp:
                messages = await resp.json()
                if messages:
                    msg_id = messages[0]['id']
                    read_url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={username}&domain={domain}&id={msg_id}"
                    async with session.get(read_url) as read_resp:
                        return await read_resp.json()
            await asyncio.sleep(3)
    return {"error": "Timeout waiting for email"}

async def inject_som_markers(page: Page):
    """Draws numbered bounding boxes over clickable elements across all frames."""
    # First, inject a style tag to the main page to ensure markers are visible
    await page.add_style_tag(content=".som-marker { pointer-events: none !important; }")
    
    return await page.evaluate(r'''async () => {
        document.querySelectorAll('.som-marker').forEach(e => e.remove());
        
        let map = {};
        let index = 0;

        const processFrame = (doc, frameOffset = { x: 0, y: 0 }) => {
            // Broaden selectors to catch more potential interactive elements
            const selectors = [
                'a', 'button', 'input', 'select', 'textarea', 
                '[role="button"]', '[role="link"]', '[role="checkbox"]', '[role="menuitem"]',
                '[role="slider"]', '[role="tab"]', '[role="treeitem"]',
                '[onclick]', '.btn', '.button', '[class*="button"]',
                '.slider-handle', '.slider-track', '[class*="slider"]',
                'canvas', 'svg' // Often used in bot challenges
            ];
            
            let elements = Array.from(doc.querySelectorAll(selectors.join(',')))
                .filter(el => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return rect.width > 2 && 
                           rect.height > 2 && 
                           style.visibility !== 'hidden' && 
                           style.display !== 'none' &&
                           style.opacity !== '0';
                });
            
            // Fallback: If we have very few elements, look for anything with a pointer cursor
            if (elements.length < 5) {
                const all = Array.from(doc.querySelectorAll('div, span, img, svg, canvas'))
                    .filter(el => {
                        const style = window.getComputedStyle(el);
                        const rect = el.getBoundingClientRect();
                        return (style.cursor === 'pointer' || el.onclick) && rect.width > 2 && rect.height > 2;
                    });
                elements = [...new Set([...elements, ...all])];
            }

            elements.forEach((el) => {
                let rect = el.getBoundingClientRect();
                let marker = document.createElement('div');
                marker.className = 'som-marker';
                
                // Fixed positioning relative to the viewport
                const top = rect.top + frameOffset.y;
                const left = rect.left + frameOffset.x;
                
                marker.style.cssText = `position:fixed; top:${top}px; left:${left}px; width:${rect.width}px; height:${rect.height}px; border: 2px solid red; z-index: 2147483647; pointer-events:none;`;
                
                let label = document.createElement('span');
                label.textContent = index;
                label.style.cssText = 'background:red; color:white; font-size:12px; font-weight:bold; position:absolute; top:0; left:0;';
                
                marker.appendChild(label);
                window.top.document.body.appendChild(marker);
                
                // Helper to calculate contrast ratio according to WCAG
                const getLuminance = (r, g, b) => {
                    const a = [r, g, b].map(v => {
                        v /= 255;
                        return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
                    });
                    return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
                };

                const getContrast = (el) => {
                    const style = window.getComputedStyle(el);
                    const rgb = (c) => {
                        const parts = c.match(/\d+(\.\d+)?/g);
                        return parts ? parts.map(Number) : [0,0,0,1];
                    };

                    const getBackdropColor = (target) => {
                        let curr = target;
                        while (curr && curr !== document.documentElement) {
                            const bg = rgb(window.getComputedStyle(curr).backgroundColor);
                            // If alpha is > 0.05, we found our backdrop
                            if (bg.length === 3 || (bg.length === 4 && bg[3] > 0.05)) {
                                return bg;
                            }
                            curr = curr.parentElement;
                        }
                        return [255, 255, 255]; // Default to white
                    };
                    
                    const bg = getBackdropColor(el);
                    const fg = rgb(style.color);
                    
                    const l1 = getLuminance(fg[0], fg[1], fg[2]) + 0.05;
                    const l2 = getLuminance(bg[0], bg[1], bg[2]) + 0.05;
                    
                    return {
                        ratio: Math.max(l1, l2) / Math.min(l1, l2),
                        fontSize: parseFloat(style.fontSize)
                    };
                };

                const details = getContrast(el);
                
                map[index] = {
                    x: left + (rect.width / 2),
                    y: top + (rect.height / 2),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    area: Math.round(rect.width * rect.height),
                    fontSize: details.fontSize,
                    contrast: details.ratio.toFixed(2),
                    text: el.innerText ? el.innerText.substring(0, 50).replace(/\n/g, ' ') : ''
                };
                index++;
            });
        };

        try {
            processFrame(document);
        } catch (e) { console.error(e); }

        // Process all iframes
        let frames = Array.from(document.querySelectorAll('iframe'));
        frames.forEach(frame => {
            try {
                const rect = frame.getBoundingClientRect();
                if (frame.contentDocument) {
                    processFrame(frame.contentDocument, { x: rect.left, y: rect.top });
                }
            } catch (e) {
                // Cross-origin iframe
            }
        });
        
        return map;
    }''')

async def human_click(page: Page, x: float, y: float, button: Literal["left", "right", "middle"] = "left", click_count: int = 1):
    target_x = x + random.randint(-5, 5)
    target_y = y + random.randint(-5, 5)
    await page.mouse.move(target_x, target_y, steps=random.randint(5, 15))
    await page.wait_for_timeout(random.randint(200, 600))
    await page.mouse.click(target_x, target_y, button=button, click_count=click_count)
    await page.wait_for_timeout(random.randint(1000, 2500))

async def human_hover(page: Page, x: float, y: float):
    target_x = x + random.randint(-5, 5)
    target_y = y + random.randint(-5, 5)
    await page.mouse.move(target_x, target_y, steps=random.randint(5, 15))
    await page.wait_for_timeout(random.randint(500, 1000))

async def human_type(page: Page, x: float, y: float, text: str):
    await human_click(page, x, y)
    for char in text:
        # Use .type() instead of .press() to handle Unicode (ü, ö, ä, etc.) gracefully
        await page.keyboard.type(char)
        await page.wait_for_timeout(random.randint(50, 150))
    await page.wait_for_timeout(random.randint(300, 800))

async def human_scroll(page: Page, direction: str):
    distance = random.randint(400, 700)
    if direction == "up":
        distance = -distance
    await page.mouse.wheel(0, distance)
    await page.wait_for_timeout(random.randint(800, 1500))

async def human_drag(page: Page, start_x: float, start_y: float, end_x: float, end_y: float):
    await page.mouse.move(start_x, start_y, steps=random.randint(5, 10))
    await page.mouse.down()
    # Move in a slightly non-linear path to look more human
    steps = random.randint(15, 30)
    for i in range(steps):
        curr_x = start_x + (end_x - start_x) * (i / steps) + random.randint(-2, 2)
        curr_y = start_y + (end_y - start_y) * (i / steps) + random.randint(-2, 2)
        await page.mouse.move(curr_x, curr_y)
        await asyncio.sleep(0.01)
    await page.mouse.move(end_x, end_y, steps=5)
    await page.mouse.up()
    await page.wait_for_timeout(random.randint(1000, 2000))

def denormalize(coords, width, height):
    """Converts 0-1000 normalized coordinates to absolute pixels."""
    return (coords[0] * width / 1000), (coords[1] * height / 1000)

async def visual_explore(url: str, client: genai.Client, output_dir: str):
    """Navigates the site using vision, types fake data, and captures the state."""
    final_path = os.path.join(output_dir, "final_audit.png")
    steps_log = []
    reject_click_depth = 0
    temp_email = None
    max_steps = 70

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="Europe/Berlin"
        )
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        # Track all pages to handle new tabs/windows automatically
        active_pages = [page]
        def handle_new_page(new_page):
            print(f"[*] New tab detected: {new_page.url}")
            active_pages.append(new_page)
        context.on("page", handle_new_page)
        
        await page.goto(url, wait_until="domcontentloaded")

        # Initialize manual history tracking to save tokens
        # We maintain only text context to stay within quota.
        lean_history = []
        
        all_signals = {}
        all_errors = {}
        decision = None
        
        for step in range(max_steps):
            current_page = active_pages[-1]
            try: await current_page.wait_for_load_state("load", timeout=5000)
            except: pass

            if hasattr(current_page, "_stealth_applied") is False:
                await stealth.apply_stealth_async(current_page)
                current_page._stealth_applied = True

            print(f"[*] Step {step} on: {current_page.url}")
            await current_page.wait_for_timeout(2000)
            element_map = await inject_som_markers(current_page)
            print(f"[*] Injected {len(element_map)} markers.")

            # If no elements found, wait a bit more and retry once
            if not element_map:
                print("[*] No elements found, retrying markers...")
                await current_page.wait_for_timeout(3000)
                element_map = await inject_som_markers(current_page)
                print(f"[*] Retried injection: {len(element_map)} markers.")

            screenshot_name = f"S-{step+1:02d}.png"
            screenshot_path = os.path.join(output_dir, screenshot_name)
            await current_page.screenshot(path=screenshot_path)
            
            dom_hash = "sha256:" + hashlib.sha256((await current_page.content()).encode('utf-8')).hexdigest()
            image = Image.open(screenshot_path)

            # Unified request: Audit + Decision using manual contents list
            # The current turn includes [Pruned History] + [New Screenshot + Prompt]
            current_prompt = f"Step: {step+1}. URL: {current_page.url}.\n\nExtract signals and decide next action. Use placeholders for values."
            contents = lean_history + [
                types.Content(role="user", parts=[
                    types.Part(inline_data=types.Blob(mime_type="image/png", data=open(screenshot_path, "rb").read())),
                    types.Part(text=current_prompt)
                ])
            ]

            max_retries = 5
            response = None
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model="gemma-4-26b-a4b-it",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            response_schema=UnifiedDecision,
                            response_mime_type="application/json",
                            temperature=0.1
                        )
                    )
                    break
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        wait_time = 125
                        print(f"[!] Quota exceeded (429). Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                    else: raise e

            if response.usage_metadata:
                print(f"[*] Tokens: Prompt={response.usage_metadata.prompt_token_count}, Response={response.usage_metadata.candidates_token_count}, Total={response.usage_metadata.total_token_count}")

            decision = UnifiedDecision.model_validate_json(response.text)
            
            # --- CONTEXT MANAGEMENT: Add turn to lean history for next step ---
            # We record only the TEXT of the model's response and a TEXT summary of the user input.
            # This completely discards the heavy image data (screenshots) from previous turns.
            lean_history.append(types.Content(role="user", parts=[types.Part(text=f"Turn {step+1}: screenshot was provided. URL: {current_page.url}")]))
            lean_history.append(types.Content(role="model", parts=[types.Part(text=response.text)]))
            
            # Limit history length to prevent token overflow during long runs
            if len(lean_history) > 40: # 20 full turns (user+model) is plenty for reasoning
                lean_history = lean_history[-40:]
            
            print(f"[*] History size: {len(lean_history)} entries (text-only).")
            
            # Resolution Logic: Fill placeholders from the local element_map
            for entry in decision.signals:
                val = str(entry.signal.value)
                if val.startswith("FETCH:"):
                    try:
                        _, eid, attr = val.split(":")
                        if eid in element_map:
                            data = element_map[eid]
                            if attr == "text": entry.signal.value = data['text']
                            elif attr == "area": entry.signal.value = int(data['area'])
                            elif attr == "font": entry.signal.value = float(data['fontSize'])
                            elif attr == "contrast": entry.signal.value = float(data['contrast'])
                    except: pass
            
            print(f"[*] Agent Thought: {decision.thought_process}")
            
            # Store signals found at this step with 'Sticky Positive' logic
            captured_signals = []
            for entry in decision.signals:
                new_val = entry.signal.value
                existing = all_signals.get(entry.name)

                # Persistence Policy:
                # Once a 'positive' finding is made (True, or a non-zero measurement),
                # don't allow it to be overriden by a 'negative' finding (False/0) in later steps.
                should_update = True
                if existing:
                    old_val = existing.get('value')
                    if isinstance(old_val, bool) and old_val is True and new_val is False:
                        should_update = False
                    elif isinstance(old_val, (int, float)) and old_val > 0 and (new_val == 0 or new_val is False):
                        # Special case: don't overwrite a found price/area with zero
                        should_update = False
                
                if should_update:
                    entry.signal.step = decision.step_name
                    entry.signal.evidence = screenshot_name
                    all_signals[entry.name] = entry.signal.model_dump()
                    captured_signals.append(f"{entry.name}={entry.signal.value}")
                    # Clear from errors if we found a valid value
                    if entry.name in all_errors:
                        del all_errors[entry.name]

            if captured_signals:
                print(f"[*] Signals Captured: {', '.join(captured_signals)}")
            
            for entry in decision.signal_errors:
                # Only record error if we don't have a valid signal captured in a previous step
                if entry.name not in all_signals:
                    all_errors[entry.name] = entry.reason

            # Store decision in journey log
            steps_log.append({
                "step": decision.step_name,
                "url": current_page.url,
                "screenshot": screenshot_name,
                "dom_hash": dom_hash,
                "reasoning": decision.thought_process,
                "action": decision.action_type,
                "input": decision.input_text
            })

            action_info = f"{decision.action_type}"
            if decision.target_id is not None: action_info += f" (ID: {decision.target_id})"
            if decision.target_pixel: action_info += f" (Pixel: {decision.target_pixel})"
            if decision.drag_pixels: action_info += f" (Drag: {decision.drag_pixels})"
            if decision.input_text: action_info += f" (Input: {decision.input_text})"
            print(f"[*] Action Requested: {action_info}")

            if decision.is_blocked:
                print("[!] Bot detection detected. Stopping exploration.")
                break

            if decision.goal_reached:
                print(f"[*] Target goal reached at step {step+1}.")
                break
            
            # Execute Action
            if decision.action_type == "scroll":
                direction = decision.input_text if decision.input_text in ["up", "down"] else "down"
                await human_scroll(current_page, direction)
            elif decision.action_type == "wait":
                ms = int(decision.input_text) if decision.input_text and decision.input_text.isdigit() else 2000
                await current_page.wait_for_timeout(ms)
            elif decision.action_type == "key":
                key = decision.input_text or "Enter"
                await current_page.keyboard.press(key)
                await current_page.wait_for_timeout(random.randint(1000, 2000))
            elif decision.action_type in ["click_pixel", "double_click_pixel", "right_click_pixel", "hover_pixel"] and decision.target_pixel:
                x, y = denormalize(decision.target_pixel, 1440, 900)
                if decision.action_type == "click_pixel": await human_click(current_page, x, y)
                elif decision.action_type == "double_click_pixel": await human_click(current_page, x, y, click_count=2)
                elif decision.action_type == "right_click_pixel": await human_click(current_page, x, y, button="right")
                elif decision.action_type == "hover_pixel": await human_hover(current_page, x, y)
            elif decision.action_type == "drag_pixel" and decision.drag_pixels and len(decision.drag_pixels) == 2:
                start_x, start_y = denormalize(decision.drag_pixels[0], 1440, 900)
                end_x, end_y = denormalize(decision.drag_pixels[1], 1440, 900)
                await human_drag(current_page, start_x, start_y, end_x, end_y)
            elif decision.target_id is not None:
                if str(decision.target_id) in element_map:
                    # Logic for reject click depth: Count clicks until a reject signal is found
                    # or until the banner is definitively gone.
                    is_banner_step = all_signals.get('banner_detected', {}).get('value') is True
                    has_reject_option = any(s.name == "reject_button_present" and s.signal.value is True for s in decision.signals)

                    if is_banner_step or has_reject_option:
                        reject_click_depth += 1
                        print(f"[*] Banner Flow. Reject Click Depth: {reject_click_depth}")

                    coords = element_map[str(decision.target_id)]

                    if decision.action_type == "type" and decision.input_text:
                        text = decision.input_text
                        if "SESSION_EMAIL" in text:
                            if not temp_email:
                                temp_email = await get_temp_email()
                                print(f"[*] Generated session email: {temp_email}")
                            text = text.replace("SESSION_EMAIL", temp_email)
                        if "FETCH_OTP" in text:
                            print("[*] Polling OTP...")
                            if not temp_email:
                                temp_email = await get_temp_email()
                                print(f"[*] Generated session email for OTP: {temp_email}")
                            email_data = await wait_for_email(temp_email)
                            if "error" not in email_data:
                                match = re.search(r'\b\d{4,6}\b', email_data.get('textBody', ''))
                                text = text.replace("FETCH_OTP", match.group(0) if match else "123456")
                            else:
                                text = text.replace("FETCH_OTP", "000000")
                        await human_type(current_page, coords['x'], coords['y'], text)
                    elif decision.action_type == "double_click": await human_click(current_page, coords['x'], coords['y'], click_count=2)
                    elif decision.action_type == "right_click": await human_click(current_page, coords['x'], coords['y'], button="right")
                    elif decision.action_type == "hover": await human_hover(current_page, coords['x'], coords['y'])
                    elif decision.action_type == "drag_and_drop":
                        target_id = decision.input_text
                        if target_id and target_id.isdigit() and target_id in element_map:
                            t_coords = element_map[target_id]
                            await human_drag(current_page, coords['x'], coords['y'], t_coords['x'], t_coords['y'])
                    else: await human_click(current_page, coords['x'], coords['y'])
                else:
                    print(f"[!] Warning: Target ID {decision.target_id} not found in element map. Skipping action.")

        # Final cleanup for the active page
        current_page = active_pages[-1]
        await current_page.evaluate("document.querySelectorAll('.som-marker').forEach(e => e.remove());")

        final_step_name = "checkout" if (decision and decision.goal_reached) else "abandoned"
        await current_page.screenshot(path=final_path, full_page=True)
        final_content = await current_page.content()
        final_hash = "sha256:" + hashlib.sha256(final_content.encode('utf-8')).hexdigest()

        steps_log.append({
            "step": final_step_name,
            "url": current_page.url,
            "screenshot": "final_audit.png",
            "dom_hash": final_hash
        })

        await browser.close()
        
    return steps_log, reject_click_depth, final_step_name, (decision.is_blocked if decision else False), all_signals, all_errors
