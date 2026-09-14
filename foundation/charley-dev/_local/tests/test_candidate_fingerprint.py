"""A candidate built from older source must not authorize a new model definition."""
import copy
import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import validate_candidate_model as model


def test_candidate_fingerprint():
    handle = {"run_id": "fingerprint-test", "lakehouse_id": "isolated-test"}
    target = {"id": handle["lakehouse_id"], "defaultSchema": "dbo"}
    first = model.candidate.build_full(handle["run_id"], target)
    second = model.candidate.build_full(handle["run_id"], target)
    assert json.dumps(first) == json.dumps(second), "candidate generation is nondeterministic"
    handle["definition_sha256"] = hashlib.sha256(json.dumps(first).encode()).hexdigest()
    model.require_current_definition(handle)
    for fingerprint in (None, "0" * 64):
        invalid = dict(handle, definition_sha256=fingerprint)
        if fingerprint is None:
            del invalid["definition_sha256"]
        try:
            model.require_current_definition(invalid)
        except RuntimeError:
            pass
        else:
            raise AssertionError("missing or changed fingerprint accepted")
    changed = copy.deepcopy(first)
    next(c for c in changed["cells"] if c["cell_type"] == "code")["source"].append("\nraise RuntimeError('changed source')\n")
    with patch.object(model.candidate, "build_full", return_value=changed):
        try:
            model.require_current_definition(handle)
        except RuntimeError:
            pass
        else:
            raise AssertionError("changed candidate code accepted under older fingerprint")


if __name__ == "__main__":
    test_candidate_fingerprint()
    print("candidate fingerprint checks passed")
