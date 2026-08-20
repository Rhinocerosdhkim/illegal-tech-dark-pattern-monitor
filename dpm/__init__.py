"""Dark Pattern Monitor — evidence gathering and structuring.

Directories:
    dpm/capture/   capture layer (Karthik)
    dpm/signals/   signal measurement (Karthik)
    dpm/engine/    evaluate the rulebook (Donghyun)
    dpm/report/    Beweisakte, market overview, timeline (Donghyun)
    dpm/ui/        the three views (Donghyun)
    dpm/ai/        the four model call sites — and nowhere else

Language convention: code, tests, capture.json and data/targets/*.yaml are
English, because the capture layer is written by an English-speaking
partner. The rulebook (rules/*.yaml) and the rendered Beweisakte stay
German — they are written by German lawyers and read by a German consumer
protection agency.
"""

# Appears verbatim in every Beweisakte. Provisionally fixed on 20.08.2026;
# final decision still open (docs/ABSTIMMUNG_Regelwerk.md C1).
PRODUCT_NAME = "PatternWatch"
