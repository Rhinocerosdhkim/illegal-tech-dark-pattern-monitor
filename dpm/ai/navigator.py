"""AI 3 -- path navigation.

Shown a screenshot with numbered boxes drawn over the clickable elements
(Set-of-Mark), the model answers which box leads further along the funnel.
It decides where to click. It never decides a finding.

Its reasoning is kept and written to capture.json. If a human cannot check
afterwards why the tool clicked what it clicked, the path is not usable as
evidence (ARBEITSTEILUNG_Technik.md 2.9).
"""

from __future__ import annotations

from dataclasses import dataclass

from .client import Model, ModelError

_PROMPT = """You are walking through an online shop to reach the order page.

The screenshot has red numbered boxes over the clickable elements.

Answer with:
  step         which step of the path this page is, one of: {steps}
               -- or "{off_path}" if the page is none of them: a login or
               registration wall, a captcha, an age gate, an error page, or
               any interstitial that is not part of buying a product.
  target_id    the number of the box that leads one step further, or null
               if nothing does
  goal_reached true only if this is the final order page
  reason       one sentence, in English, on why you chose that box

Pick the box that moves towards buying a product. Ignore boxes that only
lead to help pages, language switches or social media.

Say "{off_path}" whenever it fits, and do not force the page into one of
the path steps because it is the closest of the five. Nothing measured on
such a page is recorded, so a wrong label there turns into a statement
about a shop that was never examined."""


def _schema(steps, off_path: str) -> dict:
    return {
        "type": "object",
        "properties": {
            "step": {"type": "string", "enum": list(steps) + [off_path]},
            "target_id": {"type": "integer", "nullable": True},
            "goal_reached": {"type": "boolean"},
            "reason": {"type": "string"},
        },
        "required": ["step", "goal_reached", "reason"],
    }


@dataclass
class Decision:
    step: str
    target_id: int | None
    goal_reached: bool
    reason: str


async def decide(model: Model, screenshot: bytes, steps,
                 off_path: str) -> Decision:
    """One navigation decision. Raises ModelError if it cannot be read.

    `off_path` is the answer for a page that is on none of the steps. It is
    a required argument rather than a default so that no caller can take
    the escape hatch away by forgetting it: without one, the model has to
    name a path step for a login wall, and whatever is measured there
    becomes a fact about that step.
    """
    allowed = list(steps) + [off_path]
    answer = await model.ask(
        _PROMPT.format(steps=", ".join(steps), off_path=off_path),
        schema=_schema(steps, off_path), screenshot=screenshot)

    step = answer.get("step")
    if step not in allowed:
        raise ModelError(f"unknown step name {step!r}")

    target = answer.get("target_id")
    if target is not None and not isinstance(target, int):
        raise ModelError(f"target_id was {target!r}, not a number")

    return Decision(step=step, target_id=target,
                    goal_reached=bool(answer.get("goal_reached")),
                    reason=str(answer.get("reason") or ""))
