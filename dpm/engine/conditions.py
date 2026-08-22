"""Condition parser for rules/*.yaml — without eval().

Supports exactly what rules/_VORLAGE.yaml promises the legal team:

    comparison   == != > >= < <=
    connective   and   or          (and binds tighter)
    arithmetic   accept_button_area_px2 / reject_button_area_px2 > 2.0
                 accept_contrast_ratio - reject_contrast_ratio > 3.0
    lists        kuendigungsbutton_label not in zulaessige_labels
                 order_button_label not_in_whitelist ["a", "b"]
    free text    countdown_text contains_any sitzungs_woerter
                 countdown_text not_contains_any sitzungs_woerter

Why no eval(): a file written by the legal team must never be executed as
program code. And a typo should produce a readable message, not a crash.

Three-valued logic. A missing signal does not automatically make a
condition unevaluable:

    a and b   is false as soon as one part is false — even if another
              part was never measured
    a or b    is true as soon as one part is true — likewise

MissingSignal is raised only when the result genuinely depends on the
value we do not have. That is not convenience but precision: we should
say "unresolved" only where we really do not know.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_COMPARISON = re.compile(r"(>=|<=|==|!=|>|<)")
_LIST_OP_INLINE = re.compile(r"\b(not_in_[a-z_]+|in_[a-z_]+)\b")
_LIST_OP_NAMED = re.compile(
    r"^([a-zA-Z_][a-zA-Z0-9_]*)\s+(not\s+in|in)\s+([a-zA-Z_][a-zA-Z0-9_]*)$")
# Free-text signals cannot be compared for equality: countdown_text reads
# "Angebot endet in 14:59", never exactly one of our list entries. These two
# ask whether ANY listed word occurs IN the text.
_CONTAINS_NAMED = re.compile(
    r"^([a-zA-Z_][a-zA-Z0-9_]*)\s+(not_contains_any|contains_any)"
    r"\s+([a-zA-Z_][a-zA-Z0-9_]*)$")
_NUMBER = re.compile(r"^-?\d+(\.\d+)?$")
# Look like an identifier but are not signal names.
_LITERALS = ("true", "True", "false", "False")
_IDENTIFIER = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

# Arithmetic only with surrounding spaces. Otherwise "-1" could not be told
# apart from a subtraction.
_ARITHMETIC = {"/": lambda a, b: a / b, "-": lambda a, b: a - b,
               "+": lambda a, b: a + b, "*": lambda a, b: a * b}


class MissingSignal(Exception):
    """A required signal was not captured -> verdict level "unklar"."""

    def __init__(self, name: str, reason: str | None = None):
        self.name = name
        self.reason = reason
        super().__init__(f"signal '{name}' not captured"
                         + (f": {reason}" if reason else ""))


class RuleSyntaxError(Exception):
    """The condition in the rulebook cannot be read. A rulebook defect."""


@dataclass
class SignalTable:
    """Measured values of one capture run, with their provenance.

    values     signal name -> {"value", "step", "evidence"}
    errors     signal name -> why it could not be measured
    confirmed  signal names a human confirmed in the target profile (C4)
    """

    values: dict
    errors: dict = field(default_factory=dict)
    confirmed: set = field(default_factory=set)

    def get(self, name: str):
        if name in self.values:
            return self.values[name]["value"]
        if name in self.errors:
            raise MissingSignal(name, self.errors[name])
        raise MissingSignal(name, "not contained in the capture")

    def evidence(self, name: str) -> dict | None:
        entry = self.values.get(name)
        if not entry:
            return None
        return {"signal": name,
                "value": entry["value"],
                "step": entry.get("step"),
                "evidence": entry.get("evidence")}


@dataclass
class Evaluation:
    is_true: bool
    signals_used: list


def evaluate(condition: str, table: SignalTable,
             lists: dict | None = None) -> Evaluation:
    """Evaluate one condition. May raise MissingSignal or RuleSyntaxError."""
    used: list = []
    result = _disjunction(_normalise(condition), table, lists or {}, used)
    return Evaluation(is_true=result, signals_used=used)


# --- connectives, three-valued -------------------------------------------

def _disjunction(text: str, table, lists, used) -> bool:
    results, missing = _branches(_split(text, "or"),
                                 lambda t: _conjunction(t, table, lists, used))
    if any(results):
        return True
    if missing:
        raise missing[0]
    return False


def _conjunction(text: str, table, lists, used) -> bool:
    results, missing = _branches(_split(text, "and"),
                                 lambda t: _atom(t, table, lists, used))
    if not all(results):
        return False
    if missing:
        raise missing[0]
    return True


def _branches(parts: list, evaluator):
    results, missing = [], []
    for part in parts:
        try:
            results.append(evaluator(part))
        except MissingSignal as error:
            missing.append(error)
    return results, missing


def _normalise(condition: str) -> str:
    """Unify the spellings that actually occur in the rule files.

    DP-005 writes conditions as a YAML folded block, so the value arrives
    with quotes and line breaks. This absorbs that, so the legal team does
    not have to change how it writes.
    """
    text = " ".join(str(condition).split())
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1].strip()
    return text


def _split(text: str, keyword: str) -> list:
    """Split at ' and ' / ' or ', but not inside [] or quotes."""
    parts, buffer, depth, quote = [], [], 0, None
    for word in text.split(" "):
        if word == keyword and depth == 0 and quote is None:
            parts.append(" ".join(buffer))
            buffer = []
            continue
        for char in word:
            if quote:
                if char == quote:
                    quote = None
            elif char in "\"'":
                quote = char
            elif char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
        buffer.append(word)
    parts.append(" ".join(buffer))
    return [p.strip() for p in parts if p.strip()]


# --- single condition ----------------------------------------------------

def _atom(text: str, table, lists, used) -> bool:
    contains = _CONTAINS_NAMED.match(text)
    if contains:
        return _contains(contains.group(1),
                         contains.group(2).startswith("not_"),
                         _named_list(contains.group(3), lists, text),
                         table, used)

    named = _LIST_OP_NAMED.match(text)
    if named:
        return _membership(named.group(1), named.group(2).startswith("not"),
                           _named_list(named.group(3), lists, text),
                           table, used)

    inline = _LIST_OP_INLINE.search(text)
    if inline and "[" in text:
        return _membership(text[:inline.start()].strip(),
                           inline.group(1).startswith("not_"),
                           _inline_list(text, inline), table, used)

    match = _COMPARISON.search(text)
    if not match:
        raise RuleSyntaxError(f"no comparison operator in condition: {text!r}")

    operator = match.group(1)
    left, right = text[:match.start()].strip(), text[match.end():].strip()
    a = _operand(left, table, lists, used)
    b = _operand(right, table, lists, used)

    if operator == "==":
        return a == b
    if operator == "!=":
        return a != b

    _need_numbers(((left, a), (right, b)),
                  f"operator '{operator}' needs numbers, got {a!r} and {b!r} "
                  f"in: {text!r}",
                  f"the rule compares it with '{operator}'")
    return {">": a > b, ">=": a >= b, "<": a < b, "<=": a <= b}[operator]


def _need_numbers(operands, rule_defect: str, signal_defect: str) -> None:
    """Both operands have to be numbers. Whose defect is it if one is not?

    At runtime a malformed rule and a mismeasured signal look the same, so
    the literal side decides:

        banner_detected > true    nonsense whatever was measured -> the rule
        scarcity_value > 0        a sound rule that got False    -> the signal

    The distinction is not cosmetic. A signal we cannot read means we do not
    know, so the finding is "unklar" and names the signal. Calling that a
    Regelwerksfehler sends the legal team looking for a mistake they did not
    make -- which is what happened with the capture of 22.08., where
    scarcity_value arrived as false and DP-003 was reported as broken.
    """
    def is_number(value) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def is_signal(source: str) -> bool:
        return bool(_IDENTIFIER.match(source)) and source not in _LITERALS

    for source, value in operands:              # the rule's own text first
        if not is_number(value) and not is_signal(source):
            raise RuleSyntaxError(rule_defect)
    for source, value in operands:
        if not is_number(value):
            raise MissingSignal(source, f"value {value!r} is not a number, "
                                        f"but {signal_defect}")


def _named_list(name: str, lists: dict, text: str) -> list:
    if name not in (lists or {}):
        raise RuleSyntaxError(
            f"the rule refers to the list '{name}', which is not defined "
            f"under 'listen:'. Condition: {text!r}")
    return [str(e) for e in lists[name]]


def _inline_list(text: str, inline) -> list:
    start, end = text.find("[", inline.end()), text.rfind("]")
    if start == -1 or end == -1:
        raise RuleSyntaxError(f"list not readable in: {text!r}")
    return [_unquote(e) for e in
            re.split(r",(?=(?:[^\"']*[\"'][^\"']*[\"'])*[^\"']*$)",
                     text[start + 1:end]) if e.strip()]


def _membership(signal_name: str, negated: bool, entries: list,
                table, used) -> bool:
    """Membership in a word list.

    Compared case-insensitively and with whitespace collapsed: § 312j BGB
    is about the wording, not the typography. Which list is meant (white,
    grey, positive) does not matter for evaluation — the name only
    documents what it stands for legally.
    """
    value = _operand(signal_name, table, {}, used)
    contained = _fold(value) in {_fold(e) for e in entries}
    return not contained if negated else contained


# Trailing punctuation and decoration are not part of the wording.
_DECORATION = " \t\n.,;:!?…\"'»«*→>-"


def _contains(signal_name: str, negated: bool, entries: list,
              table, used) -> bool:
    """Does any listed word occur in the free text of the signal?

    Substring, case-insensitive, whitespace collapsed. Needed because a
    countdown caption is free text — matching it for equality against a
    list would never hit. Whether the caption claims a limited AVAILABILITY
    or merely announces a session timeout is exactly the distinction
    Anhang Nr. 7 turns on, and it cannot be made without reading the words.
    """
    text = _fold(_operand(signal_name, table, {}, used))
    hit = any(_fold(e) in text for e in entries if str(e).strip())
    return not hit if negated else hit


def _fold(value) -> str:
    """Normalise a label for comparison against a word list.

    § 312j Abs. 3 BGB is about the wording of the button, not its
    typography. "Jetzt kaufen!" and "jetzt kaufen" are the same wording;
    treating the exclamation mark as a violation would be a false alarm we
    could not defend (EuGH C-249/21, Fuhrmann-2, turns on the label alone).
    """
    return " ".join(str(value).split()).strip(_DECORATION).casefold()


def _unquote(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1]
    return text.strip()


def _operand(raw: str, table, lists, used):
    """Resolve one operand: arithmetic, number, boolean, string, signal."""
    text = raw.strip()

    parts = text.split(" ")
    if len(parts) == 3 and parts[1] in _ARITHMETIC:
        left = _operand(parts[0], table, lists, used)
        right = _operand(parts[2], table, lists, used)
        _need_numbers(((parts[0], left), (parts[2], right)),
                      f"arithmetic needs numbers: {text!r}",
                      "the rule calculates with it")
        if parts[1] == "/" and right == 0:
            # Division by zero is not a statement, it is a measurement gap.
            raise MissingSignal(parts[2], "value 0, ratio cannot be formed")
        return _ARITHMETIC[parts[1]](left, right)

    if text in ("true", "True"):
        return True
    if text in ("false", "False"):
        return False
    if _NUMBER.match(text):
        return float(text) if "." in text else int(text)
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]

    if not _IDENTIFIER.match(text):
        raise RuleSyntaxError(f"not a valid signal name: {text!r}")

    if text not in used:
        used.append(text)
    return table.get(text)
