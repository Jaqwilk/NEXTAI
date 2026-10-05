"""Cycle320 publisher metadata only: never download or decode target samples."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import urllib.request

from nextai_autoresearch.utils import atomic_write_json, utc_now


ROOT = Path(__file__).resolve().parents[1]
LIMIT = 4 * 1024 * 1024
FLOOR = 10 * 1024**3
USED = 0
REQUESTS = []


def request(url, *, method="GET", byte_range=None, cap=32768):
    global USED
    free = shutil.disk_usage(ROOT).free
    assert free - (LIMIT - USED) >= FLOOR
    headers = {"User-Agent": "NEXTAI metadata-only research"}
    if byte_range:
        headers["Range"] = f"bytes={byte_range[0]}-{byte_range[1]}"
    with urllib.request.urlopen(urllib.request.Request(url, method=method, headers=headers), timeout=20) as response:
        if byte_range:
            assert response.status == 206, "Range ignored: stop before reading target payload"
            assert response.headers["Content-Range"].startswith(f"bytes {byte_range[0]}-{byte_range[1]}/")
        data = response.read(cap + 1) if method != "HEAD" else b""
        assert len(data) <= cap and USED + len(data) <= LIMIT
        USED += len(data)
        REQUESTS.append(dict(url=url,method=method,range=byte_range,status=response.status,
                             headers=dict(response.headers),bytes_read=len(data),
                             sha256=hashlib.sha256(data).hexdigest(),free_before=free,
                             free_after=shutil.disk_usage(ROOT).free))
        return data, response.headers


def main():
    output = ROOT / "research/laboratory/FAMILY2-CYCLE320-METADATA-V1.json"
    assert not output.exists()
    original, _ = request("https://archive.ics.uci.edu/ml/machine-learning-databases/optdigits/optdigits-orig.names")
    reduced, _ = request("https://archive.ics.uci.edu/ml/machine-learning-databases/optdigits/optdigits.names")
    assamese_url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00208/Online%20Handwritten%20Assamese%20Characters%20Dataset.rar"
    _, assamese = request(assamese_url, method="HEAD")
    nist_url = "https://s3.amazonaws.com/nist-srd/SD19/by_write.zip"
    _, nist = request(nist_url, method="HEAD")
    size = int(nist["Content-Length"])
    tail, _ = request(nist_url, byte_range=(size-65536,size-1), cap=65536)
    position = tail.rfind(b"PK\x05\x06")
    assert position >= 0
    eocd = struct.unpack_from("<4s4H2IH", tail, position)
    count, cd_size, offset = eocd[4:7]
    if 0xFFFFFFFF in (cd_size,offset) or count == 0xFFFF:
        z = tail.rfind(b"PK\x06\x06")
        assert z >= 0, "ZIP64 directory descriptor not in bounded tail"
        entry = struct.unpack_from("<4sQ2H2I4Q", tail, z)
        count, cd_size, offset = entry[7:10]
    end = offset + min(cd_size, 1536*1024) - 1
    directory, _ = request(nist_url, byte_range=(offset,end), cap=1536*1024)
    parsed=[]; cursor=0; writers={}
    while cursor+46 <= len(directory) and directory[cursor:cursor+4] == b"PK\x01\x02":
        row=struct.unpack_from("<4s6H3I5H2I",directory,cursor)
        stop=cursor+46+sum(row[10:13])
        if stop>len(directory):
            break
        name=directory[cursor+46:cursor+46+row[10]].decode("utf-8")
        assert not name.startswith("/") and ".." not in name.split("/")
        match=re.search(r"/f(\d{4})_\d{2}/",name)
        if match and name.endswith(".png"):
            writers[match[1]]=writers.get(match[1],0)+1
        parsed.append(dict(name=name,compressed_bytes=row[8],uncompressed_bytes=row[9],crc32=row[7],local_offset=row[16]))
        cursor=stop
    # Raw bytes are ZIP directory entries only, no local file entry/image/label.
    metadata_root=ROOT/"research/laboratory/archive/FAMILY2-cycle320-metadata-V1"
    metadata_root.mkdir(parents=True,exist_ok=False)
    for name,data in (("optdigits.names.txt",reduced),("optdigits-orig.names.txt",original),("nist-central-directory-prefix.bin",directory),("nist-directory-tail.bin",tail)):
        (metadata_root/name).write_bytes(data)
    result=dict(created_at=utc_now(),schema_version=1,metadata_only=True,numeric_samples_read=0,
                requests=REQUESTS,bytes_read=USED,download_cap_bytes=LIMIT,
                assamese_archive_bytes=int(assamese["Content-Length"]) if assamese["Content-Length"] else None,
                assamese_archive_size_status="Exact HEAD length when supplied; otherwise publisher7.7MB estimate only, future stream requires frozen cap",
                nist_archive_bytes=size,nist_directory_bytes=cd_size,nist_directory_offset=offset,
                nist_total_directory_entries=count,nist_prefix_entries=len(parsed),
                nist_writer_png_counts_from_partial_directory=writers,
                nist_first30_writers_min_png=min((writers.get(f"{i:04d}",0) for i in range(30)),default=0),
                nist_complete_index_read=False,partial_entries=parsed,
                raw_metadata_path=metadata_root.relative_to(ROOT).as_posix(),
                metadata_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in metadata_root.iterdir()},
                disk_free_after=shutil.disk_usage(ROOT).free)
    atomic_write_json(output,result)
    print(json.dumps({k:v for k,v in result.items() if k not in {"partial_entries","requests","nist_writer_png_counts_from_partial_directory"}}))


if __name__ == "__main__":
    main()
