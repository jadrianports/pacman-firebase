"""Developer release tool (NOT shipped). Cuts an auto-updatable release:

  python release.py --init     # one-time: generate TUF keys + root.json, init repo
  python release.py            # build + zip + add signed bundle to the TUF repo

Operator then deploys ./repo to Firebase Hosting /updates and compiles the installer.
See RELEASE.md. tufup + its keys are imported/used only here, never in the game."""
import argparse
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.join(ROOT, "repo")
KEYS_DIR = os.path.join(ROOT, "tuf-keys")          # gitignored — private keys
DIST_APP = os.path.join(ROOT, "dist", "pacman")
ROOT_JSON_DEST = os.path.join(ROOT, "assets", "tuf", "root.json")
APP_NAME = "Pacman"


def build_parser():
    p = argparse.ArgumentParser(description="Cut an auto-updatable Pac-Man release.")
    p.add_argument("--init", action="store_true",
                   help="one-time: generate TUF keys + root.json and initialise the repo")
    return p


def _app_version():
    sys.path.insert(0, ROOT)
    import settings
    return settings.APP_VERSION


def init_repo():
    """One-time TUF setup: keypairs for the four roles, initial metadata, and the
    public root.json copied into assets/tuf so the build can bundle it."""
    from tufup.repo import Repository
    os.makedirs(KEYS_DIR, exist_ok=True)
    repo = Repository(
        app_name=APP_NAME,
        repo_dir=REPO_DIR,
        keys_dir=KEYS_DIR,
    )
    repo.initialize()  # generates keys + root/targets/snapshot/timestamp metadata
    os.makedirs(os.path.dirname(ROOT_JSON_DEST), exist_ok=True)
    shutil.copyfile(os.path.join(REPO_DIR, "metadata", "root.json"), ROOT_JSON_DEST)
    print(f"TUF repo initialised. PUBLIC root.json -> {ROOT_JSON_DEST} (commit it).")
    print(f"PRIVATE keys -> {KEYS_DIR} (gitignored). BACK THESE UP. Do NOT lose root key.")


def cut_release():
    version = _app_version()
    print(f"Building Pac-Man {version} ...")
    subprocess.check_call([sys.executable, os.path.join(ROOT, "build.py")])

    zip_base = os.path.join(ROOT, "dist", "pacman")
    shutil.make_archive(zip_base, "zip", DIST_APP)   # dist/pacman.zip (grab-and-go)
    print(f"Zipped -> {zip_base}.zip")

    from tufup.repo import Repository
    repo = Repository(app_name=APP_NAME, repo_dir=REPO_DIR, keys_dir=KEYS_DIR)
    repo.add_bundle(new_bundle_dir=DIST_APP, new_version=version)
    repo.publish_changes(private_key_dirs=[KEYS_DIR])
    print(f"Published {version} to TUF repo {REPO_DIR}.")
    print("Next (operator): deploy ./repo to Firebase /updates, compile installer/pacman.iss,")
    print("publish dist/pacman.zip + pacman-setup.exe. See RELEASE.md.")


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.init:
        init_repo()
    else:
        cut_release()


if __name__ == "__main__":
    main()
