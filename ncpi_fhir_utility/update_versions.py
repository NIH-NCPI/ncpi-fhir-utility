#!/usr/bin/env python3
"""
Updates versions and dates in all of our FHIR resources.

Example:
    $ scripts/update_versions.py 1.1.1
"""
import configparser
import json
from datetime import datetime, timezone
from pathlib import Path


def bump_ig_version(filePath, new_version):
    config = configparser.ConfigParser()
    if config.read(filePath) and "IG" in config:
        config.set("IG", "version", new_version)
        with filePath.open(mode="w") as f:
            config.write(f)
    else:
        raise Exception(f"Could not read {filePath}")


def bump_resource_version(filePath, new_version, our_urls):
    try:
        with filePath.open(mode="r") as f:
            body = json.load(f)
    except json.decoder.JSONDecodeError:
        return
    if body.get("url", "").startswith(our_urls):
        body["version"] = new_version
        body["date"] = datetime.now().astimezone(timezone.utc).isoformat()
        with filePath.open(mode="w") as f:
            json.dump(body, f, indent=2)
    elif any(
        p.startswith(our_urls)
        for p in body.get("meta", {}).get("profile", [""])
    ):
        body["meta"]["versionId"] = new_version
        body["meta"]["lastUpdated"] = (
            datetime.now().astimezone(timezone.utc).isoformat()
        )
        with filePath.open(mode="w") as f:
            json.dump(body, f, indent=2)


def run(site_root, new_version, our_urls):
    our_urls = tuple(s.strip() for s in our_urls.split(","))
    site_root = Path(site_root)
    if not site_root.is_dir():
        raise Exception(f"<site_root> dir '{site_root}' must exist")
    ini_file = Path(site_root, "ig.ini")
    if not ini_file.is_file():
        raise Exception(f"<ini_file> '{ini_file}' must exist")

    bump_ig_version(ini_file, new_version)
    for f in site_root.rglob("*.json"):
        bump_resource_version(f, new_version, our_urls)
