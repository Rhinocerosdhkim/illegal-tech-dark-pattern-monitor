# Befundstufen — der Maßstab

**Stand 20.08.2026.** Verbindlich für jede Bedingung in `rules/*.yaml`.
Entstanden aus der Einzelprüfung aller sechs Regeln am 20.08.: 42 Beanstandungen, davon 15 in der höchsten Risikoklasse. Fast alle gingen auf **fünf immer gleiche Fehlermuster** zurück. Dieses Dokument macht daraus einen Prüfmaßstab, damit dieselben Fehler nicht wieder entstehen.

**Keine Rechtsberatung.** Der Maßstab ist ein Arbeitsmittel des Teams und ersetzt die juristische Bewertung nicht.

---

## 1. Was die Stufen aussagen

Jede Stufe ist eine **Aussage, die wir gegenüber einem Unternehmen treffen**. Sie muss so gemeint sein, wie sie dasteht.

| Stufe | Was wir damit sagen | Was wir belegen können müssen |
|---|---|---|
| **eindeutig** | „Das ist so." | Jedes Tatbestandsmerkmal ist gemessen. Ein Unternehmen könnte den **Sachverhalt** nicht bestreiten — nur seine rechtliche Würdigung |
| **verdächtig** | „Das sieht danach aus, und hier ist warum." | Eine belastbare Messung, die auf rechtmäßigen Seiten **selten** ist. Rechtmäßige Erklärungen existieren, sind aber die Ausnahme |
| **unklar** | „Wir behaupten nichts. Wir konnten es nicht prüfen." | Nur, dass ein benötigter Messwert fehlt — und warum |
| **unauffällig** | „Wir haben geprüft und nichts gefunden." | Dass **alle** Bedingungen der Regel auswertbar waren |
| *nicht anwendbar* | *(interner Zustand, erscheint in keiner Akte)* | Dass die Regel diesen Sachverhalt gar nicht betrifft |

> **Die Grundregel, aus der alles Weitere folgt:**
> **Wir sagen nie mehr, als wir gemessen haben.** Eine unentdeckte Auffälligkeit kostet uns einen Befund. Eine falsche Behauptung kostet uns die Glaubwürdigkeit des Projekts — und macht die Verbraucherzentrale nach § 4 Nr. 1, Nr. 2 UWG, §§ 823, 824 BGB angreifbar.
> **Im Zweifel eine Stufe herunter. Ausnahmslos.**

---

## 2. Die Hürde für `eindeutig` — vier Tests, alle müssen bestehen

Eine Bedingung darf **nur dann** `eindeutig` tragen, wenn alle vier zutreffen. Fällt einer, ist die Höchststufe `verdächtig`.

### T1 · Vollständigkeit des Tatbestands
> Jedes Merkmal der zitierten Norm ist **gemessen** — oder die Norm ordnet die Unlauterkeit ohne dieses Merkmal an (Per-se-Verbot).
> Wird auch nur ein Merkmal **stillschweigend angenommen**, ist `eindeutig` gesperrt.

*Anwendung:* Anhang Nr. 7 zu § 3 Abs. 3 UWG verlangt eine **unwahre** Angabe **zur Verfügbarkeit**, mit der Absicht, eine **sofortige** Entscheidung zu veranlassen, **ohne Zeit und Gelegenheit** zur Information. Ein zurückspringender Countdown belegt davon: dass der Zähler sitzungsbezogen erzeugt wird. Drei der vier Merkmale bleiben unbelegt → DP-003 kann `eindeutig` nicht tragen.

### T2 · Keine offene gesetzliche Ausnahme
> Enthält die Norm eine Ausnahme, einen Halbsatz „dies gilt nicht für …" oder ein „es sei denn", das wir **nicht messen können**, ist `eindeutig` gesperrt.

*Anwendung:* § 25 Abs. 2 TDDDG nimmt technisch notwendige Speicherung aus — ein Cookie-Zähler kann sie nicht von tracking unterscheiden. Anhang Nr. 20 nimmt unvermeidbare Lieferkosten aus — Versandkosten sind genau das.

