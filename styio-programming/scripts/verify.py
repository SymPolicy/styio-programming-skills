#!/usr/bin/env python3
"""Offline package checks and isolated execution of pinned Styio fixtures.

JSON stdout; exits: 0 checks passed (runtime may be not_run), 1 runtime failure,
2 invalid arguments/package/environment. Does not install or download anything.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
SHA = re.compile(r"[0-9a-f]{64}")
PIN = re.compile(r"[0-9a-f]{40}")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative(value: str) -> Path:
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError(f"unsafe relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in {".", "..", ""} for p in value.split("/")):
        raise ValueError(f"unsafe relative path: {value!r}")
    return Path(*path.parts)


def checked_file(root: Path, path: str, sha: str) -> bytes:
    target = root / relative(path)
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise ValueError(f"invalid sha256 for {path}")
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"fixture escapes package: {path}")
    node = target
    while node != root:
        if node.is_symlink():
            raise ValueError(f"symlink fixture: {path}")
        node = node.parent
    data = target.read_bytes()
    if digest(data) != sha:
        raise ValueError(f"fixture hash mismatch: {path}")
    return data


def load_package(root: Path = ROOT) -> tuple[dict, dict, dict]:
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    header = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", skill, re.S)
    if not header or not re.search(r"^name: styio-programming$", header[1], re.M) or not re.search(r"^description: .+", header[1], re.M):
        raise ValueError("SKILL.md needs name: styio-programming and a description")
    if re.search(r"\bTODO\b|\[TODO", skill):
        raise ValueError("unfinished skill scaffold")
    for filename in ("agents/openai.yaml", "references/idioms.md", "references/diagnostics.md", "references/compatibility.md"):
        if not (root / filename).is_file():
            raise ValueError(f"missing package file: {filename}")
    compat = json.loads((root / "compatibility.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "fixtures/cases.json").read_text(encoding="utf-8"))
    if compat.get("schema_version") != 1 or manifest.get("schema_version") != 1:
        raise ValueError("unsupported manifest schema")
    if not PIN.fullmatch(manifest.get("compiler_ref", "")) or compat["language"]["commit"] != manifest["compiler_ref"]:
        raise ValueError("language source pins disagree or are malformed")
    if compat["language"]["repository"] != manifest["source_repository"] or not SHA.fullmatch(compat["verified_build"]["binary_sha256"]):
        raise ValueError("invalid compatibility metadata")
    all_files = {}
    for case in manifest["cases"]:
        cid = case["id"]
        if not isinstance(cid, str) or not re.fullmatch(r"[a-z0-9-]+", cid) or cid in all_files:
            raise ValueError(f"invalid or duplicate case: {cid}")
        if not 0 < case.get("timeout_seconds", 0) <= 120:
            raise ValueError(f"unbounded timeout: {cid}")
        negative = bool(case.get("expect_failure"))
        if negative != bool(case.get("stderr_source")) or sum(bool(case.get(x)) for x in ("stdout_source", "stderr_source", "artifact")) != 1:
            raise ValueError(f"case needs exactly one positive/negative/artifact oracle: {cid}")
        if (negative and case.get("expect_exit") not in (3, 4)) or (not negative and case.get("expect_exit") != 0):
            raise ValueError(f"invalid pinned exit code: {cid}")
        files = {}
        for key in ("source", "stdout_source", "stdin_source", "stderr_source"):
            if key in case:
                sha_key = "source_sha256" if key == "source" else key.replace("_source", "_sha256")
                files[key] = checked_file(root / "fixtures/upstream", case[key], case[sha_key])
        for asset in case.get("assets", []):
            files[asset["path"]] = checked_file(root / "fixtures/upstream", asset["path"], asset["sha256"])
        if "artifact" in case:
            relative(case["artifact"]["path"])
        for replacement in case.get("source_replacements", []):
            relative(replacement["new"])
            if replacement.get("count") != 1 or not replacement.get("old"):
                raise ValueError("path adaptation must identify one exact occurrence")
            if files["source"].decode("utf-8").count(replacement["old"]) != 1:
                raise ValueError("path adaptation no longer matches source")
        all_files[cid] = files
    if not all_files:
        raise ValueError("empty fixture suite")
    normalize = lambda s: re.sub(r"\s+", " ", s).strip()
    normalized_sources = [normalize(f["source"].decode("utf-8")) for f in all_files.values()]
    for doc in [root / "SKILL.md", *(root / "references").glob("*.md")]:
        text = doc.read_text(encoding="utf-8")
        prose = re.sub(r"```.*?```|`[^`]*`", "", text, flags=re.S)
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", prose):
            if "://" in target or target.startswith("#"):
                continue
            dest = (doc.parent / target.split("#")[0]).resolve()
            if not dest.is_relative_to(root.resolve()) or not dest.is_file():
                raise ValueError(f"broken or escaping local reference: {doc.name}: {target}")
        for code in re.findall(r"```styio\n(.*?)\n```", text, re.S):
            if not normalize(code) or not any(normalize(code) in source for source in normalized_sources):
                raise ValueError(f"unverified fenced Styio excerpt in {doc.name}")
    return compat, manifest, all_files


def judge(case: dict, data: dict, process: subprocess.CompletedProcess, cwd: Path) -> list[str]:
    errors = []
    if process.returncode != case["expect_exit"]:
        errors.append(f"exit {process.returncode}, expected {case['expect_exit']}")
    if case.get("expect_failure"):
        stderr = process.stderr.decode("utf-8", errors="replace")
        fragments = data["stderr_source"].decode("utf-8").splitlines()
        if not any(fragments) or any(line and line not in stderr for line in fragments):
            errors.append("expected diagnostic fragment missing")
        if process.stdout:
            errors.append("negative case produced stdout")
    else:
        if process.stderr:
            errors.append("unexpected stderr")
        if "stdout_source" in data and process.stdout != data["stdout_source"]:
            errors.append("stdout differs from golden bytes")
        if "artifact" in case:
            output = cwd / relative(case["artifact"]["path"])
            if not output.is_file() or output.read_bytes() != case["artifact"]["text"].encode("utf-8"):
                errors.append("output file differs from expected bytes")
    return errors


def run_case(binary: Path, case: dict, data: dict) -> dict:
    with tempfile.TemporaryDirectory(prefix="styio-skill-") as name:
        cwd = Path(name)
        source = data["source"].decode("utf-8")
        for replacement in case.get("source_replacements", []):
            source = source.replace(replacement["old"], replacement["new"])
        program = cwd / "case.styio"
        program.write_bytes(source.encode("utf-8"))
        for asset in case.get("assets", []):
            target = cwd / relative(asset["path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data[asset["path"]])
        try:
            process = subprocess.run([str(binary), "--file", str(program)], cwd=cwd,
                                     input=data.get("stdin_source", b""), capture_output=True,
                                     timeout=case["timeout_seconds"], shell=False)
        except subprocess.TimeoutExpired:
            return {"id": case["id"], "status": "failed", "errors": ["timeout"]}
        errors = judge(case, data, process, cwd)
        result = {"id": case["id"], "status": "failed" if errors else "passed", "exit_code": process.returncode, "errors": errors}
        if errors:
            result.update(stdout=process.stdout.decode("utf-8", errors="replace")[:3000], stderr=process.stderr.decode("utf-8", errors="replace")[:3000])
        return result


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def main(argv: list[str] | None = None) -> int:
    report = {"schema_version": 1, "static_status": "not_run", "runtime_status": "not_run"}
    try:
        parser = Parser(description=__doc__)
        parser.add_argument("--styio-bin", type=Path)
        parser.add_argument("--case", action="append", default=[])
        parser.add_argument("--require-known-binary", action="store_true")
        parser.add_argument("--json", action="store_true", help="JSON is always emitted")
        args = parser.parse_args(argv)
        compat, manifest, files = load_package()
        unknown = set(args.case) - set(files)
        if unknown:
            raise ValueError(f"unknown case IDs: {sorted(unknown)}")
        cases = [c for c in manifest["cases"] if not args.case or c["id"] in args.case]
        report.update(static_status="passed", skill_version=compat["skill_version"], language_commit=manifest["compiler_ref"], suite_scope="selected" if args.case else "full", fixture_count=len(manifest["cases"]))
        if not args.styio_bin:
            if args.require_known_binary:
                raise ValueError("--require-known-binary requires --styio-bin")
            report["cases"] = [{"id": c["id"], "status": "not_run"} for c in cases]
            report["next_step"] = "Supply --styio-bin with a trusted executable to run language tests."
        else:
            binary = args.styio_bin.expanduser().resolve(strict=True)
            if not binary.is_file() or not os.access(binary, os.X_OK):
                raise ValueError("compiler is not an executable file")
            binary_sha = digest(binary.read_bytes())
            known = binary_sha == compat["verified_build"]["binary_sha256"]
            report.update(binary_sha256=binary_sha, binary_provenance="known_tested_binary" if known else "unverified_binary_provenance")
            if args.require_known_binary and not known:
                raise ValueError("compiler fingerprint differs from recorded tested binary")
            report["cases"] = [run_case(binary, c, files[c["id"]]) for c in cases]
            report["runtime_status"] = "failed" if any(c["status"] != "passed" for c in report["cases"]) else "passed"
        code = 1 if report["runtime_status"] == "failed" else 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as exc:
        report.update(error=str(exc))
        code = 2
    report["exit_code"] = code
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
