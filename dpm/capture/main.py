import os
import sys
import json
import asyncio
from datetime import datetime, timezone
from google import genai
from dpm.capture.agent import visual_explore
from dpm.capture.driver import LOCALE, TIMEZONE, USER_AGENT, VIEWPORT

async def walk(target_url, industry="unbekannt", output_root="out"):
    """Walk one target and write out/<run_id>/capture.json.

    Split out of main() so the web UI can start the same run the command
    line starts. Everything the two shared used to be copied.

    Returns the run folder.
    """
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    now = datetime.now(timezone.utc).astimezone().replace(microsecond=0)
    
    safe_url_name = target_url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
    run_id = f"{now.strftime('%Y-%m-%dT%H-%M-%S')}_{safe_url_name}"
    
    # out/<run_id>/, the folder `python -m dpm rebuild` looks in. Under
    # artifacts/ the run existed but no report was ever built from it: on
    # Tuesday the handover would have found an empty out/.
    artifacts_dir = os.path.join(str(output_root), run_id)
    os.makedirs(artifacts_dir, exist_ok=True)
    
    print(f"[*] Generating Evidence Dossier for {target_url}...")
    print(f"[*] All artifacts will be saved to: {artifacts_dir}")
    
    # Unified Step: Agent navigates AND audits simultaneously
    # agent.py returns: steps_log, reject_click_depth, final_step_name, is_blocked, signals, errors
    steps_log, reject_depth, final_step_name, is_blocked, signals, errors = await visual_explore(target_url, client, artifacts_dir)
    
    if is_blocked:
        print("[!] Exploration stopped early due to bot detection.")
    
    # Inject the rejection-specific click depth calculated by the agent's logic
    # NOT published as reject_click_depth: the counter counts every funnel
    # click, but the signal means "interaction steps until consent is fully
    # refused" and DP-001 judges on it. A miscounted value here produced a
    # confident false accusation (amazon, 23.08.). Until the reject path is
    # actually walked, the honest answer is a gap.
    errors.setdefault("reject_click_depth",
                      "requires clicking through the reject path — the agent "
                      f"made {reject_depth} funnel clicks, which is not the "
                      "same measurement")
    
    # Final error pruning: If a signal was found at ANY step, remove it from errors
    final_errors = {k: v for k, v in errors.items() if k not in signals}
    
    # Construct the final JSON schema
    capture_data = {
        "meta": {
            "target": safe_url_name,
            "start_url": target_url,
            "timestamp": now.isoformat(),
            # Written from the same constants the browser was opened with,
            # not typed out again -- these four lines are what makes a
            # capture reproducible, and a copy drifts from the original.
            "viewport": dict(VIEWPORT),
            "locale": LOCALE,
            "timezone": TIMEZONE,
            "user_agent": USER_AGENT,
            "capture_mode": "headless",
            "industry": industry,
            "run_id": run_id,
            "is_blocked": is_blocked
        },
        "steps": steps_log,
        "signals": signals,
        "signal_errors": final_errors
    }
    
    capture_path = os.path.join(artifacts_dir, "capture.json")
    with open(capture_path, "w", encoding="utf-8") as f:
        json.dump(capture_data, f, ensure_ascii=False, indent=2)
        
    print(f"[*] Evidence Dossier successfully locked and saved to {capture_path}.")
    return artifacts_dir


async def main():
    if len(sys.argv) < 2:
        print("Usage: python -m dpm.capture.main <target_url> [branche]")
        sys.exit(1)

    if "GEMINI_API_KEY" not in os.environ:
        print("[!] Error: GEMINI_API_KEY environment variable is missing.")
        sys.exit(1)

    # Without a branch there is no statistic by branch in the
    # Marktuebersicht, and that is what the consumer agency asked for in
    # the seminar. Unset is written as "unbekannt", never guessed.
    await walk(sys.argv[1],
               sys.argv[2] if len(sys.argv) > 2 else "unbekannt")


if __name__ == "__main__":
    asyncio.run(main())
