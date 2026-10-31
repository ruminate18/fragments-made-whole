"""Generate two reconstructions for every fragment in cases.json through the course's Prodia proxy.

For each case:
  uninformed  - the same one-line "restore this" prompt for every object
  evidence    - a prompt written only from the museum record and published scholarship

Usage:
  python3 generate.py --draft 291843     # one cheap FLUX.2 Klein test ($0.004) into work/drafts/
  python3 generate.py                    # final images with the model in cases.json
  python3 generate.py 291843 215515      # only these objects

The key is read from PRODIA_PROXY_KEY (environment or .env) and is never printed.
Results are saved to docs/img/gen/<id>-<variant>.jpg and skipped on later runs,
so a rerun never pays twice. Every charge is appended to costs.json.
"""
import io
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROXY = "https://prodia-proxy.vercel.app/v2/job"
FRAGMENTS = os.path.join(HERE, "docs", "img", "fragments")
OUT = os.path.join(HERE, "docs", "img", "gen")
DRAFTS = os.path.join(HERE, "work", "drafts")
COSTS = os.path.join(HERE, "costs.json")
DRAFT_MODEL = "inference.flux-2.klein.4b.img2img.v1"


def load_key():
    key = os.environ.get("PRODIA_PROXY_KEY", "").strip()
    env = os.path.join(HERE, ".env")
    if not key and os.path.exists(env):
        for line in open(env):
            name, _, value = line.partition("=")
            if name.strip() == "PRODIA_PROXY_KEY":
                key = value.strip().strip("'\"")
    if not key or "XXXX" in key:
        sys.exit("No Prodia key found. Put PRODIA_PROXY_KEY='...' in .env (see .env.example).")
    return key


def input_jpeg(oid):
    """The fragment photo, shrunk to fit 1024 x 1024 and sent as JPEG (proxy limits)."""
    im = Image.open(os.path.join(FRAGMENTS, f"{oid}.jpg")).convert("RGB")
    im.thumbnail((1024, 1024), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    return buf.getvalue()


def run_job(key, job_type, prompt, image_bytes):
    config = {"prompt": prompt, "images": ["fragment.jpg"]}
    if "gemini" in job_type:
        config["resolution"] = "1K"
    job = {"type": job_type, "config": config}
    for attempt in range(4):
        res = requests.post(
            PROXY,
            headers={"Authorization": "Bearer " + key, "Accept": "image/jpeg"},
            files={"job": (None, json.dumps(job), "application/json"),
                   "input": ("fragment.jpg", image_bytes, "image/jpeg")},
            timeout=300,
        )
        if res.status_code == 429:
            wait = int(res.headers.get("retry-after", 20))
            print(f"    Prodia busy, waiting {wait}s")
            time.sleep(wait)
            continue
        if not res.ok:
            raise RuntimeError(f"{res.status_code}: {res.text[:300]}")
        return res.content, float(res.headers.get("x-proxy-charged-dollars", 0)), float(res.headers.get("x-proxy-spent-dollars", 0))
    raise RuntimeError("Prodia stayed busy; try again later")


def log_cost(entry):
    log = json.load(open(COSTS)) if os.path.exists(COSTS) else []
    log.append(entry)
    json.dump(log, open(COSTS, "w"), indent=1)


def main():
    args = sys.argv[1:]
    draft = "--draft" in args
    only = {int(a) for a in args if a.isdigit()}
    spec = json.load(open(os.path.join(HERE, "cases.json")))
    model = DRAFT_MODEL if draft else spec["model"]
    out_dir = DRAFTS if draft else OUT
    os.makedirs(out_dir, exist_ok=True)
    key = load_key()
    total = 0.0
    for case in spec["cases"]:
        if only and case["id"] not in only:
            continue
        image = input_jpeg(case["id"])
        for variant, prompt in (("uninformed", spec["uninformed_prompt"]), ("evidence", case["prompt"])):
            path = os.path.join(out_dir, f"{case['id']}-{variant}.jpg")
            if os.path.exists(path):
                print(f"  {case['slug']} {variant}: already made, skipping")
                continue
            print(f"  {case['slug']} {variant}: generating with {model}", flush=True)
            t0 = time.time()
            data, charged, spent = run_job(key, model, prompt, image)
            with open(path, "wb") as f:
                f.write(data)
            total += charged
            log_cost({"when": datetime.now(timezone.utc).isoformat(timespec="seconds"), "object": case["id"],
                      "variant": variant, "model": model, "charged": charged, "spent_total": spent, "draft": draft})
            print(f"    saved {os.path.relpath(path, HERE)} ({time.time() - t0:.0f}s, ${charged:.3f}; course total spent ${spent:.2f})")
            if draft:
                return  # a draft run is one image, to test the pipeline cheaply
    print(f"done; this run cost ${total:.3f}")


if __name__ == "__main__":
    main()
