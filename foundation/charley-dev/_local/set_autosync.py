"""Turn OFF Direct Lake automatic update ("Keep your Direct Lake data up to date") on both models.

    python set_autosync.py            # dry run: resolve both internal model ids, change nothing
    python set_autosync.py --apply    # POST directLakeAutoSync=false to both

WHY. With automatic update on, the service frames each table as soon as gold changes - before
the DQ gate, and table by table, so readers can see a half-built, unvalidated release. Off,
the only frame is cd_50_publish_models, which the pipeline runs after the gate passes.

HOW. There is no public API or TMDL property for this setting. This is exactly what
semantic-link-labs sempy_labs.directlake.set_autosync(enable=False) does
(src/sempy_labs/directlake/_autosync.py, _helper_functions._get_url_prefix/get_model_id):
  cluster = GET api.powerbi.com/v1.0/myorg/capacities -> "@odata.context" before "/v1.0"
  model   = GET {cluster}/metadata/models/{datasetId} -> model.id
  POST {cluster}/metadata/models/{model.id}/settings  {"directLakeAutoSync": false} -> 204
Undocumented and internal: confirm the result in the portal (Semantic model settings >
Refresh) after --apply, because the setting cannot be read back through any API.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy as dp  # noqa: E402
import deploy_publish  # noqa: E402
import validate_model as vm  # noqa: E402


def call(method: str, url: str, tok: str, body: dict | None = None) -> tuple[int, dict]:
    request = urllib.request.Request(
        url, method=method, data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raise dp.FabricError(f"{method} {url} failed ({exc.code}): {exc.read().decode()[:300]}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    tok = vm.pbi_token()
    _, capacities = call("GET", f"{vm.PBI_API}/capacities", tok)
    cluster = capacities["@odata.context"].split("/v1.0")[0]
    print(f"cluster {cluster}")

    for name, dataset_id in deploy_publish.MODELS:
        _, meta = call("GET", f"{cluster}/metadata/models/{dataset_id}", tok)
        model_id = meta.get("model", {}).get("id")
        if not model_id:
            raise dp.FabricError(f"no internal model id for {name} ({dataset_id})")
        url = f"{cluster}/metadata/models/{model_id}/settings"
        if not args.apply:
            print(f"  would POST {url} {{\"directLakeAutoSync\": false}}  ({name})")
            continue
        status, _ = call("POST", url, tok, {"directLakeAutoSync": False})
        if status != 204:
            raise dp.FabricError(f"{name}: expected 204, got {status}")
        print(f"  {name}: automatic update disabled")

    if not args.apply:
        print("\nDRY RUN - nothing changed. Re-run with --apply.")
    else:
        print("\nConfirm both in the portal: Semantic model settings > Refresh.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
