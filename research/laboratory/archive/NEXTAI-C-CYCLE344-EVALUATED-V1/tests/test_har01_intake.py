import importlib.util
import zipfile
from pathlib import Path

import pytest


def intake():
    path = Path(__file__).resolve().parents[1] / "scripts/acquire_har01.py"
    spec = importlib.util.spec_from_file_location("har01_intake", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_archive_is_not_extracted(tmp_path):
    path = tmp_path / "native.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("UCI HAR Dataset/train/subject_train.txt", "1\n")
    archive, nested = intake().data_archive(path, {"maximum_expanded_bytes": 1024})
    with archive:
        assert not nested
        assert archive.read("UCI HAR Dataset/train/subject_train.txt") == b"1\n"
    assert list(tmp_path.iterdir()) == [path]


def test_archive_expansion_bound_checked_before_data(tmp_path):
    path = tmp_path / "native.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("UCI HAR Dataset/train/subject_train.txt", "1\n" * 2048)
    with pytest.raises(ValueError, match="expanded bound"):
        intake().data_archive(path, {"maximum_expanded_bytes": 1024})


def test_no_unspecified_nested_archive(tmp_path):
    path = tmp_path / "native.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("another-dataset.zip", "not HAR")
    with pytest.raises(ValueError, match="one bounded native HAR"):
        intake().data_archive(path, {"maximum_expanded_bytes": 1024, "maximum_download_bytes": 1024})
