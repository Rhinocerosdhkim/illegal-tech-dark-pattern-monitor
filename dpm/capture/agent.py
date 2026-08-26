from __future__ import annotations

import os
import hashlib
import random
import string
import asyncio
import io
import json
import re
from datetime import datetime
from typing import Literal
from pathlib import Path
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright, Page
from playwright_stealth import Stealth 
from google.genai import types
from PIL import Image
from urllib.parse import urljoin

from dpm.capture.prompts import system_prompt
from dpm.capture.schemas import UnifiedDecision
from dpm.capture.network_audit import get_cookie_stats, get_accessibility_audit
from dpm.capture.path import FIRST_CONTACT, PATH_STEPS, ABANDONED, OFF_PATH, supersedes
from dpm.signals import collect

# Fixed in code, not left to defaults. Pixel areas are meaningless without a
# fixed viewport and reproducibility is our whole claim against the ML
# approach. Locale de-DE because the keyword signals are German: an English
# page shows no "inkl. MwSt." and no "nur noch 2 verfuegbar".
VIEWPORT = {"width": 1440, "height": 900}
LOCALE = "de-DE"
TIMEZONE = "Europe/Berlin"
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 "
              "Safari/537.36")


@dataclass
class Capture:
    meta: dict
    path: Path
    steps: list = field(default_factory=list)
    signals: dict = field(default_factory=dict)
    errors: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)

    def as_dict(self) -> dict:
        # "notes" is not part of the schema the engine reads. It is in the
        # file so that "why did this stop at step 2" survives the terminal
        # scrolling away.
        return {"meta": self.meta, "notes": self.notes, "steps": self.steps,
                "signals": self.signals, "signal_errors": self.errors}

    def write(self) -> Path:
        """capture.json next to its screenshots, one folder per run.

        The engine resolves every evidence file relative to this folder, so
        the two must not be separated -- and a second run of the same target
        must not overwrite the first, or the Zeitachse has nothing to
        compare.
        """
        file = self.path / "capture.json"
        file.write_text(json.dumps(self.as_dict(), ensure_ascii=False,
                                   indent=2), encoding="utf-8")
        return file


def _normalise(html: str) -> str:
    """Strip what changes on every request before hashing.

    Without this, nonces, ad ids and inline CSRF tokens make every capture
    of an unchanged page hash differently, and the Zeitachse diff can no
    longer tell "the page changed" from "we loaded it again". Heuristic, and
    deliberately conservative: only script and style bodies, comments and
    nonce attributes go. The visible markup -- what the hash is supposed to
    prove -- stays.
    """
    html = re.sub(r"<script\b[^>]*>.*?</script>", "<script/>", html,
                  flags=re.S | re.I)
    html = re.sub(r"<style\b[^>]*>.*?</style>", "<style/>", html,
                  flags=re.S | re.I)
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    html = re.sub(r'\s(nonce|integrity)="[^"]*"', "", html, flags=re.I)
    return re.sub(r"\s+", " ", html).strip()


# Signals nothing in the capture layer can produce yet, with the reason
# that is true regardless of which page the walk happened to end on. A
# model looking at a broken page writes "Page is blank" into
# signal_errors, and that sentence then explains in the Beweisakte why
# § 25 TDDDG could not be checked. The structural reason has to win.
STRUCTURAL_GAPS = {
    "reject_click_depth":
        "erfordert das Ablaufen des Ablehnwegs — ein Vorgang, keine "
        "Messung; noch nicht umgesetzt",
    "banner_reappears_on_reject":
        "erfordert das Ablaufen des Ablehnwegs — ein Vorgang, keine "
        "Messung; noch nicht umgesetzt",
    "banner_reappears_count_24h":
        "erfordert Erfassungen ueber 24 Stunden; noch nicht umgesetzt",
    "more_info_leads_to_reject":
        "erfordert das Oeffnen von „Mehr Informationen“ — ein Vorgang, "
        "keine Messung; noch nicht umgesetzt",
    "third_party_cookies_before_consent":
        "steht nicht im DOM — erfordert das Auslesen des Cookie-Speichers "
        "vor jeder Interaktion; noch nicht umgesetzt",
    "countdown_unchanged_scans":
        "erfordert eine zweite Erfassung desselben Ziels; noch nicht "
        "umgesetzt",
    "scarcity_value_unchanged_scans":
        "erfordert eine zweite Erfassung desselben Ziels; noch nicht "
        "umgesetzt",
}


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

