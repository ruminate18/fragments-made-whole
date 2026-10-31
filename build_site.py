"""Build docs/index.html (static, for GitHub Pages) from cases.json, analysis.json and the museum records.

    python3 build_site.py
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "docs")
e = html.escape


def load(name, default=None):
    path = os.path.join(HERE, name)
    return json.load(open(path)) if os.path.exists(path) else default


def figure(src, caption, cls, alt):
    exists = os.path.exists(os.path.join(SITE, src))
    img = (f'<button class="zoom" data-full="{e(src)}" aria-label="Enlarge: {e(alt)}"><img src="{e(src)}" alt="{e(alt)}" loading="lazy"></button>'
           if exists else '<div class="pending">Not generated yet</div>')
    return f'<figure class="{cls}">{img}<figcaption>{caption}</figcaption></figure>'


def case_html(n, case, rec, an, spec):
    oid = case["id"]
    tomb = " · ".join(x for x in [rec.get("culture"), rec.get("dated")] if x)
    ev = "".join(f"<li>{e(x)}</li>" for x in case["evidence"])
    right = "".join(f"<li>{e(x)}</li>" for x in an.get("supported", []))
    wrong = "".join(f"<li>{e(x)}</li>" for x in an.get("invented", []))
    naive = "".join(f"<li>{e(x)}</li>" for x in an.get("uninformed", []))
    analysis = ""
    if an:
        analysis = f"""
        <div class="reading">
          <div><h4>The uninformed guess</h4><ul>{naive}</ul></div>
          <div><h4 class="ok">What the evidence supports</h4><ul>{right}</ul></div>
          <div><h4 class="bad">What the machine invented</h4><ul>{wrong}</ul></div>
        </div>
        <p class="verdict"><b>Verdict.</b> {e(an.get("verdict", ""))}</p>"""
    return f"""
  <article class="case" id="{e(case['slug'])}">
    <header class="case-head">
      <div class="case-num">{n:02d}</div>
      <div class="case-title">
        <span class="loss">{e(case['loss'])}</span>
        <h3>{e(rec['title'])}</h3>
        <p class="tomb">{e(tomb)} · <a href="{e(rec['url'])}" target="_blank" rel="noopener">Harvard Art Museums {e(rec['objectnumber'])}</a></p>
      </div>
    </header>
    <div class="triptych">
      {figure(f"img/fragments/{oid}.jpg", "<b>What survives.</b> Museum photograph.", "frag", rec['title'])}
      {figure(f"img/gen/{oid}-uninformed.jpg", "<b>Uninformed.</b> “Restore this damaged artwork…”", "gen", "AI reconstruction from a generic prompt")}
      {figure(f"img/gen/{oid}-evidence.jpg", "<b>Evidence-led.</b> Prompt built from the record.", "gen", "AI reconstruction from an evidence-based prompt")}
    </div>
    <div class="case-body">
      <div class="evidence"><h4>The evidence</h4><ul>{ev}</ul>
        <details><summary>Read the evidence-led prompt</summary><p class="prompt">{e(case['prompt'])}</p></details>
      </div>
      {analysis}
    </div>
  </article>"""


def main():
    spec = load("cases.json")
    recs = {r["id"]: r for r in load("data/records.json")["records"]}
    analysis = load("analysis.json", {})
    costs = load("costs.json", [])
    spent = sum(c["charged"] for c in costs)
    finals = [c for c in costs if not c.get("draft")]
    toc = "".join(f'<li><a href="#{e(c["slug"])}"><span>{i:02d}</span>{e(c["short"])}<em>{e(c["loss"])}</em></a></li>'
                  for i, c in enumerate(spec["cases"], 1))
    cases = "".join(case_html(i, c, recs[c["id"]], analysis.get(str(c["id"]), {}), spec) for i, c in enumerate(spec["cases"], 1))
    findings = analysis.get("_findings", [])
    findings_html = "".join(f"<li>{f}</li>" for f in findings)
    page = open(os.path.join(HERE, "template.html")).read()
    page = (page.replace("{{TOC}}", toc).replace("{{CASES}}", cases).replace("{{FINDINGS}}", findings_html)
                .replace("{{N_IMAGES}}", str(len(finals))).replace("{{SPENT}}", f"${spent:.2f}")
                .replace("{{UNINFORMED}}", e(spec["uninformed_prompt"])))
    open(os.path.join(SITE, "index.html"), "w").write(page)
    print(f"built docs/index.html: {len(spec['cases'])} cases, {len(finals)} generated images, ${spent:.2f} spent")


if __name__ == "__main__":
    main()
