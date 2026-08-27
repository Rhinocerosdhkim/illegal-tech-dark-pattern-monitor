import tldextract
from urllib.parse import urlparse

async def get_cookie_stats(context, current_url):
    """
    Analyzes cookies in the current browser context.
    Identifies 1st party vs 3rd party based on the current URL.
    """
    cookies = await context.cookies()
    parsed_url = urlparse(current_url)
    ext = tldextract.extract(current_url)
    main_domain = f"{ext.domain}.{ext.suffix}"
    
    first_party = []
    third_party = []
    
    for cookie in cookies:
        cookie_domain = cookie['domain'].lstrip('.')
        # Simple check for 3rd party: is the cookie domain a suffix of our main domain?
        if cookie_domain.endswith(main_domain):
            first_party.append(cookie)
        else:
            third_party.append(cookie)
            
    return {
        "total_cookies": len(cookies),
        "first_party_count": len(first_party),
        "third_party_count": len(third_party),
        "third_party_domains": list(set([c['domain'] for c in third_party]))
    }

async def check_local_storage(page):
    """
    Retrieves the count of items in LocalStorage and SessionStorage.
    Often used for 'cookie-less' tracking.
    """
    try:
        storage_info = await page.evaluate('''() => {
            return {
                local_storage_count: Object.keys(localStorage).length,
                session_storage_count: Object.keys(sessionStorage).length,
                storage_keys: Object.keys(localStorage)
            };
        }''')
        return storage_info
    except:
        return {"error": "Could not access storage"}

async def get_network_signals(page):
    """
    This could be expanded to track requests to known tracking domains.
    For now, it returns a summary of the page's current technical state.
    """
    # Example: Look for common tracking keywords in script sources
    scripts = await page.locator('script[src]').all_attribute_values('src')
    trackers = ["analytics", "tracker", "pixel", "facebook", "google-analytics", "hotjar", "clarity"]
    
    detected_trackers = [src for src in scripts if any(t in src.lower() for t in trackers)]
    
    return {
        "script_tracker_count": len(detected_trackers),
        "detected_tracker_srcs": detected_trackers[:10] 
    }

async def get_accessibility_audit(page):
    """
    Checks for accessibility-related dark patterns like aria-hidden on legal info.
    """
    return await page.evaluate('''() => {
        const legalKeywords = ['impressum', 'widerruf', 'datenschutz', 'agb', 'privacy', 'legal', 'terms'];
        const results = {
            aria_hidden_on_required_info: false,
            hidden_by_opacity_count: 0,
            required_info_in_collapsed_element: false
        };

        const allElements = document.querySelectorAll('a, button, span, div, p');
        allElements.forEach(el => {
            const text = (el.innerText || '').toLowerCase();
            const isLegal = legalKeywords.some(kw => text.includes(kw));
            
            if (isLegal) {
                // Check aria-hidden
                let curr = el;
                while (curr && curr !== document.body) {
                    if (curr.getAttribute('aria-hidden') === 'true') {
                        results.aria_hidden_on_required_info = true;
                    }
                    curr = curr.parentElement;
                }

                // Check opacity
                const style = window.getComputedStyle(el);
                if (parseFloat(style.opacity) < 0.5) {
                    results.hidden_by_opacity_count++;
                }

                // Check if in collapsed element
                let parent = el.parentElement;
                while (parent && parent !== document.body) {
                    const pStyle = window.getComputedStyle(parent);
                    if (pStyle.display === 'none' || parseInt(pStyle.height) === 0) {
                         results.required_info_in_collapsed_element = true;
                    }
                    parent = parent.parentElement;
                }
            }
        });
        return results;
    }''')

class NetworkTracker:
    """
    Tracks network requests to identify third-party trackers.
    """
    def __init__(self, main_url):
        ext = tldextract.extract(main_url)
        self.main_domain = f"{ext.domain}.{ext.suffix}"
        self.third_party_requests = []
        self.tracker_keywords = ["analytics", "pixel", "collect", "track", "telemetry", "beacon"]

    def handle_request(self, request):
        url = request.url
        ext = tldextract.extract(url)
        request_domain = f"{ext.domain}.{ext.suffix}"
        
        if request_domain != self.main_domain:
            is_tracker = any(kw in url.lower() for kw in self.tracker_keywords)
            self.third_party_requests.append({
                "url": url,
                "domain": request_domain,
                "is_likely_tracker": is_tracker
            })

    def get_stats(self):
        trackers = [r for r in self.third_party_requests if r['is_likely_tracker']]
        return {
            "total_3rd_party_requests": len(self.third_party_requests),
            "likely_trackers_count": len(trackers),
            "unique_3rd_party_domains": list(set([r['domain'] for r in self.third_party_requests]))
        }
