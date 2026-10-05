"""Restore the exact published native record; never overwrite an existing result."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ID = "EXP-20261005-0001"
RELATIVE = f"research/results/{ID}.json"

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def main(root):
    root=root.resolve()
    record=json.loads((root/f"research/results/{ID}-publication.json").read_text(encoding="utf-8"))
    native=(root/RELATIVE).resolve();bundle=(root/(RELATIVE+".gz")).resolve()
    assert native.is_relative_to(root) and bundle.is_relative_to(root)
    assert record["experiment_id"]==ID and record["native_path"]==RELATIVE
    assert record["bundle_path"]==RELATIVE+".gz"
    if native.exists():
        if digest(native)!=record["native_sha256"]:raise ValueError("Existing native record differs; preserved without overwrite")
        print("Native record already matches its immutable hash");return
    if digest(bundle)!=record["bundle_sha256"]:raise ValueError("Published bundle hash mismatch")
    if shutil.disk_usage(native.parent).free-record["native_bytes"]<10*1024**3:raise OSError("Restoration would leave less than10GiB free")
    fd,name=tempfile.mkstemp(prefix=ID+"-restore-",suffix=".tmp",dir=native.parent);temporary=Path(name)
    try:
        h=hashlib.sha256();size=0
        with os.fdopen(fd,"wb") as out,gzip.open(bundle,"rb") as source:
            for block in iter(lambda:source.read(1024*1024),b""):
                size+=len(block)
                if size>record["native_bytes"]:raise ValueError("Decompressed record exceeds its frozen size")
                h.update(block);out.write(block)
            out.flush();os.fsync(out.fileno())
        if size!=record["native_bytes"] or h.hexdigest()!=record["native_sha256"]:raise ValueError("Native record size/hash mismatch")
        try:os.link(temporary,native)
        except FileExistsError:
            if digest(native)!=record["native_sha256"]:raise ValueError("Concurrent existing record differs; no overwrite")
        print("Native record restored with exact original bytes:",native)
    finally:
        assert temporary.parent.resolve()==native.parent
        temporary.unlink()

if __name__=="__main__":
    main(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1])
