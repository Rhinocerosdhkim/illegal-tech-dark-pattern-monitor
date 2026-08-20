# Fundstellenprüfung — DP-001 bis DP-006

**Stand 20.08.2026** · geprüft gegen öffentlich zugängliche Quellen
**Keine Rechtsberatung.** Diese Liste ersetzt die Prüfung durch das juristische Team nicht — sie sagt nur, welche Angaben sich von außen bestätigen ließen und welche nicht.

> Aus [`_VORLAGE.yaml`](../rules/_VORLAGE.yaml): *„Erfundene Fundstellen sind das Einzige, was uns wirklich schadet."*
> Deshalb hat diese Prüfung Vorrang vor allem anderen am Regelwerk.

---

## 1. Bestätigt

| Fundstelle | Prüfergebnis |
|---|---|
| **EuGH C-249/21 (Fuhrmann-2), 07.04.2022** — DP-002 | ✅ Aktenzeichen, Datum und Sachverhalt („Buchung abschließen") bestätigt. Rechtsgrundlage ist Art. 8 Abs. 2 UAbs. 2 RL 2011/83/EU, umgesetzt in § 312j BGB. **Bestätigt auch die entscheidende Aussage der Regel:** maßgeblich ist allein die Beschriftung der Schaltfläche, nicht die Begleitumstände |
| **EuGH C-673/17 (Planet49), 01.10.2019** — DP-001 | ✅ Vorangekreuztes Kästchen ist keine wirksame Einwilligung |
| **BGH I ZR 7/16 (Cookie-Einwilligung II), 28.05.2020** — DP-001 | ✅ Aktenzeichen, Datum und Bezeichnung bestätigt |
| **EuGH C-319/20 (Meta Platforms Ireland), 28.04.2022** — DP-001 | ✅ Verbandsklagebefugnis nach Art. 80 Abs. 2 DSGVO bestätigt. Klägerin war der vzbv |
| **EuGH C-21/23 (Lindenapotheke), 04.10.2024** — DP-001 | ✅ Existiert und sagt, was die Regel behauptet — **mit einer Einschränkung, siehe 3.1** |
| **OLG Köln, 19.01.2024, 6 U 80/23 (wetteronline)** — DP-001 | ✅ **Die stärkste Fundstelle im ganzen Regelwerk für unser Kernmuster.** Siehe 2 |
| **Anhang zu § 3 Abs. 3 UWG Nr. 7** — DP-003 | ✅ Wortlaut **wörtlich** mit `tatbestand_de` der Regel abgeglichen, stimmt Zeichen für Zeichen |
| **Anhang zu § 3 Abs. 3 UWG Nr. 20** — DP-005 | ✅ Existiert — **aber der zweite Halbsatz kippt unsere Bedingung, siehe 3.2** |

## 2. Ein Fund, der unser stärkstes Muster stützt

**OLG Köln, Urteil vom 19.01.2024, 6 U 80/23** (Verfahren einer Verbraucherzentrale gegen wetteronline.de) entscheidet fast punktgenau das, was DP-001 misst:

- ein Banner **ohne Ablehnoption auf der ersten Ebene**, das die Ablehnung auf eine zweite Ebene verlagert, führt **nicht** zu einer freiwilligen und informierten Einwilligung
- Zustimmung und Ablehnung müssen **auf derselben Ebene**, **gleich sichtbar**, **gleich groß** und sprachlich gleich verständlich angeboten werden
- die Ablehnung muss **ohne Umweg über Untermenüs** unmittelbar wählbar sein
- ein Verstoß gegen § 25 TTDSG/TDDDG i. V. m. Art. 7 DSGVO ist **über § 3a UWG lauterkeitsrechtlich durchsetzbar**

**Folgen für uns, drei:**

1. **Die Anspruchskette von DP-001 steht.** Der Weg § 25 TDDDG → § 3a UWG → § 8 UWG ist nicht nur Literaturmeinung, sondern von einem Oberlandesgericht in genau dieser Konstellation entschieden.
2. **Die Fundstelle gehört in `threshold_source`, nicht nur in eine Fußnote.** Sie steht bisher nur unter `offene_fragen_resolved`.
3. **Unsere Einstufung „Ablehnung nur über die zweite Ebene → `verdaechtig`" ist womöglich zu vorsichtig.** Das OLG hält genau diese Gestaltung für unwirksam. *Vorschlag zur Diskussion:* auf `eindeutig` anheben, wenn das juristische Team die Übertragbarkeit bejaht. Weil es eine OLG- und keine BGH-Entscheidung ist, entscheiden wir das nicht allein.

## 3. Zwei Präzisierungen

### 3.1 Lindenapotheke trägt die Verbandsklage nicht

C-21/23 betrifft die Klagebefugnis von **Mitbewerbern**, nicht von Verbraucherverbänden. In `offene_fragen_resolved` von DP-001 stützt die Antwort die Aussage *„Qualifizierte Verbraucherschutzeinrichtungen **bzw.** Wettbewerber können Verstöße geltend machen"* unter anderem auf diese Entscheidung.

Das Ergebnis stimmt, die Zuordnung ist unscharf. **Für uns — die Adressatin ist eine Verbraucherzentrale — sind C-319/20 (Meta) und § 8 Abs. 3 Nr. 3 UWG die tragenden Fundstellen.** Bitte im Text trennen. In der Fragerunde wäre das sonst ein leichter Treffer.

### 3.2 Die „gratis"-Bedingung war falsch — **eingebaut von der Technik, am selben Tag korrigiert**

Gestern wurde DP-005 um eine lauffähige Bedingung ergänzt:

```yaml
eindeutig:
  - "gratis_claim_present == true and shipping_cost_amount > 0"
```

Der Wortlaut des Anhangs Nr. 20 lautet im zweiten Halbsatz:

> *„dies gilt nicht für Kosten, die im Zusammenhang mit dem Eingehen auf das Waren- oder Dienstleistungsangebot oder **für die Abholung oder Lieferung der Ware** … unvermeidbar sind"*

**Versandkosten sind genau „Kosten für die Lieferung der Ware".** Sie fallen in die gesetzliche Ausnahme, sofern sie unvermeidbar sind — etwa weil keine kostenlose Abholung angeboten wird. Genau das misst niemand; das Signal dafür wurde als Rechtsbegriff abgelehnt.

Die Bedingung hätte also einen Verstoß behauptet, wo das Gesetz eine Ausnahme vorsieht — und hätte damit dem `tatbestand_de` derselben Regel widersprochen, der die Ausnahme ausdrücklich nennt. Dieselbe Fehlerart, die wir gestern in vier anderen Regeln beanstandet haben.

**Korrigiert:** auf `verdaechtig` heruntergestuft, die Ausnahme in der Begründung benannt, und die Frage nach der Unvermeidbarkeit in `menschliche_pruefung` eingetragen.

## 4. Nicht bestätigt — bitte prüfen oder streichen

| Fundstelle | Status |
|---|---|
| **BGH GRUR-RS 2025, 5877** („Folgeentscheidung zur Bestätigung", DP-001) | ⚠️ **Nicht auffindbar.** Es gibt BGH-Entscheidungen vom 27.03.2025 zur Cookie-Einwilligung, aber diese GRUR-RS-Fundstelle ließ sich nicht bestätigen. **Bitte in der GRUR-Datenbank verifizieren und ein Aktenzeichen ergänzen — oder streichen.** Eine Fundstelle ohne Aktenzeichen ist in einer Beweisakte wertlos und in der Fragerunde gefährlich |
| **BGH GRUR 2020, 896 Rn. 33 ff.** („App-Zentrum", DP-001) | 🟡 Die Entscheidung existiert (BGH I ZR 186/17, 28.05.2020, Facebook/App-Zentrum). Die **Seitenzahl und Randnummer** ließen sich nicht gegenprüfen. Bitte Aktenzeichen ergänzen |
| **OLG Köln GRUR-RR 2024, 341** | 🟡 Die Entscheidung ist bestätigt (6 U 80/23, 19.01.2024), die **Fundstelle in GRUR-RR** nicht. Bitte Aktenzeichen und Datum ergänzen — beides ist ohnehin aussagekräftiger als die Zeitschriftenfundstelle |
| **BeckOK UWG/Niebel/Bauer/Kerl, § 3a Rn. 70a (Stand 1.5.2026)** | 🟡 Kommentarliteratur, von außen nicht einsehbar. Bitte bestätigen, dass Randnummer und Bearbeiterstand stimmen |
| **EDPB Guidelines 03/2022 on Deceptive Design Patterns** | 🟡 Die Leitlinien existieren. Bitte prüfen, ob die **Fassung 2.0 (Februar 2023)** einschlägig ist — dann sollte sie zitiert werden |

> **Empfehlung zur Zitierweise:** Bei jeder Gerichtsentscheidung **Gericht, Datum und Aktenzeichen** angeben; die Zeitschriftenfundstelle nur ergänzend. Ein Aktenzeichen lässt sich von jedem nachprüfen, eine GRUR-RS-Nummer nicht.

## 5. Was nicht geprüft werden konnte

Die Subsumtion selbst. Ob die gewählten Schwellenwerte im Einzelfall tragen, ob die Anspruchsketten in einem konkreten Verfahren durchgehen und ob die Auswahl der Normen vollständig ist — das ist juristische Bewertung und gehört zum Team. Geprüft wurde ausschließlich: **existiert die zitierte Quelle, und sagt sie, was die Regel behauptet?**