### T3 · Positive Feststellung, nicht Abwesenheit
> Ein Befund darf sich nur auf etwas stützen, das wir **gesehen** haben. Auf etwas, das wir **nicht gefunden** haben, nur dann, wenn die Suche den maßgeblichen Bereich **vollständig** abgedeckt hat.

*Anwendung:* Die Erfassung besucht drei bis vier Seiten eines Ziels und sucht nach Stichworten. „Kein Kündigungsbutton gefunden" und „keine Widerrufsbelehrung gefunden" sind **Abwesenheit von Beweis, nicht Beweis der Abwesenheit** → höchstens `verdächtig`.

### T4 · Eine geschlossene Positivliste stellt nichts fest
> Sagt die Norm „… **oder mit einer entsprechend eindeutigen Formulierung**", kann keine endliche Weißliste den Negativbeweis führen. `eindeutig` nur aus einer **belegten Negativliste**.

*Anwendung:* § 312j Abs. 3 BGB und § 312k Abs. 2 BGB sind beide offen formuliert. „Zahlungspflichtig buchen" (Bahn, Fluglinien), „Kostenpflichtig abonnieren", „Vertrag hier kündigen" — alle rechtmäßig, alle auf keiner unserer Listen.

### C4 · Abgeleitete Anwendbarkeit (bereits beschlossen)
> Beruht `applies_when` auf einer **unbestätigten Ableitung**, ist `eindeutig` gesperrt, bis ein Mensch die Voraussetzung im Zielprofil bestätigt.

---

## 3. Die Hürde für `verdächtig` — der Fünf-Seiten-Test

> **Die Bedingung wird gegen fünf gewöhnliche, rechtstreue deutsche Seiten gehalten** — etwa: Modeshop, Bank, Nachrichtenseite, Bäckerei, Softwareanbieter.
> **Löst sie bei einer davon aus, ist sie kein Anhaltspunkt, sondern Rauschen.** Dann wird sie enger gefasst oder gestrichen — nicht heruntergestuft.

Eine Stufe, die auf der Hälfte aller Seiten steht, sagt nichts mehr. Sie schadet doppelt: sie macht den Bericht unbrauchbar, und sie entwertet die Fälle, in denen sie zu Recht steht.

