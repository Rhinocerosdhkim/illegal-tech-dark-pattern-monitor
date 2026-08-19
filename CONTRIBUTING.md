# Mitarbeiten — auch ohne Git-Kenntnisse

Dieses Repository ist unser gemeinsamer Arbeitsstand. **Du brauchst weder Git noch einen Editor auf dem Rechner.** Alles lässt sich direkt im Browser auf github.com erledigen.

Inhaltliche Anleitung zum Regelwerk: [`rules/README.md`](rules/README.md). Dieses Dokument erklärt nur das *Wie* der Bedienung.

---

## Eine Datei ändern — in sechs Schritten

1. Datei im Browser öffnen, z. B. [`rules/DP-003_Dringlichkeit.yaml`](rules/DP-003_Dringlichkeit.yaml)
2. Oben rechts auf das **Stift-Symbol** (✏️ *Edit this file*) klicken
3. Text ändern. Ganz normales Tippen — Einrückung mit **Leerzeichen**, niemals mit Tab
4. Oben rechts **Commit changes…**
5. In das Feld eine kurze Beschreibung schreiben, z. B. `DP-003: Tatbestand und Anspruchskette ergänzt`
6. **Commit directly to the `main` branch** auswählen → **Commit changes**

Fertig. Deine Änderung ist sofort für alle sichtbar. Kaputtmachen kannst du nichts — jede Version bleibt erhalten und lässt sich zurückholen.

> **Größere oder unsichere Änderung?** Wähle in Schritt 6 stattdessen *Create a new branch and start a pull request*. Dann schaut jemand drüber, bevor es in `main` landet.

---

## Wenn zwei am selben Tag an derselben Regel arbeiten

Trag dich **vorher** in die Statustabelle im [README](README.md) und in das Feld `bearbeiter` der YAML-Datei ein. Das ist unsere einzige Absprache — mehr Prozess brauchen wir bei sechs Regeln nicht.

---

## Statusfluss einer Regel

```
ENTWURF  →  IN_ARBEIT  →  REVIEW  →  FERTIG
```

| Status | Wann setzen |
|---|---|
| `IN_ARBEIT` | sobald du anfängst — zusammen mit deinem Namen in `bearbeiter` |
| `REVIEW` | wenn du fertig bist. **Danach im Teamchat melden.** Das Entwicklungsteam lädt die Regel ins System und meldet zurück, ob sie technisch läuft |
| `FERTIG` | erst nach gemeinsamer Durchsicht |

**Lieber früh im Zustand `REVIEW` als spät im Zustand `FERTIG`.** Am Donnerstagabend jagen wir zum ersten Mal alle Regeln durch das System — da bricht garantiert etwas, und dafür brauchen wir Zeit.

---

## YAML — die drei Fehler, die tatsächlich passieren

Du musst kein YAML können. Es ist eine Liste von Feldern mit Doppelpunkt. Drei Dinge reichen:

**1. Einrückung mit Leerzeichen, nie mit Tab.** Die Einrückungstiefe der Vorlage einfach beibehalten.

**2. Text mit Doppelpunkt oder Sonderzeichen in Anführungszeichen:**

```yaml
name_de: "Vorgetäuschte Begrenzung: Countdown"     # ✅
name_de: Vorgetäuschte Begrenzung: Countdown       # ❌ zweiter Doppelpunkt bricht
```

**3. Für längeren Text `>` benutzen** — dann darfst du beliebig schreiben, auch mehrzeilig:

```yaml
tatbestand_de: >
  Eine Einwilligung ist nur wirksam, wenn sie freiwillig
  erteilt wird. Freiwilligkeit setzt voraus, dass die
  Ablehnung nicht erschwert ist.
```

Wenn GitHub dir beim Speichern eine Fehlermeldung zeigt oder etwas seltsam aussieht: **einfach im Teamchat melden.** Formatfehler sind in zwei Minuten behoben und niemandem peinlich.

---

## Ein Issue aufmachen — wofür?

Über *Issues* → *New issue* stehen zwei Vorlagen bereit:

| Vorlage | Wofür |
|---|---|
| **Regel-Review** | Deine Regel steht auf `REVIEW` und soll durchs System gejagt werden |
| **Signal-Anfrage** | Du brauchst ein Signal, das nicht in [`_SIGNALE.md`](rules/_SIGNALE.md) steht |

Zur Signal-Anfrage: **frag, bevor du die Regel darauf aufbaust.** Manches ist in einem Tag machbar, manches nicht. Eine Regel, deren Kern auf einem nicht zugesagten Signal steht, ist bis Sonntag wertlos.

---

## Entscheidungen festhalten

Jede inhaltliche Entscheidung kommt mit Datum und Begründung in [`docs/DECISIONS.md`](docs/DECISIONS.md). Das erspart uns, dieselbe Diskussion zweimal zu führen — und liefert das Material für die Fragerunde nach der Präsentation.

---

## English — short version

You do not need Git. Open any file on github.com, click the ✏️ pencil, edit, then **Commit changes** to `main`. Nothing can be broken permanently — every version is recoverable.

Three YAML rules: indent with **spaces** (never tabs); wrap text containing a colon in `"quotes"`; use `>` for anything longer than one line. Format errors — just say so in the team chat, they take two minutes to fix.

Set `status: IN_ARBEIT` and your name in `bearbeiter` when you start, `REVIEW` when done, and tell the team chat. Send it in `REVIEW` early rather than `FERTIG` late.

Need a signal that is not in [`rules/_SIGNALE.md`](rules/_SIGNALE.md)? Open a **Signal-Anfrage** issue *before* building your rule around it.
