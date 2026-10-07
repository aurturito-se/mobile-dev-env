#!/opt/venv/bin/python
"""webqa : QA web multi-navigateur/viewport. Usage:
webqa.py URL [URL...] [--browsers chromium,firefox,webkit] [--viewports desktop,mobile] [--out DIR] [--no-axe] [--expect TEXT]
Sortie : DIR/report.json + report.md + captures PNG. Code retour 1 si échec (HTTP>=400, erreur console/JS, requête échouée, violation axe critical/serious, texte attendu absent)."""
import argparse, json, os, re, sys, time
from playwright.sync_api import sync_playwright
AXE = os.popen("npm root -g").read().strip() + "/axe-core/axe.min.js"
VIEWPORTS = {"desktop": {"viewport": {"width": 1366, "height": 768}},
             "tablet": {"viewport": {"width": 820, "height": 1180}},
             "mobile": {"viewport": {"width": 390, "height": 844}, "is_mobile": True, "has_touch": True, "device_scale_factor": 2}}

def main():
    a = argparse.ArgumentParser()
    a.add_argument("urls", nargs="+"); a.add_argument("--browsers", default="chromium")
    a.add_argument("--viewports", default="desktop,mobile"); a.add_argument("--out", default="/workspace/qa-report")
    a.add_argument("--no-axe", action="store_true"); a.add_argument("--expect", action="append", default=[])
    a.add_argument("--wait", type=float, default=1.0)
    o = a.parse_args(); os.makedirs(o.out, exist_ok=True)
    res = []; fail = False
    with sync_playwright() as p:
        for bn in o.browsers.split(","):
            try: br = getattr(p, bn).launch(headless=True, args=["--no-sandbox"] if bn == "chromium" else [])
            except Exception as e:
                res.append({"browser": bn, "error": f"launch: {str(e)[:200]}"}); fail = True; continue
            for vn in o.viewports.split(","):
                for url in o.urls:
                    ctx = br.new_context(ignore_https_errors=True, **VIEWPORTS[vn]); pg = ctx.new_page()
                    cons, failed = [], []
                    pg.on("console", lambda m, c=cons: c.append(m.text[:200]) if m.type == "error" else None)
                    pg.on("pageerror", lambda e, c=cons: c.append("pageerror: " + str(e)[:200]))
                    pg.on("requestfailed", lambda r, f=failed: f.append(f"{r.url[:120]} {r.failure}"))
                    r = {"browser": bn, "viewport": vn, "url": url}
                    try:
                        t = time.time(); resp = pg.goto(url, wait_until="networkidle", timeout=30000)
                        r["status"] = resp.status if resp else None; r["load_s"] = round(time.time() - t, 2)
                        pg.wait_for_timeout(int(o.wait * 1000))
                        r["title"] = pg.title()
                        r["h_overflow"] = pg.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
                        slug = re.sub(r"\W+", "_", url)[-50:]
                        shot = f"{o.out}/{bn}_{vn}_{slug}.png"; pg.screenshot(path=shot, full_page=True); r["screenshot"] = shot
                        body = pg.inner_text("body")
                        r["missing_text"] = [x for x in o.expect if x not in body]
                        if not o.no_axe and os.path.exists(AXE):
                            pg.add_script_tag(path=AXE)
                            ax = pg.evaluate("axe.run().then(x=>x.violations.map(v=>({id:v.id,impact:v.impact,n:v.nodes.length})))")
                            r["axe"] = ax
                        r["console_errors"] = cons[:10]; r["failed_requests"] = failed[:10]
                        bad = (r["status"] or 0) >= 400 or cons or failed or r["missing_text"] or any(v["impact"] in ("critical", "serious") for v in r.get("axe", []))
                        r["ok"] = not bad
                    except Exception as e:
                        r["error"] = str(e)[:200]; r["ok"] = False
                    fail |= not r["ok"]; res.append(r); ctx.close()
            br.close()
    json.dump(res, open(f"{o.out}/report.json", "w"), indent=1)
    md = ["# Rapport QA web", ""]
    for r in res:
        md.append(f"- {'OK' if r.get('ok') else 'KO'} {r.get('browser')}/{r.get('viewport','-')} {r.get('url','')} status={r.get('status')} load={r.get('load_s')}s overflow={r.get('h_overflow')} console={len(r.get('console_errors',[]))} failed_req={len(r.get('failed_requests',[]))} axe={[(v['id'],v['impact']) for v in r.get('axe',[])]} {r.get('error','')}")
    open(f"{o.out}/report.md", "w").write("\n".join(md)); print("\n".join(md)); print("VERDICT:", "FAIL" if fail else "PASS")
    sys.exit(1 if fail else 0)
main()
