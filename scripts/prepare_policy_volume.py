"""Run with python -I -S before dropping root; never imports application code."""
import os

MOUNT = "/var/lib/sentinelayer-policy"
STATE = MOUNT + "/runtime"


def prepare_child(mount: str, uid: int, gid: int) -> None:
    # Directory descriptors keep mkdir/open/chown bound to the inspected directory.
    parent = os.open(mount, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        try:
            os.mkdir("runtime", mode=0o700, dir_fd=parent)
        except FileExistsError:
            pass
        child = os.open("runtime", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        try:
            os.fchown(child, uid, gid)
            # This is a directory: owner-only traversal/write is required by the gateway.
            # nosemgrep: python.lang.security.audit.insecure-file-permissions.insecure-file-permissions
            os.fchmod(child, 0o700)
        finally:
            os.close(child)
    finally:
        os.close(parent)


def main() -> None:
    if os.geteuid() != 0:
        raise RuntimeError("Volume initialization requires root")
    if (os.environ.get("GATEWAY_POLICY_STATE_DIR") != STATE
            or os.environ.get("RAILWAY_VOLUME_MOUNT_PATH") != MOUNT
            or not os.path.ismount(MOUNT) or os.path.islink(MOUNT)):
        raise RuntimeError("A dedicated mounted policy volume is required")
    prepare_child(MOUNT, 1000, 1000)
    print("Dedicated policy volume initialized; dropping runtime privileges", flush=True)


if __name__ == "__main__":
    main()