async def visual_explore(url: str, model, output_root: Path, max_steps: int = None, username: str = None, password: str = None):
    """Navigates the site using vision, types fake data, and captures the state."""
    from dpm.capture.targets import slug
    from zoneinfo import ZoneInfo

    # Handle local file paths
    if url.startswith("/") or url.startswith("./"):
        url = urljoin("file:", os.path.abspath(url))
        
    # Setup output directory structure: out/<run_id>/
    now = datetime.now(ZoneInfo(TIMEZONE)).replace(microsecond=0)
    target = slug(url)
    run_id = f"{now.strftime('%Y-%m-%dT%H-%M-%S')}_{target}"
    output = Path(output_root) / run_id
    output.mkdir(parents=True, exist_ok=True)
    
    # Prepare metadata for capture.json
    meta = {
        "target": target,
        "industry": "unbekannt",
        "start_url": url,
        "timestamp": now.isoformat(),
        "capture_mode": "headless",
        "viewport": dict(VIEWPORT),
        "locale": LOCALE,
        "timezone": TIMEZONE,
        "user_agent": USER_AGENT,
        "run_id": run_id,
    }

    final_path = str(output / "final_audit.png")
    steps_log = []
    reject_click_depth = 0
    if max_steps is None:
        max_steps = int(os.environ.get("DPM_MAX_STEPS", "12"))
    lean_history = []
    all_signals = {}
    all_errors = {}
    decision = None
    final_step_name = "started"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                viewport=dict(VIEWPORT),
                user_agent=USER_AGENT,
                locale=LOCALE,
                timezone_id=TIMEZONE
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

            for step in range(max_steps):
                current_page = active_pages[-1]
                try: await current_page.wait_for_load_state("load", timeout=5000)
                except: pass

                if hasattr(current_page, "_stealth_applied") is False:
                    await stealth.apply_stealth_async(current_page)
                    current_page._stealth_applied = True

                print(f"[*] Step {step} on: {current_page.url}")
                await current_page.wait_for_timeout(2000)

                # Clear previous markers and capture evidence
                await current_page.evaluate(
                    "document.querySelectorAll('.som-marker').forEach(e => e.remove());")
                screenshot_name = f"S-{step+1:02d}.png"
                screenshot_path = str(output / screenshot_name)
                await current_page.screenshot(path=screenshot_path)
                dom_hash = "sha256:" + hashlib.sha256(
                    _normalise(await current_page.content()).encode("utf-8")).hexdigest()

                # First iteration is startseite by construction
                step_name = PATH_STEPS[0] if step == 0 else ABANDONED

                if model is None:
                    # Fallback: without a model, we only capture the start page signals from DOM
                    wall = await collect.blocked(current_page)
                    if wall:
                        steps_log.append({
                            "step": OFF_PATH, "url": current_page.url,
                            "screenshot": screenshot_name, "dom_hash": dom_hash,
                            "blocked": wall
                        })
                        break
                    
                    try:
                        dom_values, dom_gaps = await collect.measure(current_page)
                        for name, value in dom_values.items():
                            all_signals[name] = {"value": value, "step": step_name, "evidence": screenshot_name}
                        for name, reason in dom_gaps.items():
                            all_errors[name] = reason
                    except Exception as error:
                        print(f"[!] DOM measurement failed: {error}")

                    steps_log.append({
                        "step": step_name, "url": current_page.url,
                        "screenshot": screenshot_name, "dom_hash": dom_hash
                    })
                    break

                element_map = await inject_som_markers(current_page)

                # --- Automated Technical Audit (Direct Injection) ---
                # These signals are extracted via Playwright/JS and injected directly
                # into all_signals without requiring AI placeholders.

                # 1. Accessibility & Information Obscurity
                acc_data = await get_accessibility_audit(current_page)
                for key, val in acc_data.items():
                    # Sticky Positive: If we find a violation once, keep it
                    if val is True or (isinstance(val, int) and val > 0):
                        all_signals[key] = {
                            "value": val,
                            "step": f"auto_scan_{step}",
                            "evidence": "accessibility_logic"
                        }

                # 2. Third-Party Cookies (Initial State)
                if step == 0:
                    cookie_stats = await get_cookie_stats(context, current_page.url)
                    all_signals["third_party_cookies_before_consent"] = {
                        "value": cookie_stats["third_party_count"],
                        "step": "initial_scan",
                        "evidence": "network_log"
                    }

                print(f"[*] Injected {len(element_map)} markers.")

                # If no elements found, wait a bit more and retry once
                if not element_map:
                    print("[*] No elements found, retrying markers...")
                    await current_page.wait_for_timeout(3000)
                    element_map = await inject_som_markers(current_page)
                    print(f"[*] Retried injection: {len(element_map)} markers.")

                nav_dir = str(output / "nav")
                os.makedirs(nav_dir, exist_ok=True)
                marked_path = os.path.join(nav_dir, screenshot_name)
                await current_page.screenshot(path=marked_path)

                # --- Visual Stagnation Check ---
                stagnation_warning = ""
                if len(steps_log) > 0:
                    last_step = steps_log[-1]
                    if last_step.get("dom_hash") == dom_hash:
                        stagnation_warning = f"\n[!] WARNING: Your previous action did not change the page state. DO NOT REPEAT IT. Try a different strategy (scroll, click other ID, or click_pixel)."

                # Unified request: Audit + Decision using Model.ask
                current_prompt = f"Step: {step+1}. URL: {current_page.url}.{stagnation_warning}\n\nExtract signals and decide next action. Use placeholders for values."
                
                try:
                    response = await model.ask(
                        prompt=current_prompt,
                        schema=UnifiedDecision.model_json_schema(),
                        screenshot=open(marked_path, "rb").read(),
                        history=lean_history,
                        system_instruction=system_prompt
                    )
                except Exception as e:
                    print(f"[!] Model call failed: {e}")
                    break

                decision = UnifiedDecision.model_validate(response)

                # --- CONTEXT MANAGEMENT: Add turn to lean history for next step ---
                # We record the model's reasoning and the EXPLICIT action taken.
                action_desc = f"Action: {decision.action_type}"
                if decision.target_id is not None: action_desc += f" on ID {decision.target_id}"
                if decision.input_text: action_desc += f" with input '{decision.input_text}'"

                lean_history.append(types.Content(role="user", parts=[types.Part.from_text(text=f"Turn {step+1}: URL {current_page.url}. Result of previous {action_desc} is shown in the next screenshot.")]))
                lean_history.append(types.Content(role="model", parts=[types.Part.from_text(text=json.dumps(response))]))

                # Limit history length to prevent token overflow
                if len(lean_history) > 40:
                    lean_history = lean_history[-40:]

                print(f"[*] History size: {len(lean_history)} entries (text-only).")

                # Resolution Logic: Fill placeholders from the local element_map
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

                # Out of signals, into signal_errors
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

                    should_update = True
                    if existing:
                        old_val = existing.get('value')
                        if isinstance(old_val, bool) and old_val is True and new_val is False:
                            should_update = False
                        elif isinstance(old_val, (int, float)) and old_val > 0 and (new_val == 0 or new_val is False):
                            should_update = False

                    if should_update:
                        entry.signal.step = decision.step_name
                        entry.signal.evidence = screenshot_name
                        all_signals[entry.name] = entry.signal.model_dump()
                        captured_signals.append(f"{entry.name}={entry.signal.value}")
                        if entry.name in all_errors:
                            del all_errors[entry.name]

                if captured_signals:
                    print(f"[*] Signals Captured: {', '.join(captured_signals)}")

                # Deterministic pass: DOM measurement
                first_contact_done = any(n in all_signals for n in FIRST_CONTACT)
                try:
                    dom_values, dom_gaps = await collect.measure(current_page)
                    for name, value in dom_values.items():
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
                        if name in FIRST_CONTACT and first_contact_done:
                            all_errors.setdefault(
                                name, "am Erstkontakt nicht messbar")
                            continue
                        all_errors[name] = reason
                except Exception as error:
                    print(f"[!] DOM measurement failed: {error}")

                for entry in decision.signal_errors:
                    if entry.name not in all_signals:
                        all_errors[entry.name] = entry.reason

                # Store decision in journey log
                steps_log.append({
                    "step": decision.step_name,
                    "url": current_page.url,
                    "screenshot": screenshot_name,
                    "dom_hash": dom_hash,
                    "chosen_by": decision.thought_process[:150]
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
                        is_banner_step = all_signals.get('banner_detected', {}).get('value') is True
                        has_reject_option = any(s.name == "reject_button_present" and s.signal.value is True for s in decision.signals)

                        if is_banner_step or has_reject_option:
                            reject_click_depth += 1
                            print(f"[*] Banner Flow. Reject Click Depth: {reject_click_depth}")

                        coords = element_map[str(decision.target_id)]

                        if decision.action_type == "type" and decision.input_text:
                            text = decision.input_text
                            if "SESSION_EMAIL" in text or "SESSION_USERNAME" in text:
                                if not username:
                                    print("[!] Login/Registration required but no credentials provided. Stopping.")
                                    decision.is_blocked = True
                                    break
                                text = text.replace("SESSION_EMAIL", username).replace("SESSION_USERNAME", username)
                            if "SESSION_PASSWORD" in text:
                                if not password:
                                    print("[!] Password required but none provided. Stopping.")
                                    decision.is_blocked = True
                                    break
                                text = text.replace("SESSION_PASSWORD", password)
                            if "FETCH_OTP" in text:
                                print("[!] OTP verification reached. Stopping as automatic OTP fetching is disabled.")
                                decision.is_blocked = True
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
    except Exception as e:
        print(f"[!] Fatal error during exploration: {e}")
        # Ensure browser is closed
        try:
            if 'browser' in locals(): await browser.close()
        except: pass
        final_step_name = "crashed"

    return steps_log, reject_click_depth, final_step_name, (decision.is_blocked if decision else False), all_signals, all_errors, meta
