import hashlib
import importlib.util
import json
import struct
from pathlib import Path


MODULE_PATH = Path(__file__).parents[2] / "packaging" / "windows" / "validate_pe_architecture.py"
SPEC = importlib.util.spec_from_file_location("validate_pe_architecture", MODULE_PATH)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def write_pe(path: Path, machine: int, suffix: bytes = b"") -> bytes:
    data = bytearray(0x86)
    data[0:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<H", data, 0x84, machine)
    data.extend(suffix)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return bytes(data)


def test_arm64_x64_and_malformed(tmp_path, capsys):
    write_pe(tmp_path / "arm.exe", 0xAA64)
    assert validator.validate(tmp_path / "arm.exe", "arm64", [], None) == 0
    assert validator.validate(tmp_path / "arm.exe", "x64", [], None) == 1
    malformed = tmp_path / "broken.dll"
    malformed.write_bytes(b"MZ")
    assert validator.validate(malformed, "arm64", [], None) == 1
    assert "truncated DOS header" in capsys.readouterr().err


def test_unsupported_architecture_fails_cleanly(tmp_path, capsys):
    write_pe(tmp_path / "arm.exe", 0xAA64)
    assert validator.validate(tmp_path, "sparc", [], None) == 1
    assert "unsupported architecture: sparc" in capsys.readouterr().err


def test_recursive_ordering_and_deterministic_manifest(tmp_path):
    z_data = write_pe(tmp_path / "z.DLL", 0xAA64, b"z")
    a_data = write_pe(tmp_path / "Nested" / "a.exe", 0xAA64, b"a")
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    assert validator.validate(tmp_path, "arm64", [], first) == 0
    assert validator.validate(tmp_path, "arm64", [], second) == 0
    assert first.read_bytes() == second.read_bytes()
    manifest = json.loads(first.read_text(encoding="utf-8"))
    assert [item["path"] for item in manifest["files"]] == ["Nested/a.exe", "z.DLL"]
    assert manifest["files"][0]["sha256"] == hashlib.sha256(a_data).hexdigest()
    assert manifest["files"][1]["sha256"] == hashlib.sha256(z_data).hexdigest()


def test_mixed_machine_reports_all_failures(tmp_path, capsys):
    write_pe(tmp_path / "bad-one.dll", 0x8664)
    write_pe(tmp_path / "bad-two.pyd", 0x014C)
    assert validator.validate(tmp_path, "arm64", [], None) == 1
    errors = capsys.readouterr().err
    assert "bad-one.dll" in errors
    assert "bad-two.pyd" in errors


def test_zero_candidates_and_required_python3_dll(tmp_path, capsys):
    assert validator.validate(tmp_path, "arm64", ["python3.dll"], None) == 1
    errors = capsys.readouterr().err
    assert "no PE candidates" in errors
    assert "missing required PE: python3.dll" in errors


def test_missing_root_reports_missing_path(tmp_path, capsys):
    missing = tmp_path / "missing"
    assert validator.validate(missing, "arm64", [], None) == 1
    errors = capsys.readouterr().err
    assert "path does not exist" in errors
    assert "no PE candidates" not in errors


def test_validation_without_manifest_does_not_hash(tmp_path, monkeypatch):
    write_pe(tmp_path / "arm.exe", 0xAA64)

    def unexpected_hash(_path):
        raise AssertionError("hashing is unnecessary without a manifest")

    monkeypatch.setattr(validator, "file_size_and_sha256", unexpected_hash)
    assert validator.validate(tmp_path, "arm64", [], None) == 0


def test_missing_required_path_fails(tmp_path, capsys):
    write_pe(tmp_path / "UltiMaker-Cura.exe", 0xAA64)
    assert validator.validate(
        tmp_path, "arm64", ["UltiMaker-Cura.exe", "python3.dll"], None
    ) == 1
    assert "missing required PE: python3.dll" in capsys.readouterr().err


def test_required_path_accepts_windows_separators_on_any_host(tmp_path):
    write_pe(tmp_path / "Nested" / "a.exe", 0xAA64)
    assert validator.validate(tmp_path, "arm64", [r"Nested\a.exe"], None) == 0
