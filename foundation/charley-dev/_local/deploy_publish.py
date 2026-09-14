"""Build and deploy cd_50_publish_models - the only thing that shows readers a new gold.

    python deploy_publish.py                # dry run
    python deploy_publish.py --apply        # create/update the notebook (does NOT run it)
    python deploy_publish.py --apply --run  # ...and run it now: an out-of-band publish

WHY THIS EXISTS. Both models are Direct Lake on OneLake. Readers see the gold Delta tables
as of the model's last framing. With automatic update ON, the service frames on its own as
soon as gold is written - before the DQ gate has looked at it, and per table, so mid-build a
report can mix two releases. With it OFF, this notebook is the one place a frame happens,
and the pipeline runs it only after "Data Quality Gate" Succeeded.

WHAT IT DOES, EVERY RUN, IN ORDER:
  1. Resolves both models BY NAME in the workspace (exactly one each, or fail). Ids are not
     hardcoded: deploy_model.py --recreate issues a new id.
  2. Turns automatic update OFF on both (idempotent). A recreated model comes back with it
     ON; set_autosync.py uses the same function for a one-off. A failure here is recorded,
     both refreshes still run, and the activity FAILS at the end.
  3. Reads each model's latest meta_PipelineRun RunId BEFORE refreshing. If a model already
     shows the gate run this notebook is about to publish, something framed it without us -
     automatic update was on. Recorded, refresh still done (so both models agree), then the
     activity FAILS with that message.
  4. Full refresh of "Affect Project Report", wait for THAT request (matched by requestId),
     then "Project Quality Plan". NOT atomic: if model 2 fails after model 1 succeeded, the
     two models show DIFFERENT releases until the next successful run. The failure alert
     names each model's current run so it is clear which one is ahead.
  5. After both refreshes, each model's latest run must be the gate run and Status "ok".
  6. Writes Files/_diag/publish_run.json before raising; alerts via fabric_common.notify.

--run is deliberately separate from --apply: running it outside the pipeline frames
whatever gold holds right now, validated or not.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy as dp  # noqa: E402
import deploy_seeds as ds  # noqa: E402
import validate_model as vm  # noqa: E402
from make_notebooks import cell, notebook  # noqa: E402

HERE = Path(__file__).resolve().parent
NOTEBOOK_NAME = "cd_50_publish_models"

# Refresh order matters: see step 4 above.
MODEL_NAMES = ["Affect Project Report", "Project Quality Plan"]
REFRESH_TIMEOUT = 900
ROOT_API = vm.PBI_API
GROUP_API = f"{vm.PBI_API}/groups/{dp.WORKSPACE_ID}"

# MIN(Status): "blocked" sorts before "ok", so any blocked row at the latest RunAt wins.
RUN_ID_DAX = """EVALUATE
VAR Last = MAX ( meta_PipelineRun[RunAt] )
RETURN ROW (
    "RunId", CALCULATE ( MAX ( meta_PipelineRun[RunId] ), meta_PipelineRun[RunAt] = Last ),
    "Status", CALCULATE ( MIN ( meta_PipelineRun[Status] ), meta_PipelineRun[RunAt] = Last ) )"""

dax = vm.dax  # module-level name so latest_run resolves here exactly as in the notebook


# ---- Shared by the notebook (embedded by source) and set_autosync.py -----------------------

def pbi(method: str, url: str, tok: str, body: dict | None = None) -> tuple[int, dict]:
    request = urllib.request.Request(
        url, method=method, data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raise dp.FabricError(f"{method} {url} failed ({exc.code}): {exc.read().decode()[:300]}") from exc


def resolve_models(tok: str) -> list[tuple[str, str]]:
    _, body = pbi("GET", f"{GROUP_API}/datasets", tok)
    resolved = []
    for name in MODEL_NAMES:
        ids = [d.get("id") for d in body.get("value", []) if d.get("name") == name]
        if len(ids) != 1:
            raise dp.FabricError(f"expected exactly one semantic model named {name!r} in the workspace, found {len(ids)}")
        resolved.append((name, ids[0]))
    return resolved


def disable_autosync(tok: str, dataset_id: str, apply: bool = True) -> str:
    """semantic-link-labs set_autosync(enable=False): internal API, no public equivalent."""
    _, capacities = pbi("GET", f"{ROOT_API}/capacities", tok)
    cluster = capacities["@odata.context"].split("/v1.0")[0]
    _, meta = pbi("GET", f"{cluster}/metadata/models/{dataset_id}", tok)
    model_id = meta.get("model", {}).get("id")
    if not model_id:
        raise dp.FabricError(f"no internal model id for dataset {dataset_id}")
    url = f"{cluster}/metadata/models/{model_id}/settings"
    if apply:
        status, _ = pbi("POST", url, tok, {"directLakeAutoSync": False})
        if status != 204:
            raise dp.FabricError(f"disabling automatic update on {dataset_id}: expected 204, got {status}")
    return url


def latest_run(tok: str, dataset_id: str) -> dict:
    row = dax(dataset_id, tok, RUN_ID_DAX)[0]
    return {"run_id": row.get("[RunId]"), "status": row.get("[Status]")}


SHARED = (pbi, resolve_models, disable_autosync, latest_run)

PUBLISH = '''
tok = notebookutils.credentials.getToken("pbi")
record = {"started": datetime.now(timezone.utc).isoformat(), "models": [], "ok": False}
os.makedirs(DIAG, exist_ok=True)

try:
    with open(f"{DIAG}/heartbeat_run.json", encoding="utf-8") as fh:
        gate = record["gate_run_id"] = json.load(fh)["run_id"]
    record["models"] = [{"name": n, "id": i} for n, i in resolve_models(tok)]
    # A failure here must not skip the refreshes: gold already passed the gate, and a model
    # left unframed shows readers yesterday. Recorded, both refreshes run, then it fails.
    for m in record["models"]:
        try:
            disable_autosync(tok, m["id"])
            m["autosync_disabled"] = True
        except Exception as exc:
            m["autosync_disabled"] = False
            m["autosync_error"] = f"{type(exc).__name__}: {exc}"
    for m in record["models"]:
        try:
            m["before"] = latest_run(tok, m["id"])
        except Exception as exc:  # a recreated model that was never framed cannot answer
            m["before"] = f"unreadable: {exc}"
    auto_framed = [m["name"] for m in record["models"]
                   if isinstance(m["before"], dict) and m["before"]["run_id"] == gate]
    record["auto_framed"] = auto_framed
    for m in record["models"]:
        print(f"refreshing {m['name']} ...", flush=True)
        m["refresh"] = reframe(m["id"], tok, timeout=REFRESH_TIMEOUT)
        print(f"  {m['refresh'].get('status')} {m['refresh'].get('requestId')}")
    for m in record["models"]:
        m["after"] = latest_run(tok, m["id"])
        print(f"  {m['name']}: {m['after']}")
    wrong = [m["name"] for m in record["models"] if m["after"] != {"run_id": gate, "status": "ok"}]
    if wrong:
        raise RuntimeError(f"after refresh, {wrong} do not show gate run {gate} with Status ok")
    if auto_framed:
        raise RuntimeError(
            f"AUTO-FRAMING DETECTED: {auto_framed} already showed gate run {gate} before this "
            "notebook refreshed - Direct Lake automatic update was ON, so readers may have seen "
            "gold before the DQ gate. It has now been turned off; check who re-enabled it.")
    autosync_failed = {m["name"]: m["autosync_error"] for m in record["models"] if not m["autosync_disabled"]}
    if autosync_failed:
        raise RuntimeError(
            f"AUTOMATIC UPDATE NOT DISABLED on {sorted(autosync_failed)}: both models were refreshed "
            f"to gate run {gate}, but automatic update may still be ON, so the next gold write can "
            f"reach readers before the DQ gate. Run set_autosync.py --apply. Errors: {autosync_failed}")
    record["ok"] = True
except Exception as exc:
    record["error"] = f"{type(exc).__name__}: {exc}"
    releases = []
    for m in record["models"]:
        try:
            m["now"] = latest_run(tok, m["id"])
        except Exception as read_exc:
            m["now"] = f"unreadable: {read_exc}"
        releases.append(f"- {m['name']}: {m['now']} (refresh {'done' if 'refresh' in m else 'NOT done'})")
    record["alert"] = (
        f"{record['error']}\\n\\nGate run: {record.get('gate_run_id')}\\nWhat each model shows now "
        "(if they differ, the one on the gate run is ahead):\\n" + "\\n".join(releases))
    try:
        import fabric_common as fc
        record["alert_sent"] = bool(fc.notify("PUBLISH FAILED - cd_50_publish_models", record["alert"]))
        if not record["alert_sent"]:
            print("!" * 78 + "\\nWARNING: PUBLISH FAILED AND NO ALERT WAS SENT - no DQ-ALERT-WEBHOOK "
                  "secret is configured, so nobody has been told.\\nThis activity fails below; "
                  "check the pipeline run.\\n" + "!" * 78)
    except Exception as alert_exc:
        print(f"[alert] could not alert: {alert_exc}\\n{record['alert']}")
    raise
finally:
    record["finished"] = datetime.now(timezone.utc).isoformat()
    with open(f"{DIAG}/publish_run.json", "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1, default=str)

print(f"published run {gate} to {len(record['models'])} model(s)")
'''


def build_notebook() -> dict:
    # The SAME functions validate_model.py / set_autosync.py use and the tests exercise -
    # copied in by source, not rewritten, so the notebook cannot drift from them.
    helpers = "\n\n".join(inspect.getsource(f) for f in (vm.dax, vm.reframe, vm.wait_refresh, *SHARED))
    cells = [
        cell(
            f"""
