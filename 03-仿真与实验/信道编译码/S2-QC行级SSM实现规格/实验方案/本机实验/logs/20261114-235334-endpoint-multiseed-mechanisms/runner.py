"""Detached, logged subprocesses for this experiment only (no shell pipeline)."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent


def now():
    return datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()


def save(path, data):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["launch", "supervise"])
    parser.add_argument("--name", required=True)
    parser.add_argument("--cwd", default=str(ROOT.parent.parent))
    arguments = sys.argv[1:]
    separator = arguments.index("--") if "--" in arguments else len(arguments)
    args = parser.parse_args(arguments[:separator])
    command = arguments[separator + 1:]
    directory = ROOT / args.name
    if args.mode == "launch":
        directory.mkdir(exist_ok=False)
        assert command, "command required"
        specification = {
            "command": command, "command_shell_display": shlex.join(command),
            "cwd": args.cwd, "created_at": now(),
            "environment_overrides": {
                "CUDA_VISIBLE_DEVICES": "GPU-1b921c5f-58e5-ea98-777b-8f09a1ef0857",
                "CUDA_DEVICE_ORDER": "PCI_BUS_ID", "NVIDIA_TF32_OVERRIDE": "0",
                "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1",
                "CUBLAS_WORKSPACE_CONFIG": ":4096:8"
            },
            "session_kind": "POSIX detached supervisor (setsid), direct stdout/stderr files",
            "stdout": str(directory / "stdout.log"), "stderr": str(directory / "stderr.log")
        }
        save(directory / "launch.json", specification)
        with (directory / "supervisor.stdout.log").open("wb") as stdout, \
             (directory / "supervisor.stderr.log").open("wb") as stderr:
            supervisor = subprocess.Popen(
                [sys.executable, "-B", str(Path(__file__).resolve()), "supervise", "--name", args.name],
                start_new_session=True, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                close_fds=True)
        print(json.dumps({"name": args.name, "supervisor_pid": supervisor.pid,
                          "logs": str(directory)}, ensure_ascii=False))
        return
    specification = json.loads((directory / "launch.json").read_text())
    environment = os.environ.copy()
    environment.update(specification["environment_overrides"])
    with (directory / "stdout.log").open("wb") as stdout, \
         (directory / "stderr.log").open("wb") as stderr:
        child = subprocess.Popen(specification["command"], cwd=specification["cwd"],
                                 env=environment, stdin=subprocess.DEVNULL,
                                 stdout=stdout, stderr=stderr)
        specification.update(supervisor_pid=os.getpid(), pid=child.pid,
                             session_id=os.getsid(0), started_at=now())
        save(directory / "launch.json", specification)
        returncode = child.wait()
    save(directory / "exit.json", {"returncode": returncode, "finished_at": now(),
                                    "pid": child.pid, "supervisor_pid": os.getpid()})
    sys.exit(returncode if returncode >= 0 else 128 - returncode)


if __name__ == "__main__":
    main()
