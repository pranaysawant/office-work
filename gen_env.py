#!/usr/bin/env python3
"""
Build environment variables from config.json and set the Gemini
service-account key path.

Local (no Docker): key is used where it is; variables go to .env,
which the app loads with python-dotenv's load_dotenv():
    python gen_env.py --gemini-keypath ~/keys/gemini_sa.json

Docker (RUN_ENV=docker set in the Dockerfile): key is copied to
/app/secrets/gemini_sa.json and the app is started with the variables:
    python gen_env.py --gemini-keypath /run/secrets/gemini_sa.json -- python src/app.py
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

# Nested sections that get flattened: UAIS_DATA.AUTH_URL -> UAIS_AUTH_URL
FLATTEN = {"UAIS_DATA": "UAIS_"}
# Replaced by the copied key path below
SKIP = {"SA_KEYPATH"}


def to_str(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"))
    return str(value)


def config_to_env(config):
    env = {}
    for key, value in config.items():
        if key in SKIP:
            continue
        if key in FLATTEN and isinstance(value, dict):
            items = [(FLATTEN[key] + k, v) for k, v in value.items()]
        else:
            items = [(key, value)]
        for name, val in items:
            # Blank values are secrets supplied at runtime (docker -e / Azure app settings)
            if val is None or val == "":
                continue
            env[name] = to_str(val)
    return env


def stage_key(src, dest):
    src, dest = Path(src), Path(dest)
    if not src.is_file():
        sys.exit(f"Gemini key not found: {src}")
    json.loads(src.read_text())  # fail early if it isn't valid JSON
    dest.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(dest.parent, 0o700)
    shutil.copyfile(src, dest)
    os.chmod(dest, 0o600)
    return str(dest)


def detect_mode():
    # Set ENV RUN_ENV=docker in the Dockerfile; /.dockerenv is a fallback
    # (it doesn't exist under containerd, e.g. AKS, so don't rely on it alone).
    run_env = os.environ.get("RUN_ENV", "").lower()
    if run_env in ("docker", "local"):
        return run_env
    return "docker" if Path("/.dockerenv").exists() else "local"


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--gemini-keypath", required=True,
                        help="Path to the Gemini service-account JSON key")
    parser.add_argument("--dest", default="/app/secrets/gemini_sa.json",
                        help="Where to copy the key inside the container")
    parser.add_argument("--env-out",
                        help=".env file to write (default: .env in local mode, none in docker)")
    parser.add_argument("--mode", choices=["auto", "local", "docker"], default="auto")
    parser.add_argument("cmd", nargs=argparse.REMAINDER,
                        help="Command to run with the env, after --")
    args = parser.parse_args()

    mode = detect_mode() if args.mode == "auto" else args.mode
    print(f"Mode: {mode}")

    config = json.loads(Path(args.config).read_text())
    env = config_to_env(config)

    if mode == "docker":
        key_path = stage_key(args.gemini_keypath, args.dest)
    else:
        # Local: use the key where it is, no copy
        src = Path(args.gemini_keypath).expanduser().resolve()
        if not src.is_file():
            sys.exit(f"Gemini key not found: {src}")
        key_path = str(src)
        if not args.env_out:
            args.env_out = ".env"

    env["SA_KEYPATH"] = key_path
    env["GOOGLE_APPLICATION_CREDENTIALS"] = key_path

    print(f"SA_KEYPATH={key_path}")
    print(f"GOOGLE_APPLICATION_CREDENTIALS={key_path}")

    if args.env_out:
        # Unquoted KEY=value works with both `docker --env-file` and python-dotenv
        Path(args.env_out).write_text("".join(f"{k}={v}\n" for k, v in env.items()))
        print(f"Wrote {len(env)} variables to {args.env_out}")

    cmd = args.cmd[1:] if args.cmd[:1] == ["--"] else args.cmd
    if cmd:
        # Variables already set (docker -e, Azure app settings) win over config.json
        merged = {**env, **os.environ}
        merged["SA_KEYPATH"] = key_path
        merged["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
        os.execvpe(cmd[0], cmd, merged)


if __name__ == "__main__":
    main()
