#!/usr/bin/env python3

"""
SPDX-FileCopyrightText: 2024 Adithya R
SPDX-License-Identifier: MIT
"""

import requests
import subprocess
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) != 2:
    print("Usage:\n\t./merge-tag.py <tag>")
    sys.exit(1)

tag = sys.argv[1]

modules = {
    "audio-kernel": "https://git.codelinaro.org/clo/la/platform/vendor/qcom/opensource/audio-kernel-ar",
    "camera-kernel": "https://git.codelinaro.org/clo/la/platform/vendor/opensource/camera-kernel",
    "cvp-kernel": "https://git.codelinaro.org/clo/la/platform/vendor/opensource/cvp-kernel",
    "dataipa": "https://git.codelinaro.org/clo/la/platform/vendor/opensource/dataipa",
    "datarmnet": "https://git.codelinaro.org/clo/la/platform/vendor/qcom/opensource/datarmnet",
    "datarmnet-ext": "https://git.codelinaro.org/clo/la/platform/vendor/qcom/opensource/datarmnet-ext",
    "display-drivers": "https://git.codelinaro.org/clo/la/platform/vendor/opensource/display-drivers",
    "eva-kernel": "https://git.codelinaro.org/clo/la/platform/vendor/opensource/eva-kernel",
    "mmrm-driver": "https://git.codelinaro.org/clo/la/platform/vendor/opensource/mmrm-driver",
    "video-driver": "https://git.codelinaro.org/clo/la/platform/vendor/opensource/video-driver",
    "wlan/fw-api": "https://git.codelinaro.org/clo/la/platform/vendor/qcom-opensource/wlan/fw-api",
    "wlan/qca-wifi-host-cmn": "https://git.codelinaro.org/clo/la/platform/vendor/qcom-opensource/wlan/qca-wifi-host-cmn",
    "wlan/qcacld-3.0": "https://git.codelinaro.org/clo/la/platform/vendor/qcom-opensource/wlan/qcacld-3.0",
}

# These are in a separate manifest
separated_techpacks = {
    "camera-kernel": "camera",
    "display-drivers": "display",
    "mmrm-driver": "video",
    "video-driver": "video",
}

# Parses the module revision from a techpack manifest
def get_revision_from_manifest(techpack, tp_tag, path):
    response = requests.get(f"https://git.codelinaro.org/clo/la/techpack/{techpack}/manifest/-/raw/release/{tp_tag}.xml")
    if response.status_code != 200:
        print("Failed to load", techpack, "manifest!")
        return

    root = ET.fromstring(response.content)

    for project in root.findall('project'):
        repo_path = project.get('path')
        if repo_path is not None and repo_path.endswith(path):
            return project.get('revision')

    print("Failed to obtain revision from", techpack, "techpack manifest!")

# Obtains the tag for the given techpack manifest from vendor manifest
def get_techpack_tag(techpack):
    refs = manifest_root.find('refs')
    if refs is not None:
        for image in refs:
            project = image.get('project')
            if project == "techpack/" + techpack + "/manifest":
                return(image.get('tag'))

    print("Failed to obtain", techpack, "techpack tag from manifest!")

def get_revision(path):
    if path in separated_techpacks.keys():
        techpack = separated_techpacks.get(path)
        tp_tag = get_techpack_tag(techpack)
        if tp_tag is not None:
            print("Techpack tag:", tp_tag)
            return get_revision_from_manifest(techpack, tp_tag, path)
    else:
        return tag

# Here we go
response = requests.get(f"https://git.codelinaro.org/clo/la/la/vendor/manifest/-/raw/release/{tag}.xml")
if response.status_code != 200:
    print("Tag does not exist!")
    sys.exit(1)

# print(response.content)
manifest_root = ET.fromstring(response.content)

for path, url in modules.items():
    print("\nMerging", path)

    revision = get_revision(path)
    if revision is None:
        print("Failed to obtain revision, bailing!")
        break

    print("URL:", url)
    print("Revision:", revision)

    if revision == tag:
        commit_msg = f"{path}: Merge tag \'{tag}\'"
    else:
        commit_msg = f"{path}: Merge {revision}\n\nFrom vendor tag: \'{tag}\'"

    try:
        subprocess.run([
            "git",
            "subtree",
            "pull",
            "-P",
            "qcom/opensource/" + path,
            "-m",
            commit_msg,
            url,
            revision
        ], check=True)
    except subprocess.CalledProcessError as e:
        print("Failed to merge!")
        break

    print("Succesfully merged!")
