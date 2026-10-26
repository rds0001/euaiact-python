"""Check installed distributions independently; no factory checkout required.

Prepare build, setuptools, wheel, twine, pytest and jsonschema beforehand.
All package installations use --no-index; Linux runtime checks use seccomp.
"""

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--test-filter", help="Local targeted validation; CI omits this"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Export the exact verified wheel/sdist plus SHA256SUMS",
    )
    args = parser.parse_args()
    if args.output_dir is not None and args.test_filter:
        parser.error("Export requires the complete test suite, without --test-filter")
    destination = args.output_dir.absolute() if args.output_dir is not None else None
    if destination is not None and destination.exists():
        parser.error("Export destination must not exist")
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    env["PIP_NO_INDEX"] = "1"
    env["PIP_NO_CACHE_DIR"] = "1"
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"

    def run(command, cwd, runtime=False):
        if runtime and sys.platform == "linux":
            command = [
                sys.executable,
                str(root / "tools/netzsperre.py"),
                *map(str, command),
            ]
        subprocess.run(list(map(str, command)), cwd=cwd, env=env, check=True)

    with tempfile.TemporaryDirectory(prefix="euaiact-ci-") as temporary:
        work = Path(temporary)
        source = work / "source"
        shutil.copytree(
            root,
            source,
            ignore=shutil.ignore_patterns(
                ".git", ".pytest_cache", "__pycache__", "*.egg-info", "build", "dist"
            ),
        )
        artifacts = work / "artifacts"
        run(
            [sys.executable, "-m", "build", "--no-isolation", "--outdir", artifacts],
            source,
        )
        (wheel,) = artifacts.glob("*.whl")
        (sdist,) = artifacts.glob("*.tar.gz")
        run([sys.executable, "-m", "twine", "check", wheel, sdist], work)
        # Only extract the locally built archive, after checking every member.
        with tarfile.open(sdist) as archive:
            for member in archive.getmembers():
                path = Path(member.name)
                if (
                    path.is_absolute()
                    or ".." in path.parts
                    or not (member.isdir() or member.isfile())
                ):
                    raise RuntimeError("Unsafe sdist member")
            archive.extractall(work / "unpacked")
        (extracted,) = (work / "unpacked").iterdir()
        for kind, artifact in (("wheel", wheel), ("sdist", sdist)):
            venv = work / kind
            run(
                [
                    sys.executable,
                    "-m",
                    "venv",
                    "--without-pip",
                    "--system-site-packages",
                    venv,
                ],
                work,
            )
            python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            run(
                [
                    python,
                    "-m",
                    "pip",
                    "install",
                    "--no-index",
                    "--no-deps",
                    "--no-build-isolation",
                    "--ignore-installed",
                    artifact,
                ],
                work,
            )
            checks = work / (kind + "_checks")
            checks.mkdir()
            for directory in ("tests", "examples"):
                shutil.copytree(extracted / directory, checks / directory)
            (checks / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
            run(
                [
                    python,
                    "-c",
                    "import euaiact,sys; from pathlib import Path; "
                    "p=Path(euaiact.__file__).resolve(); print(p); "
                    "assert p.is_relative_to(Path(sys.prefix).resolve())",
                ],
                checks,
                runtime=True,
            )
            command = [python, "-m", "pytest", "-q", "-c", "pytest.ini", "tests"]
            if args.test_filter:
                command += ["-k", args.test_filter]
            run(command, checks, runtime=True)
            run([python, "examples/unternehmen.py"], checks, runtime=True)
        if destination is not None:
            destination.mkdir(parents=True, exist_ok=False)
            lines = []
            for artifact in (wheel, sdist):
                target = destination / artifact.name
                shutil.copy2(artifact, target)
                digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
                if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                    raise RuntimeError("Artifact changed during export")
                lines.append(digest + "  " + artifact.name)
            (destination / "SHA256SUMS").write_text(
                "\n".join(lines) + "\n", encoding="utf-8"
            )
        print("Installed wheel and sdist checks passed")


if __name__ == "__main__":
    main()
