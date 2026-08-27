import os
import sys
import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from dpm.ai.client import Model
from dpm.capture.agent import (LOCALE, STRUCTURAL_GAPS, TIMEZONE,
                                USER_AGENT, VIEWPORT, visual_explore, Capture)

async def walk(target_url, industry="unbekannt", output_root="out", username=None, password=None):
    """Walk one target and write out/<run_id>/capture.json.

    Split out of main() so the web UI can start the same run the command
    line starts. Everything the two shared used to be copied.

    Returns the run folder.
    """
    model = Model.open()
    now = datetime.now(timezone.utc).astimezone().replace(microsecond=0)
    
    # Unified Step: Agent navigates AND audits simultaneously
    # agent.py returns: steps_log, reject_depth, final_step_name, is_blocked, signals, errors, meta
    steps_log, reject_depth, final_step_name, is_blocked, signals, errors, meta = \
        await visual_explore(target_url, model, output_root=output_root,
                             username=username, password=password)
    
    if is_blocked:
        print("[!] Exploration stopped early due to bot detection.")
    
    # Inject the rejection-specific click depth calculated by the agent's logic
    for name, reason in STRUCTURAL_GAPS.items():
        if name not in signals:
            errors[name] = reason
    errors["reject_click_depth"] = (
        f"{STRUCTURAL_GAPS['reject_click_depth']} — der Agent hat "
        f"{reject_depth} Trichterklicks gemacht, was nicht dieselbe "
        f"Messung ist")
    
    # Final error pruning: If a signal was found at ANY step, remove it from errors
    final_errors = {k: v for k, v in errors.items() if k not in signals}

    if industry:
        meta["industry"] = industry
    
    # Construct the final Capture object and write it
    run = Capture(path=Path(output_root) / meta["run_id"], meta=meta,
                  steps=steps_log, signals=signals, errors=final_errors)
    capture_path = run.write()
        
    print(f"[*] Evidence Dossier successfully locked and saved to {capture_path}.")
    return run.path


async def main():
    if len(sys.argv) < 2:
        print("Usage: python -m dpm.capture.main <target_url> [branche] [username] [password]")
        sys.exit(1)

    # Check availability through the engine check
    from dpm.ai.client import unavailable
    reason = unavailable()
    if reason:
        print(f"[!] Warning: {reason}")
        print("[*] Proceeding with Surface Capture (start page only)...")

    await walk(sys.argv[1],
               industry=sys.argv[2] if len(sys.argv) > 2 else "unbekannt",
               username=sys.argv[3] if len(sys.argv) > 3 else None,
               password=sys.argv[4] if len(sys.argv) > 4 else None)


if __name__ == "__main__":
    asyncio.run(main())
