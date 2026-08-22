/* Set-of-Mark overlay: numbered boxes over the clickable elements, so the
 * navigator can answer "click box 7" instead of guessing a selector.
 *
 * No Python in this file. It is injected with page.evaluate() and would run
 * unchanged as a content script (ARBEITSTEILUNG_Technik.md 0.1).
 *
 * Everything here is in viewport coordinates, for two reasons:
 *   - page.mouse.click() takes viewport coordinates. Document coordinates
 *     happen to match only while the page is scrolled to the top, and stop
 *     matching the moment a scroll step exists.
 *   - the container is position:fixed, so a body with position:relative or
 *     a transform on an ancestor cannot shift the boxes away from the
 *     elements they label. A box drawn over the wrong element is worse than
 *     no box: the model reports a number that then clicks somewhere else.
 *
 * Only elements actually inside the viewport are numbered. The screenshot
 * shows nothing else, so a number for anything else could only be guessed.
 */
() => {
    const OLD = document.getElementById('dpm-som-layer');
    if (OLD) OLD.remove();

    const layer = document.createElement('div');
    layer.id = 'dpm-som-layer';
    layer.style.cssText = 'position:fixed; inset:0; z-index:2147483647; ' +
        'pointer-events:none; margin:0; padding:0; border:0; background:none;';

    const width = window.innerWidth;
    const height = window.innerHeight;
    const selector = 'a, button, [role="button"], input[type="submit"], ' +
        'input[type="button"], [role="link"]';

    const map = {};
    let index = 0;

    for (const el of document.querySelectorAll(selector)) {
        const rect = el.getBoundingClientRect();
        if (rect.width < 8 || rect.height < 8) continue;
        if (rect.bottom <= 0 || rect.top >= height) continue;
        if (rect.right <= 0 || rect.left >= width) continue;

        const style = window.getComputedStyle(el);
        if (style.visibility === 'hidden' || style.display === 'none') continue;

        const box = document.createElement('div');
        box.style.cssText = 'position:absolute; box-sizing:border-box; ' +
            'border:2px solid #e11; pointer-events:none; ' +
            'top:' + rect.top + 'px; left:' + rect.left + 'px; ' +
            'width:' + rect.width + 'px; height:' + rect.height + 'px;';

        const label = document.createElement('span');
        label.textContent = index;
        label.style.cssText = 'position:absolute; top:0; left:0; ' +
            'background:#e11; color:#fff; font:bold 12px/1 sans-serif; ' +
            'padding:1px 3px; pointer-events:none;';

        box.appendChild(label);
        layer.appendChild(box);

        map[index] = {
            x: rect.left + rect.width / 2,
            y: rect.top + rect.height / 2,
            label: (el.innerText || el.getAttribute('aria-label') || '')
                .trim().slice(0, 60)
        };
        index += 1;
    }

    document.body.appendChild(layer);
    return map;
}
