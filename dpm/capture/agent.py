import os
import hashlib
import random
import string
import asyncio
import re
from typing import Literal
from playwright.async_api import async_playwright, Page
from playwright_stealth import Stealth 
from google import genai
from google.genai import types
from dpm.capture.driver import (LOCALE, TIMEZONE, USER_AGENT, VIEWPORT,
                                _normalise)
from dpm.capture.path import FIRST_CONTACT, supersedes
from dpm.capture.schemas import UnifiedDecision
from dpm.signals import collect
from PIL import Image

from dpm.capture.prompts import system_prompt



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
                    text: el.innerText ? el.innerText.substring(0, 50).replace(/\n/g, ' ') : '',
                    // null, not false, when the element is not a selection
                    // control: "not a checkbox" and "a checkbox that is off"
                    // are different answers, and preselected_paid_addon_count
                    // counts the second kind.
                    checked: (el.type === 'checkbox' || el.type === 'radio')
                             ? el.checked : null
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
    # Was 70. On mediamarkt.de that meant 17 steps in twenty minutes and
    # no end in sight: one model call and one interaction per step, against
    # a free tier that allows 10-15 calls a minute. A capture nobody can
    # sit through is not a demo, twenty targets are impossible, and the
    # retrieval we have to defend in the Q&A stops looking polite.
    #
    # Twelve reaches the basket on every site tried so far; the driver
    # works with six. Raise it per run if a funnel is genuinely deeper.
    max_steps = int(os.environ.get("DPM_MAX_STEPS", "12"))

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        # The same configuration driver.py uses, imported rather than
        # repeated. locale was en-US, so amazon.de served the English shop
        # and the German keyword rules read "Proceed to Checkout" as an
        # inadmissible order-button label -- a false accusation produced by
        # our own browser setting (see docs/ARBEITSTEILUNG_Technik.md 7).
        context = await browser.new_context(
            viewport=dict(VIEWPORT),
            user_agent=USER_AGENT,
            locale=LOCALE,
            timezone_id=TIMEZONE,
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

            # Evidence first, while the page is untouched by us. The
            # Beweisakte cites S-xx.png as proof that the site looked like
            # this, and hashes it as proof of the page state -- so neither
            # may contain our own numbered boxes. The marked-up image goes
            # to the model only, into nav/, which the report never cites.
            #
            # The markers of the PREVIOUS step have to go first: a click
            # that does not replace the document leaves them standing, and
            # they were still in S-02.png of the amazon.de run on 24.08.
            # inject_som_markers() clears them too, but that runs after
            # this shot -- too late for the exhibit.
            await current_page.evaluate(
                "document.querySelectorAll('.som-marker').forEach(e => e.remove());")
            screenshot_name = f"S-{step+1:02d}.png"
            screenshot_path = os.path.join(output_dir, screenshot_name)
            await current_page.screenshot(path=screenshot_path)
            # Same normalisation as driver.py, so the two capture paths
            # produce comparable hashes: nonces, inline scripts and
            # comments are stripped first. On a page that rotates its own
            # content (amazon.de) even that is not enough and the hash
            # will differ between two loads -- it is then a fingerprint of
            # this capture, not a change detector.
            dom_hash = "sha256:" + hashlib.sha256(
                _normalise(await current_page.content()).encode("utf-8")).hexdigest()

            element_map = await inject_som_markers(current_page)
            print(f"[*] Injected {len(element_map)} markers.")

            # If no elements found, wait a bit more and retry once
            if not element_map:
                print("[*] No elements found, retrying markers...")
                await current_page.wait_for_timeout(3000)
                element_map = await inject_som_markers(current_page)
                print(f"[*] Retried injection: {len(element_map)} markers.")

            nav_dir = os.path.join(output_dir, "nav")
            os.makedirs(nav_dir, exist_ok=True)
            marked_path = os.path.join(nav_dir, screenshot_name)
            await current_page.screenshot(path=marked_path)
            image = Image.open(marked_path)

            # Unified request: Audit + Decision using manual contents list
            # The current turn includes [Pruned History] + [New Screenshot + Prompt]
            current_prompt = f"Step: {step+1}. URL: {current_page.url}.\n\nExtract signals and decide next action. Use placeholders for values."
            contents = lean_history + [
                types.Content(role="user", parts=[
                    types.Part(inline_data=types.Blob(mime_type="image/png", data=open(marked_path, "rb").read())),
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
            
            # Resolution Logic: fill placeholders from the local element_map.
            #
            # A placeholder that cannot be resolved must never survive as a
            # value. "FETCH:105:checked" was shipped verbatim into signals
            # on 24.08. -- 'checked' was not among the four attributes below
            # and the bare `except: pass` swallowed it. The engine caught it
            # ("value is not a number, but the rule compares it with '>'"),
            # but that is luck: a placeholder in a text signal would have
            # gone into the Beweisakte as a measured string.
            unresolved = []
            for entry in decision.signals:
                val = str(entry.signal.value)
                if not val.startswith("FETCH:"):
                    continue
                parts = val.split(":")
                if len(parts) != 3:
                    unresolved.append((entry, f"Platzhalter {val} ist unlesbar"))
                    continue
                _, eid, attr = parts
                data = element_map.get(eid)
                if data is None:
                    unresolved.append(
                        (entry, f"Element {eid} war beim Messen nicht mehr da"))
                    continue
                try:
                    if attr == "text":
                        entry.signal.value = data["text"]
                    elif attr == "area":
                        entry.signal.value = int(data["area"])
                    elif attr == "font":
                        entry.signal.value = float(data["fontSize"])
                    elif attr == "contrast":
                        entry.signal.value = float(data["contrast"])
                    elif attr == "checked":
                        if data.get("checked") is None:
                            raise ValueError("kein Auswahlfeld")
                        entry.signal.value = bool(data["checked"])
                    else:
                        unresolved.append(
                            (entry, f"Attribut '{attr}' wird nicht gemessen"))
                except (KeyError, TypeError, ValueError) as error:
                    unresolved.append(
                        (entry, f"{attr} an Element {eid} nicht lesbar ({error})"))

            # Out of signals, into signal_errors: not measured is not a value.
            for entry, reason in unresolved:
                all_errors.setdefault(entry.name, reason)
                decision.signals = [e for e in decision.signals if e is not entry]
                print(f"[!] {entry.name}: {reason}")
            
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

            # Deterministic pass: extractors.js measures the same page from
            # the DOM. Where both produced a signal, the measured value wins
            # over the model's reading — it is the number a lawyer can
            # recompute in the developer tools. Gaps never overwrite values.
            first_contact_done = any(n in all_signals for n in FIRST_CONTACT)
            try:
                dom_values, dom_gaps = await collect.measure(current_page)
                for name, value in dom_values.items():
                    # path.supersedes decides, not the loop order. The
                    # consent banner is answered at first contact and gone
                    # afterwards, so measuring it again on a later page
                    # says nothing about the site -- and this merge, which
                    # assigned unconditionally, overwrote banner_detected
                    # with the false read off Amazon's sign-in wall on
                    # 24.08. DP-001 lost its applicability that way.
                    held = all_signals.get(name)
                    if held and not supersedes(name, decision.step_name,
                                               held.get("step", "")):
                        continue
                    all_signals[name] = {"value": value,
                                         "step": decision.step_name,
                                         "evidence": screenshot_name}
                    all_errors.pop(name, None)
                for name, reason in dom_gaps.items():
                    if name == "__extractors__" or name in all_signals:
                        continue
                    # supersedes() protects a first-contact VALUE from a
                    # later step. A gap needs the same protection: on
                    # thalia.de the banner was answered at step 1, and the
                    # DOM of step 3 then reported "kein Einwilligungsbanner
                    # gefunden" as the reason reject_button_area_px2 was
                    # missing -- about a banner that had been there.
                    if name in FIRST_CONTACT and first_contact_done:
                        all_errors.setdefault(
                            name, "am Erstkontakt nicht messbar")
                        continue
                    all_errors[name] = reason
            except Exception as error:
                print(f"[!] DOM measurement failed: {error}")
            
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
                        # The walk stops at a login wall, it does not step
                        # over it. We tell the consumer agency we use public
                        # pages only, no login, no bypassing of access
                        # controls, and we will be asked about it in the Q&A
                        # (docs/ARBEITSTEILUNG_Technik.md 7). The prompt says
                        # so too, but a prompt is a request and this is the
                        # guarantee: no credential can leave this loop.
                        if "SESSION_EMAIL" in text or "FETCH_OTP" in text:
                            print("[!] Login or registration requested — "
                                  "stopping. Public pages only.")
                            decision.is_blocked = True
                            all_errors.setdefault(
                                "checkout_erreichbar",
                                "Der Bestellabschluss war ohne Anmeldung nicht "
                                "erreichbar. Der Lauf endet hier: es werden "
                                "keine Konten angelegt und keine "
                                "Zugangskontrollen umgangen.")
                            break
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
        final_hash = "sha256:" + hashlib.sha256(
            _normalise(final_content).encode("utf-8")).hexdigest()

        steps_log.append({
            "step": final_step_name,
            "url": current_page.url,
            "screenshot": "final_audit.png",
            "dom_hash": final_hash
        })

        await browser.close()
        
    return steps_log, reject_click_depth, final_step_name, (decision.is_blocked if decision else False), all_signals, all_errors
