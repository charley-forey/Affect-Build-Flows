"""Generate resources/ramp/endpoints-cheatsheet.md from developer-api.json.

Everything below is read out of the spec — nothing is hand-written per endpoint.
Run via refresh.sh, or: python gen-cheatsheet.py

Writes the file itself rather than printing — stdout is cp1252 on Windows and
would mangle every em-dash.
"""
import json
import collections
import datetime

METHODS = ("get", "post", "put", "patch", "delete")
spec = json.load(open("developer-api.json", encoding="utf-8"))

tag_desc = {t["name"]: t.get("description", "") for t in spec.get("tags", [])}
scope_desc = spec["components"]["securitySchemes"]["oauth2"]["flows"]["authorizationCode"]["scopes"]

ops = []
for path, item in spec["paths"].items():
    for method, op in item.items():
        if method not in METHODS:
            continue
        scopes = sorted({s for sec in op.get("security", []) for v in sec.values() for s in v})
        flags = []
        if op.get("deprecated"):
            flags.append("**deprecated**")
        if op.get("x-ramp-plus-required"):
            flags.append("Plus")
        if op.get("x-beta"):
            flags.append("beta")
        if op.get("x-destructive"):
            flags.append("destructive")
        ops.append({
            "tag": (op.get("tags") or ["Untagged"])[0],
            "method": method.upper(),
            "path": path,
            "summary": op.get("summary", op["operationId"]),
            "scopes": scopes,
            "flags": flags,
            "params": [p["name"] for p in op.get("parameters", []) if p.get("in") == "query"],
        })

by_tag = collections.defaultdict(list)
for o in ops:
    by_tag[o["tag"]].append(o)

plus = sum(1 for o in ops if "Plus" in o["flags"])
beta = sum(1 for o in ops if "beta" in o["flags"])
dep = sum(1 for o in ops if "**deprecated**" in o["flags"])
server = spec["servers"][0]["url"]

out = []
w = out.append
w("# Ramp Developer API — Endpoint Cheatsheet")
w("")
w(f"All **{len(ops)} operations** across **{len(spec['paths'])} paths**, generated from")
w(f"[`api-docs/developer-api.json`](api-docs/developer-api.json) "
  f"(OpenAPI {spec['openapi']}, `{spec['info']['title']}` {spec['info']['version']}).")
w("")
w(f"> Generated {datetime.date.today().isoformat()} by "
  f"[`api-docs/gen-cheatsheet.py`](api-docs/gen-cheatsheet.py). "
  f"Do not hand-edit — run `api-docs/refresh.sh` to rebuild.")
w("")
w(f"Base URL: `{server}` · Auth: OAuth 2.0 authorization code · "
  f"Docs: https://docs.ramp.com/developer-api/v1/introduction")
w("")
w("## Before scoping anything against this")
w("")
w(f"- **{plus} of {len(ops)} operations are marked `x-ramp-plus-required`** — they need the "
  "Ramp Plus plan. Confirm Affect's plan before designing against them.")
w(f"- **{beta} are marked `x-beta`** and {dep} are deprecated. Beta endpoints can change "
  "without notice; treat them as unsuitable for a production pipeline.")
w("- Every operation requires an OAuth scope (right-hand column). Scopes are granted per "
  "app in the Ramp developer console — an app with the wrong scopes gets a 403, not a 401.")
w("- List endpoints paginate with `start` (id cursor) + `page_size` (2–100), not offsets.")
w("")
w("**Legend:** `Plus` = requires Ramp Plus · `beta` = unstable · "
  "`destructive` = irreversible · **deprecated** = do not build on.")
w("")
w("---")
w("")

for tag in sorted(by_tag):
    w(f"## {tag}")
    if tag_desc.get(tag) and tag_desc[tag].lower() != tag.lower():
        w("")
        w(f"_{tag_desc[tag]}_")
    w("")
    w("| Endpoint | Summary | Flags | Scope |")
    w("|---|---|---|---|")
    for o in sorted(by_tag[tag], key=lambda x: (x["path"], x["method"])):
        scopes = "<br>".join(f"`{s}`" for s in o["scopes"]) or "—"
        w(f"| `{o['method']} {o['path']}` | {o['summary']} | "
          f"{' '.join(o['flags']) or '—'} | {scopes} |")
    w("")

w("---")
w("")
w("## Query parameters by endpoint")
w("")
w("Only endpoints that declare query parameters in the spec are listed.")
w("")
w("| Endpoint | Query parameters |")
w("|---|---|")
for o in sorted((o for o in ops if o["params"]), key=lambda x: (x["path"], x["method"])):
    w(f"| `{o['method']} {o['path']}` | {', '.join(f'`{p}`' for p in o['params'])} |")
w("")
w("---")
w("")
w("## OAuth scopes")
w("")
w(f"{len(scope_desc)} scopes are defined. Request only what the integration needs.")
w("")
w("| Scope | Description |")
w("|---|---|")
for s in sorted(scope_desc):
    w(f"| `{s}` | {scope_desc[s]} |")
w("")

OUT = "../endpoints-cheatsheet.md"
with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(out))

# Self-check: every operation in the spec made it into an endpoint table.
endpoint_rows = {line.split("`")[1] for line in out if line.startswith("| `")}
missing = [f"{o['method']} {o['path']}" for o in ops if f"{o['method']} {o['path']}" not in endpoint_rows]
assert not missing, f"{len(missing)} operations dropped, e.g. {missing[:3]}"
print(f"{OUT}: {len(ops)} operations, {len(spec['paths'])} paths, {len(scope_desc)} scopes")
