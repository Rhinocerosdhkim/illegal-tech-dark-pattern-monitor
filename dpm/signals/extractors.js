/*
 * Signal measurement — pure browser JavaScript.
 *
 * No Python in this file, and no Playwright: it is injected with
 * page.evaluate() and would run unchanged as a Chrome extension content
 * script. That is the whole reason it is a .js file and not a string
 * literal somewhere (ARBEITSTEILUNG_Technik.md section 2, task 4).
 *
 * Returns { signals, errors }.
 *
 *   signals   name -> value.  "measured, and this is what it is"
 *   errors    name -> reason. "we could not check"
 *
 * The distinction is the whole point. false means the thing is not there;
 * an entry in errors means we do not know. Those are two different
 * statements about a company, and the engine turns the second into
 * "unklar" on its own -- but only as long as they are kept apart. A
 * measurement that did not work is NEVER written as false, 0 or null.
 *
 * Only signals from rules/_SIGNALE.md appear here. A name that is not in
 * that list cannot reach a rule.
 */
(() => {
  "use strict";

  const out = { signals: {}, errors: {} };
  const set = (name, value) => { out.signals[name] = value; };
  // First reason wins: the specific one ("no reject button in the banner")
  // is written before the blanket one ("no banner at all"), and being
  // overwritten by the blanket one would misstate why we have no value.
  const gap = (name, reason) => {
    if (!(name in out.signals) && !(name in out.errors)) {
      out.errors[name] = reason;
    }
  };

  /* ------------------------------------------------ words we look for */

  const WORDS = {
    accept: ["alle akzeptieren", "akzeptieren", "alle zulassen", "zustimmen",
             "einverstanden", "alle cookies erlauben", "ich stimme zu",
             "annehmen", "accept all", "accept", "agree", "allow all"],
    reject: ["alle ablehnen", "ablehnen", "nur notwendige", "nur erforderliche",
             "nur essenzielle", "ohne einwilligung fortfahren", "verweigern",
             "reject all", "reject", "decline", "necessary only"],
    more:   ["einstellungen", "mehr informationen", "mehr erfahren", "anpassen",
             "individuell", "details", "verwalten", "optionen", "konfigurieren",
             "settings", "manage", "preferences"],
    banner: ["cookie", "einwilligung", "datenschutz", "tracking",
             "zustimmung", "consent", "privacy"],
    cancel: ["vertrag kündigen", "abo kündigen", "kündigen", "kündigung"],
    order:  ["kaufen", "zahlungspflichtig bestellen", "jetzt bestellen",
             "bestellen", "jetzt kaufen", "kostenpflichtig bestellen",
             "zur kasse", "buchung abschließen", "zahlungspflichtig buchen"],
    checkout: ["warenkorb", "zur kasse", "checkout", "einkaufswagen"],
    required: ["widerruf", "impressum", "gesamtpreis", "lieferkosten",
               "versandkosten", "agb"],
    gratis: ["gratis", "kostenlos", "umsonst", "geschenkt"],
    vat: ["inkl. mwst", "inkl. mehrwertsteuer", "inklusive mehrwertsteuer",
          "zzgl. mwst", "inkl. ust", "mwst.", "mehrwertsteuer"],
    finance: ["bafin", "versicherung", "kredit", "depot", "bausparen",
              "darlehen", "girokonto"],
    b2b: ["zzgl. mwst", "zzgl. ust", "nettopreis", "preise netto",
          "nur für gewerbetreibende", "nur fuer gewerbetreibende",
          "nur für geschäftskunden", "b2b", "gewerbliche kunden"],
    recurring: ["abo", "abonnement", "mitgliedschaft", "tarif"],
    minTerm: ["mindestlaufzeit", "vertragslaufzeit", "mindestvertragslaufzeit"],
    renewal: ["verlängert sich automatisch", "automatische verlängerung",
              "verlängert sich stillschweigend"],
    cancelTerms: ["kündigungsfrist", "monatlich kündbar", "jederzeit kündbar"],
  };

  const PERIOD = /(?:\/|pro\s+)(monat|jahr|woche|quartal)|monatlich|jährlich|wöchentlich/i;
  const PRICE = /\d+[.,]\d{2}\s*(?:€|eur)|(?:€|eur)\s*\d+[.,]\d{2}/i;

  const text = (element) =>
    ((element && (element.innerText || element.textContent)) || "")
      .replace(/\s+/g, " ").trim();

  const lower = (element) => text(element).toLowerCase();

  const hasWord = (haystack, list) =>
    list.some((word) => haystack.includes(word));

  /* ------------------------------------------------------- the page */

  // Open shadow roots are part of the page and have to be searched:
  // consent tools routinely put the banner in one. A closed root cannot
  // be reached at all -- that is reported as a gap, never as "no banner".
  let closedRootSeen = false;

  const everything = () => {
    const found = [];
    const walk = (root) => {
      let nodes;
      try {
        nodes = root.querySelectorAll("*");
      } catch (error) {
        return;
      }
      for (const node of nodes) {
        found.push(node);
        if (node.shadowRoot) walk(node.shadowRoot);
      }
    };
    walk(document);
    return found;
  };

  const ALL = everything();
  const BODY_TEXT = (document.body ? lower(document.body) : "");

  const visible = (element) => {
    const box = element.getBoundingClientRect();
    if (box.width <= 0 || box.height <= 0) return false;
    const style = getComputedStyle(element);
    return style.visibility !== "hidden" && style.display !== "none"
      && Number(style.opacity) > 0.05;
  };

  const clickable = (element) => {
    const tag = element.tagName;
    return tag === "BUTTON" || tag === "A"
      || (tag === "INPUT" && ["submit", "button"].includes(element.type))
      || element.getAttribute("role") === "button";
  };

  /* ------------------------------------------- is this the shop at all */

  // What we are standing on may not be the site at all: a bot check, a
  // login wall, an error page. Whatever is measured there is a fact about
  // the interstitial, not about the shop, and recorded as one it becomes a
  // clean bill of health for a site nobody examined.
  //
  // The navigator can say "abseits", but only when there is a model. The
  // keyless mode -- which is what anybody without an API key gets, and the
  // mode the demonstration runs in -- has nobody to ask. So the same
  // judgement is made here, deterministically, and kept deliberately
  // narrow: a false positive throws a real measurement away.
  const blocked = (() => {
    const CAPTCHA = ["recaptcha", "hcaptcha", "turnstile", "cf-challenge",
                     "cf-turnstile", "px-captcha", "geo.captcha"];
    const marked = Array.from(
      document.querySelectorAll("script[src], iframe[src], div[id], div[class]"))
      .some((node) => hasWord(
        ((node.getAttribute("src") || "") + " " + (node.id || "") + " " +
         (typeof node.className === "string" ? node.className : ""))
          .toLowerCase(), CAPTCHA));
    if (marked || hasWord(BODY_TEXT, ["ich bin kein roboter",
                                      "verify you are human",
                                      "sind sie ein mensch",
                                      "ungewoehnliche aktivitaet",
                                      "unusual traffic"])) {
      return "Bot-Pruefung statt der Seite";
    }

    // A login form in a header dropdown is normal. A page that is nothing
    // but a login form is a wall. Both conditions have to hold.
    const password = Array.from(
      document.querySelectorAll("input[type=password]")).some(visible);
    const ordering = ALL.some(
      (element) => clickable(element) && visible(element)
        && hasWord(lower(element), WORDS.order));
    if (password && !ordering && BODY_TEXT.length < 1200) {
      return "Anmeldewand statt der Seite";
    }

    // Only the title and the first heading -- "404" anywhere in the body
    // could be an article number.
    const heading = document.querySelector("h1");
    const banner_text = ((document.title || "") + " " +
                         (heading ? text(heading) : "")).toLowerCase();
    if (hasWord(banner_text, ["seite nicht gefunden", "404", "403",
                              "nicht verfuegbar", "access denied",
                              "zugriff verweigert", "page not found",
                              "service unavailable"])) {
      return "Fehlerseite statt der Seite";
    }
    return null;
  })();

  if (blocked) out.blocked = blocked;

  /* --------------------------------------------------------- colours */

  const channel = (value) => {
    const c = value / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  };

  const parse = (value) => {
    const found = (value || "").match(/[\d.]+/g);
    if (!found || found.length < 3) return null;
    const [r, g, b] = found.map(Number);
    const alpha = found.length > 3 ? Number(found[3]) : 1;
    return alpha < 0.05 ? null : [r, g, b];
  };

  const luminance = ([r, g, b]) =>
    0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);

  // An element with a transparent background sits on whatever is behind
  // it, so the ancestor that actually paints decides the contrast.
  const backdrop = (element) => {
    let node = element;
    while (node && node !== document.documentElement) {
      const colour = parse(getComputedStyle(node).backgroundColor);
      if (colour) return colour;
      node = node.parentElement;
    }
    return [255, 255, 255];
  };

  const contrast = (element) => {
    const front = parse(getComputedStyle(element).color);
    if (!front) return null;
    const back = backdrop(element);
    const a = luminance(front), b = luminance(back);
    const ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    return Math.round(ratio * 10) / 10;
  };

  const area = (element) => {
    const box = element.getBoundingClientRect();
    return Math.round(box.width * box.height);
  };

  /* ------------------------------------------------- consent banner */

  const bannerCandidates = ALL.filter((element) => {
    const style = getComputedStyle(element);
    const floating = ["fixed", "sticky", "absolute"].includes(style.position)
      || Number(style.zIndex) > 100;
    if (!floating || !visible(element)) return false;
    const content = lower(element);
    return content.length < 4000 && hasWord(content, WORDS.banner);
  });

  // The innermost floating element that still carries the consent words:
  // taking the outermost would drag half the page in and make the button
  // search meaningless.
  const controlsOf = (element) => Array.from(element.querySelectorAll("*"))
    .filter((node) => clickable(node) && visible(node))
    .map((node) => ({ element: node, label: lower(node) }))
    .filter((entry) => entry.label.length > 0 && entry.label.length < 80);

  // A whole label that is nothing but a confirmation. Matched against the
  // complete text, never as a substring: "ok" inside "cookie", "lokal" or
  // "blockieren" would turn half the page into an accept button.
  const SHORT_ACCEPT =
    /^(ok|okay|verstanden|alles klar|einverstanden|zulassen|weiter)[.!]?$/;

  const isAccept = (label) =>
    hasWord(label, WORDS.accept) || SHORT_ACCEPT.test(label);
  const isReject = (label) => hasWord(label, WORDS.reject);

  // A consent banner is recognised by the choice it offers, not by the
  // words it happens to contain. Every lawful German site carries a fixed
  // footer with "Impressum · Datenschutz · AGB"; on the words alone that
  // footer counts as a banner, reject_button_present comes out false, and
  // DP-001 certifies "eindeutig" against a site that did nothing wrong.
  //
  // The choice has to be an acceptance or a refusal. "Einstellungen",
  // "Details", "Verwalten", "Optionen" are ordinary interface words, and
  // gating on those as well let the consent-withdrawal tab that OneTrust,
  // Usercentrics and Cookiebot leave floating on every page count as a
  // banner — a tab that sits on more lawful sites than unlawful ones.
  const withChoice = bannerCandidates.filter(
    (element) => controlsOf(element).some(
      (entry) => isAccept(entry.label) || isReject(entry.label)));

  const banner = withChoice
    .filter((element) => !withChoice.some(
      (other) => other !== element && element.contains(other)))
    .sort((a, b) => area(b) - area(a))[0] || null;

  // Consent wording, but no acceptance and no refusal we can read: a
  // settings tab, a privacy teaser — or a real banner whose buttons sit
  // behind a closed shadow root or carry their text in an attribute we do
  // not read. From here those cannot be told apart, and "false" would be
  // an assertion where we have none. It belongs in errors.
  const unreadableBanner = !banner && bannerCandidates.length > 0;

  const consentIframe = Array.from(document.querySelectorAll("iframe"))
    .some((frame) => hasWord(
      ((frame.id || "") + " " + (frame.title || "") + " " +
       (frame.getAttribute("src") || "")).toLowerCase(), WORDS.banner));

  if (banner) {
    set("banner_detected", true);

    const controls = controlsOf(banner);

    const pick = (list) => {
      // Longest match wins: "alle ablehnen" must not be taken for
      // "alle akzeptieren" through a shared prefix.
      let best = null, bestLength = 0;
      for (const entry of controls) {
        for (const word of list) {
          if (entry.label.includes(word) && word.length > bestLength) {
            best = entry.element;
            bestLength = word.length;
          }
        }
      }
      return best;
    };

    const acceptButton = pick(WORDS.accept)
      || (controls.find((entry) => SHORT_ACCEPT.test(entry.label))
          || {}).element || null;
    const rejectButton = pick(WORDS.reject);
    const moreButton = pick(WORDS.more);

    set("reject_button_present", rejectButton !== null);
    set("more_info_present", moreButton !== null);

    if (acceptButton) {
      set("accept_button_area_px2", area(acceptButton));
      const ratio = contrast(acceptButton);
      if (ratio !== null) set("accept_contrast_ratio", ratio);
      else gap("accept_contrast_ratio", "Textfarbe des Zustimmen-Buttons nicht lesbar");
    } else {
      gap("accept_button_area_px2", "Zustimmen-Schaltflaeche im Banner nicht gefunden");
      gap("accept_contrast_ratio", "Zustimmen-Schaltflaeche im Banner nicht gefunden");
    }

    if (rejectButton) {
      set("reject_button_area_px2", area(rejectButton));
      const ratio = contrast(rejectButton);
      if (ratio !== null) set("reject_contrast_ratio", ratio);
      else gap("reject_contrast_ratio", "Textfarbe des Ablehnen-Buttons nicht lesbar");
    } else {
      // Not zero: a button that does not exist has no area. Zero would
      // read as "measured, and it is zero pixels" and make every ratio
      // rule fire.
      gap("reject_button_area_px2", "keine Ablehnen-Schaltflaeche auf der ersten Ebene");
      gap("reject_contrast_ratio", "keine Ablehnen-Schaltflaeche auf der ersten Ebene");
    }

    const boxes = Array.from(banner.querySelectorAll("input[type=checkbox]"));
    set("preselected_checkbox_count",
        boxes.filter((box) => box.checked && !box.disabled).length);
  } else if (consentIframe || closedRootSeen || unreadableBanner) {
    gap("banner_detected",
        "Einwilligungswoerter gefunden, aber weder Zustimmung noch Ablehnung "
        + "lesbar — von hier nicht entscheidbar, ob ein Banner vorliegt");
  } else {
    set("banner_detected", false);
  }

  for (const name of ["accept_button_area_px2", "reject_button_area_px2",
                      "accept_contrast_ratio", "reject_contrast_ratio",
                      "reject_button_present", "preselected_checkbox_count",
                      "more_info_present"]) {
    gap(name, "kein Einwilligungsbanner im Dokument gefunden");
  }

  /* ---------------------------------------------------- order button */

  const buttons = ALL
    .filter((element) => clickable(element) && visible(element))
    .map((element) => ({ element, label: text(element) }))
    .filter((entry) => entry.label.length > 0 && entry.label.length < 80);

  const order = buttons.find(
    (entry) => hasWord(entry.label.toLowerCase(), WORDS.order));
  set("order_button_found", order !== undefined);
  if (order) set("order_button_label", order.label);
  else gap("order_button_label", "keine Bestellschaltflaeche auf dieser Seite");

  const cancel = buttons.find(
    (entry) => hasWord(entry.label.toLowerCase(), WORDS.cancel));
  set("has_kuendigungsbutton", cancel !== undefined);
  if (cancel) {
    set("kuendigungsbutton_label", cancel.label);
    set("kuendigungsbutton_font_size_px",
        Math.round(parseFloat(getComputedStyle(cancel.element).fontSize)));
    const ratio = contrast(cancel.element);
    if (ratio !== null) set("kuendigungsbutton_contrast_ratio", ratio);
    else gap("kuendigungsbutton_contrast_ratio", "Textfarbe nicht lesbar");

    let node = cancel.element, hidden = false;
    while (node && node !== document.body) {
      if ((node.tagName === "DETAILS" && !node.open)
          || node.getAttribute("aria-expanded") === "false") {
        hidden = true;
        break;
      }
      node = node.parentElement;
    }
    set("kuendigungsbutton_hidden_in_menu", hidden);
  } else {
    for (const name of ["kuendigungsbutton_label",
                        "kuendigungsbutton_font_size_px",
                        "kuendigungsbutton_contrast_ratio",
                        "kuendigungsbutton_hidden_in_menu"]) {
      gap(name, "keine Kuendigungsschaltflaeche auf dieser Seite");
    }
  }

  /* ------------------------------------------ mandatory information */

  const scrollDepth = (element) => {
    const height = Math.max(document.body.scrollHeight,
                            document.documentElement.scrollHeight, 1);
    const top = element.getBoundingClientRect().top + window.scrollY;
    return Math.max(0, Math.min(100, Math.round(top / height * 100)));
  };

  const leaves = ALL.filter(
    (element) => element.children.length === 0 && text(element).length > 0);

  let requiredWord = null, requiredNode = null;
  for (const word of WORDS.required) {
    const hit = leaves.find((element) => lower(element).includes(word));
    if (hit) { requiredWord = word; requiredNode = hit; break; }
  }

  set("required_info_found", requiredNode !== null);
  if (requiredNode) {
    set("required_info_type", requiredWord);
    set("scroll_depth_of_required_info_pct", scrollDepth(requiredNode));

    // Measured in the region the notice sits in, not over the whole page:
    // _SIGNALE.md says "im Pflichtinformationsbereich".
    const region = requiredNode.closest("footer, section, div, article")
      || requiredNode;
    const inside = Array.from(region.querySelectorAll("*"))
      .filter((element) => element.children.length === 0
                        && text(element).length > 0);
    const parts = inside.length ? inside : [requiredNode];

    const sizes = parts
      .map((element) => parseFloat(getComputedStyle(element).fontSize))
      .filter((value) => !Number.isNaN(value));
    if (sizes.length) set("font_size_min_px", Math.round(Math.min(...sizes)));
    else gap("font_size_min_px", "keine lesbare Schriftgroesse im Pflichthinweis");

    const ratios = parts.map(contrast).filter((value) => value !== null);
    if (ratios.length) set("text_contrast_min", Math.min(...ratios));
    else gap("text_contrast_min", "keine lesbaren Farben im Pflichthinweis");

    set("hidden_by_opacity_count", parts.filter((element) => {
      const value = Number(getComputedStyle(element).opacity);
      return !Number.isNaN(value) && value < 0.5;
    }).length);
  } else {
    for (const name of ["required_info_type", "font_size_min_px",
                        "text_contrast_min", "hidden_by_opacity_count",
                        "scroll_depth_of_required_info_pct"]) {
      gap(name, "kein Pflichthinweis ueber die Stichwortliste gefunden");
    }
  }

  /* ------------------------------------------------ prices, context */

  set("has_price_display", PRICE.test(BODY_TEXT));

  // Consumer offer or not: prices quoted including VAT point at consumers,
  // net prices and "trade customers only" at businesses. Without any price
  // on the page there is nothing to read it from -- and guessing "yes"
  // would make rules apply to sites they were never meant for.
  if (PRICE.test(BODY_TEXT)) {
    set("is_b2c_offer", !hasWord(BODY_TEXT, WORDS.b2b));
  } else {
    gap("is_b2c_offer",
        "keine Preisangabe auf der Seite — Verbrauchereigenschaft nicht "
        + "aus dem Preisumfeld ableitbar");
  }
  set("has_checkout_flow", hasWord(BODY_TEXT, WORDS.checkout)
                           || out.signals.order_button_found === true);
  set("gratis_claim_present", hasWord(BODY_TEXT, WORDS.gratis));
  set("is_financial_services", hasWord(BODY_TEXT, WORDS.finance));
  set("has_recurring_contract_keywords", hasWord(BODY_TEXT, WORDS.recurring));

  const language = (document.documentElement.getAttribute("lang") || "").trim();
  if (language) set("page_language", language);
  else gap("page_language", "die Seite gibt keine Sprache an");

  const vatNode = leaves.find((element) => hasWord(lower(element), WORDS.vat));
  set("vat_disclosure_present", vatNode !== undefined);
  if (vatNode) set("vat_disclosure_scroll_pct", scrollDepth(vatNode));
  else gap("vat_disclosure_scroll_pct", "kein Umsatzsteuerhinweis gefunden");

  /* -------------------------------------------------- contract type */

  const period = BODY_TEXT.match(PERIOD);
  set("recurring_price_notation_present", period !== null);
  if (period) set("recurring_price_period", period[1] || period[0]);
  else gap("recurring_price_period", "keine Periodenangabe im Preisumfeld");

  set("min_contract_term_stated", hasWord(BODY_TEXT, WORDS.minTerm));
  set("auto_renewal_text_present", hasWord(BODY_TEXT, WORDS.renewal));
  set("cancellation_terms_present", hasWord(BODY_TEXT, WORDS.cancelTerms));

  return out;
})()