**Praxisregel für weiche Indizien** (Schriftgröße, Kontrast, Position, Klicktiefe): Sie tragen **nie einzeln**. Und die Kombination muss echte Aussagekraft hinzufügen — ein Merkmal, das bei der betrachteten Sachlage ohnehin fast immer zutrifft (etwa „Fußzeilenangabe steht unten"), ist als Paarhälfte wertlos.

---

## 4. `unauffällig` — die strengste Aussage von allen

> **`unauffällig` darf nur stehen, wenn jede einzelne Bedingung der Regel ausgewertet werden konnte.** War auch nur eine nicht auswertbar, lautet der Befund `unklar`.

Das ist keine Förmelei. „Wir haben geprüft und nichts gefunden" ist gegenüber einem Unternehmen eine Entlastung — und gegenüber der Verbraucherzentrale eine Zusage. Beides dürfen wir nur geben, wenn es stimmt.

**Folge, die beim Regelschreiben zu bedenken ist:** Eine Regel, die eine aktive Bedingung auf einem noch nicht zugesagten Signal (⚪) enthält, kann auf einer realen Seite **niemals** `unauffällig` sagen. Solche Bedingungen gehören auskommentiert, bis das Signal existiert.

---

## 5. Die fünf Fehlermuster — Prüfliste vor jedem Commit

Alle 42 Beanstandungen des 20.08. lassen sich hierauf zurückführen.

| # | Muster | Erkennungsfrage | Beispiel |
|---|---|---|---|
| **1** | **Umgekehrte Voraussetzung** | Fällt der **schwerste** Fall, den die Regel erfassen soll, durch `applies_when` heraus? | `applies_when: banner_detected == true` ließ die Seite ganz ohne Banner verschwinden — obwohl dort schon keine Einwilligung vorliegt |
| **2** | **Ausnahme ignoriert** | Steht im zweiten Halbsatz der Norm etwas, das die Bedingung nicht prüft? | Versandkosten sind die von Anhang Nr. 20 ausgenommenen Lieferkosten |
| **3** | **Messlücke als Befund** | Kann der Wert, auf den die Bedingung anschlägt, auch „nicht gemessen" bedeuten? | Knappheitshinweis ohne lesbare Zahl liefert `0`, und `== 0` löste aus |
| **4** | **Tautologische Paarhälfte** | Ist ein Glied der Und-Verknüpfung bei dieser Sachlage ohnehin fast immer wahr? | „Pflichtinformation steht unten auf der Seite" trifft auf jede Fußzeile zu |
| **5** | **Unerreichbare Bedingung** | Wird sie von einer früheren, höherstufigen Bedingung verschluckt? | Die Grauliste in DP-002 war nie erreichbar, weil `eindeutig` zuerst prüft |

---

## 6. Was der Text sagen darf

> **Der Erläuterungstext einer Regel darf nie mehr behaupten als die Stufe des konkreten Befundes.**

Ein Befund der Stufe `verdächtig` darf nicht mit „Die festgestellte Beschriftung entspricht dieser Vorgabe **nicht**" erläutert werden. Der Text gehört an die Stufe gebunden, nicht an die Regel.

Wortwahl je Stufe:

| Stufe | zulässig | unzulässig |
|---|---|---|
| eindeutig | „festgestellt", „gemessen", „liegt vor" | „Verstoß" als Feststellung |
| verdächtig | „Anhaltspunkt", „bedarf der Prüfung", „legt nahe" | „entspricht nicht", „ist unzulässig" |
| unklar | „konnte nicht geprüft werden", „nicht erhoben" | jede Aussage zur Sache |
| unauffällig | „keine Auffälligkeit festgestellt" | „rechtmäßig", „zulässig" |

---

## 7. Was dieser Maßstab am heutigen Regelwerk ändert

Angewandt auf alle sechs Regeln bleibt `eindeutig` an **drei** Stellen bestehen:

| Regel | Bedingung, die alle vier Tests besteht | Warum sie trägt |
|---|---|---|
| **DP-001** | Banner vorhanden, aber **überhaupt keine Ablehnmöglichkeit** — auch nicht über „Mehr Informationen" | T1: alle Merkmale beobachtet · T2: keine offene Ausnahme · T3: positive Beobachtung · T4: keine Liste im Spiel. Und: **OLG Köln, 19.01.2024, 6 U 80/23** entscheidet genau diese Gestaltung |
| **DP-002** | Beschriftung auf einer **belegten Negativliste** (neu) | T4 gewahrt: kein Negativbeweis aus einer Weißliste |
| **DP-004** | Bestätigungsseite **erreicht**, aber **ohne Bestätigungsschaltfläche** | T3: die erreichte Seite ist eine positive Beobachtung, keine Abwesenheit |

Alles Übrige steht künftig auf `verdächtig` oder darunter.

> **Das ist die wichtigste Zahl dieses Dokuments: drei.**
> Ein Werkzeug, das bei sechs Mustern dreimal „eindeutig" sagt und sonst „Anhaltspunkt", ist für eine Verbraucherzentrale brauchbar. Eines, das überall „eindeutig" sagt, ist es nicht — und wäre in der Fragerunde nach der Präsentation nicht zu halten.

**Zu erwartende Folge für die Vorführung:** Der Referenzfall viagogo hat eine Ablehnmöglichkeit im Banner und trägt danach **keinen** `eindeutig`-Befund mehr. Das ist kein Fehler des Maßstabs, sondern eine Aussage über das Ziel. Wenn die Vorführung einen `eindeutig`-Befund zeigen soll, braucht sie ein Ziel, bei dem einer trägt — das ist eine Frage der Zielauswahl, nicht der Regeln.
