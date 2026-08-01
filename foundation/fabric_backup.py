"""Read-only backup of a Fabric workspace into a local folder mirror.

Exports item definitions via the Fabric REST API. Never writes to Fabric.
"""
import base64, json, os, re, subprocess, sys, time
import requests

WS_NAME = "Build"
OUT = r"C:\Users\charl\Desktop\Affect\foundation"
API = "https://api.fabric.microsoft.com/v1"

# Fabric folder display name -> existing local folder name, where they differ.
LOCAL_ALIAS = {
    "01- Ingestion": "01-ingestion",
    "02- Transformation": "02 transformation",
    "03- Lakehouses": "03-lakehouses",
    "04- Semantic Models": "04-semantic_models",
    "05- Reports": "05-reports",
    "Financial Facts": "Financial_Facts",  # only under Procore_APICalls; see fixup below
}

# Types with no getDefinition endpoint -> metadata only.
NO_DEFINITION = {"Lakehouse", "Warehouse", "SQLEndpoint", "Dashboard", "Environment"}


def token(resource="https://api.fabric.microsoft.com"):
    return subprocess.run(
        ["az", "account", "get-access-token", "--resource", resource,
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, check=True, shell=True,
    ).stdout.strip()


S = requests.Session()
S.headers["Authorization"] = "Bearer " + token()


def get(url, **kw):
    r = S.get(url, **kw)
    r.raise_for_status()
    return r.json()


def safe(name):
    """Windows-safe path segment."""
    return re.sub(r'[<>:"/\\|?*]', "-", name).strip().rstrip(".")


def paged(url, key="value"):
    out = []
    while url:
        d = get(url)
        out += d.get(key, [])
        tok = d.get("continuationUri")
        url = tok
    return out


def resolve_paths(folders):
    """folder id -> local relative path"""
    by_id = {f["id"]: f for f in folders}
    paths = {}

    def walk(fid):
        if fid in paths:
            return paths[fid]
        f = by_id[fid]
        seg = LOCAL_ALIAS.get(f["displayName"], f["displayName"])
        parent = f.get("parentFolderId")
        p = os.path.join(walk(parent), safe(seg)) if parent else safe(seg)
        paths[fid] = p
        return p

    for fid in by_id:
        walk(fid)
    # "Financial Facts" under 02- Transformation keeps its Fabric name;
    # only the ingestion one is aliased to match the existing local folder.
    for fid, p in paths.items():
        if p.startswith("02 transformation") and p.endswith("Financial_Facts"):
            paths[fid] = p[: -len("Financial_Facts")] + "Financial Facts"
    return paths


def definition(ws_id, item_id, fmt=None):
    url = f"{API}/workspaces/{ws_id}/items/{item_id}/getDefinition"
    if fmt:
        url += f"?format={fmt}"
    r = S.post(url)
    if r.status_code == 202:  # long-running operation
        loc = r.headers.get("Location")
        for _ in range(60):
            time.sleep(float(r.headers.get("Retry-After", 2)))
            st = get(loc)
            if st.get("status") == "Succeeded":
                return get(loc + "/result")["definition"]
            if st.get("status") == "Failed":
                raise RuntimeError(st)
            r = S.get(loc)
        raise TimeoutError(f"LRO timeout for {item_id}")
    r.raise_for_status()
    return r.json()["definition"]


def write_parts(dest_dir, parts):
    written = []
    for part in parts:
        if part.get("payloadType") != "InlineBase64":
            continue
        path = os.path.join(dest_dir, *part["path"].split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(base64.b64decode(part["payload"]))
        written.append(part["path"])
    return written


def main():
    ws = next(w for w in get(f"{API}/workspaces")["value"] if w["displayName"] == WS_NAME)
    ws_id = ws["id"]
    folders = paged(f"{API}/workspaces/{ws_id}/folders")
    items = paged(f"{API}/workspaces/{ws_id}/items")
    fpaths = resolve_paths(folders)

    manifest, failures = [], []
    for it in sorted(items, key=lambda i: (i["type"], i["displayName"])):
        rel = fpaths.get(it.get("folderId"), "_workspace-root")
        name, typ = it["displayName"], it["type"]
        base = os.path.join(OUT, rel)
        os.makedirs(base, exist_ok=True)
        rec = {"name": name, "type": typ, "id": it["id"],
               "description": it.get("description", ""), "folder": rel}

        if typ in NO_DEFINITION:
            rec["export"] = "metadata-only"
        else:
            try:
                fmt = "ipynb" if typ == "Notebook" else None
                d = definition(ws_id, it["id"], fmt)
                if typ == "Notebook":
                    dest = os.path.join(base, safe(name) + ".ipynb")
                    payload = next(p for p in d["parts"]
                                   if p["path"].endswith((".ipynb", ".py")))
                    with open(dest, "wb") as fh:
                        fh.write(base64.b64decode(payload["payload"]))
                    rec["export"] = os.path.relpath(dest, OUT)
                else:
                    dest = os.path.join(base, f"{safe(name)}.{typ}")
                    rec["export"] = os.path.relpath(dest, OUT)
                    rec["parts"] = write_parts(dest, d["parts"])
            except Exception as e:
                detail = getattr(e, "response", None)
                msg = detail.text[:300] if detail is not None else str(e)[:300]
                rec["export"] = "FAILED"
                rec["error"] = msg
                failures.append((name, typ, msg))
        manifest.append(rec)
        print(f"{typ:15} {name[:45]:45} -> {rec['export']}", flush=True)

    # Lakehouse table inventory (no definition API; tables are data, not code).
    for it in items:
        if it["type"] != "Lakehouse":
            continue
        rel = fpaths.get(it.get("folderId"), "_workspace-root")
        try:
            tables = paged(f"{API}/workspaces/{ws_id}/lakehouses/{it['id']}/tables", "data")
        except Exception as e:
            tables = [{"error": str(e)[:200]}]
        p = os.path.join(OUT, rel, f"{safe(it['displayName'])}.Lakehouse.tables.json")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(tables, fh, indent=2)
        print(f"{'Lakehouse':15} {it['displayName'][:45]:45} -> {len(tables)} tables")

    with open(os.path.join(OUT, "_manifest.json"), "w", encoding="utf-8") as fh:
        json.dump({"workspace": WS_NAME, "workspace_id": ws_id,
                   "exported_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "folders": [{"path": fpaths[f["id"]], "fabric_name": f["displayName"],
                                "id": f["id"]} for f in folders],
                   "items": manifest}, fh, indent=2)

    print(f"\n{len(manifest)} items, {len(failures)} failures")
    for f in failures:
        print("  FAILED:", f)


if __name__ == "__main__":
    main()
