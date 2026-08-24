import os
import sys
import json
import asyncio
from datetime import datetime, timezone
from google import genai
from agent import visual_explore

async def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <target_url>")
        sys.exit(1)
        
    target_url = sys.argv[1]
    
    if "GEMINI_API_KEY" not in os.environ:
        print("[!] Error: GEMINI_API_KEY environment variable is missing.")
        sys.exit(1)
        
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    now = datetime.now(timezone.utc).astimezone().replace(microsecond=0)
    
    safe_url_name = target_url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
    run_id = f"{now.strftime('%Y-%m-%dT%H-%M-%S')}_{safe_url_name}"
    
    # Create artifacts directory
    artifacts_dir = os.path.join("artifacts", run_id)
    os.makedirs(artifacts_dir, exist_ok=True)
    
    print(f"[*] Generating Evidence Dossier for {target_url}...")
    print(f"[*] All artifacts will be saved to: {artifacts_dir}")
    
    # Unified Step: Agent navigates AND audits simultaneously
    # agent.py returns: steps_log, reject_click_depth, final_step_name, is_blocked, signals, errors
    steps_log, reject_depth, final_step_name, is_blocked, signals, errors = await visual_explore(target_url, client, artifacts_dir)
    
    if is_blocked:
        print("[!] Exploration stopped early due to bot detection.")
    
    # Inject the rejection-specific click depth calculated by the agent's logic
    signals["reject_click_depth"] = {
        "value": reject_depth,
        "step": steps_log[0]["step"] if steps_log else "start",
        "evidence": steps_log[0]["screenshot"] if steps_log else ""
    }
    
    # Final error pruning: If a signal was found at ANY step, remove it from errors
    final_errors = {k: v for k, v in errors.items() if k not in signals}
    
    # Construct the final JSON schema
    capture_data = {
        "meta": {
            "target": safe_url_name,
            "start_url": target_url,
            "timestamp": now.isoformat(),
            "viewport": { "width": 1440, "height": 900 },
            "locale": "en-US",
            "timezone": "Europe/Berlin",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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

if __name__ == "__main__":
    asyncio.run(main())
