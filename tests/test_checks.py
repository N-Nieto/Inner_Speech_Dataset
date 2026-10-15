"""checks/verify_dataset.py: integrity check against a manifest."""

import hashlib

from conftest import load_script


def test_integrity_detects_changed_and_missing_files(tmp_path):
    verify = load_script("checks/verify_dataset.py")
    files = {
        "derivatives/sub-01/ses-01/sub-01_ses-01_events.dat": b"published",
        "derivatives/sub-01/ses-01/sub-01_ses-01_report.pkl": b"report",
        "derivatives/sub-01/ses-02/sub-01_ses-02_report.pkl": b"other",
    }
    manifest = {"version": "test", "files": {}}
    for rel, content in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_bytes(content)
        manifest["files"][rel] = {
            "size": len(content),
            "md5": hashlib.md5(content).hexdigest(),
        }
    rows = verify.check_integrity(tmp_path, manifest, False, [1], [1, 2])
    assert all(r["status"] == "ok" for r in rows)

    (tmp_path / "derivatives/sub-01/ses-01/sub-01_ses-01_events.dat").write_bytes(
        b"modified events"
    )
    (tmp_path / "derivatives/sub-01/ses-02/sub-01_ses-02_report.pkl").unlink()
    status = {
        r["file"]: r["status"]
        for r in verify.check_integrity(tmp_path, manifest, False, [1], [1, 2])
    }
    assert status["derivatives/sub-01/ses-01/sub-01_ses-01_events.dat"] == "wrong size"
    assert status["derivatives/sub-01/ses-02/sub-01_ses-02_report.pkl"] == "missing"


def test_newest_manifest_is_default():
    verify = load_script("checks/verify_dataset.py")
    assert verify.newest_manifest().name == "ds003626_2.2.0_manifest.json"