# {NOTEBOOK_NAME}

Frames both Direct Lake models on the gold that the DQ gate just passed, then checks both
models show that run. Generated by `_local/deploy_publish.py`.
""",
            "markdown",
        ),
        cell(
            '''
import json, os, sys, urllib.error, urllib.request
from datetime import datetime, timezone
from types import SimpleNamespace

sys.path.insert(0, "/lakehouse/default/Files/lib")
dp = SimpleNamespace(FabricError=RuntimeError)
PBI_API = GROUP_API = ''' + json.dumps(GROUP_API) + '''
ROOT_API = ''' + json.dumps(ROOT_API) + '''
MODEL_NAMES = ''' + json.dumps(MODEL_NAMES) + '''
REFRESH_TIMEOUT = ''' + str(REFRESH_TIMEOUT) + '''
RUN_ID_DAX = ''' + json.dumps(RUN_ID_DAX) + '''
DIAG = "/lakehouse/default/Files/_diag"

''' + helpers
        ),
        cell(PUBLISH),
    ]
    return notebook(cells)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--run", action="store_true", help="also run it now (out-of-band publish)")
    args = parser.parse_args()

    tok = dp.token()
    lh = json.loads((HERE / "fabric_ids.json").read_text())["CD_Gold_Lakehouse"]
    nb = ds.attach(build_notebook(), lh, dp.WORKSPACE_ID)
    nb["metadata"]["dependencies"]["lakehouse"]["default_lakehouse_name"] = "CD_Gold_Lakehouse"

    existing = ds.find_item(tok, NOTEBOOK_NAME, "Notebook")
    print(f"would {'update' if existing else 'create'} {NOTEBOOK_NAME} "
          f"(refreshes {', '.join(MODEL_NAMES)})")
    if not args.apply:
        print("\nDRY RUN - nothing written. Re-run with --apply.")
        return 0

    definition = {"format": "ipynb", "parts": [
        {"path": "notebook-content.ipynb", "payload": ds.payload(nb),
         "payloadType": "InlineBase64"}]}
    if existing:
        status, _, headers = dp.call(
            "POST", f"/workspaces/{dp.WORKSPACE_ID}/items/{existing['id']}/updateDefinition",
            tok, {"definition": definition})
        if status == 202:
            dp.wait_for_operation(headers, tok)
        item_id = existing["id"]
        print(f"  updated {NOTEBOOK_NAME}")
    else:
        status, _, headers = dp.call(
            "POST", f"/workspaces/{dp.WORKSPACE_ID}/items", tok,
            {"displayName": NOTEBOOK_NAME, "type": "Notebook",
             "folderId": dp.FOLDER_ID, "definition": definition})
        if status == 202:
            dp.wait_for_operation(headers, tok)
        item_id = ds.find_item(tok, NOTEBOOK_NAME, "Notebook")["id"]
        print(f"  created {NOTEBOOK_NAME} ({item_id})")

    if args.run:
        print("  running ...", end=" ", flush=True)
        print(ds.run_notebook(tok, item_id))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
