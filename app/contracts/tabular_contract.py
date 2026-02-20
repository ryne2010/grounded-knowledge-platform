from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

MAX_CONTRACT_BYTES = 64 * 1024

ColumnType = Literal["string", "int", "float", "bool", "timestamp", "date"]
ValidationStatus = Literal["pass", "warn", "fail"]

_BOOL_TRUE = {"true", "t", "yes", "y", "1"}
_BOOL_FALSE = {"false", "f", "no", "n", "0"}


class ContractChecks(BaseModel):
    min_rows: int | None = None
    max_null_fraction: dict[str, float] = Field(default_factory=dict)

    @field_validator("min_rows")
    @classmethod
    def _validate_min_rows(cls, value: int | None) -> int | None:
        if value is None:
            return value
        if value < 0:
            raise ValueError("checks.min_rows must be >= 0")
        return value

    @field_validator("max_null_fraction")
    @classmethod
    def _validate_max_null_fraction(cls, value: dict[str, float]) -> dict[str, float]:
        out: dict[str, float] = {}
        for key, frac in value.items():
            f = float(frac)
            if f < 0.0 or f > 1.0:
                raise ValueError(f"checks.max_null_fraction[{key}] must be in [0,1]")
            out[str(key)] = f
        return out


class ContractColumn(BaseModel):
    name: str
    type: ColumnType
    required: bool = False
    unique: bool = False

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        v = value.strip()
        if not v:
            raise ValueError("column.name must be non-empty")
        return v


class TabularContract(BaseModel):
    version: int
    name: str
    owner: str | None = None
    strict: bool = False
    columns: list[ContractColumn] = Field(default_factory=list)
    checks: ContractChecks = Field(default_factory=ContractChecks)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        v = value.strip()
        if not v:
            raise ValueError("name must be non-empty")
        return v

    @model_validator(mode="after")
    def _validate_contract(self) -> "TabularContract":
        if self.version != 1:
            raise ValueError("Only contract version=1 is supported")
        if not self.columns:
            raise ValueError("columns must contain at least one entry")
        seen: set[str] = set()
        for c in self.columns:
            key = c.name.strip().lower()
            if key in seen:
                raise ValueError(f"Duplicate column name in contract: {c.name}")
            seen.add(key)
        return self


@dataclass(frozen=True)
class TabularSnapshot:
    headers: list[str]
    rows: list[dict[str, str]]
    inferred_types: dict[str, ColumnType]
    schema_fingerprint: str


@dataclass(frozen=True)
class ContractValidationResult:
    status: ValidationStatus
    errors: list[str]
    warnings: list[str]


def _norm(name: str) -> str:
    return name.strip().lower()


def _is_int(value: str) -> bool:
    try:
        int(value)
        return True
    except Exception:
        return False


def _is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except Exception:
        return False


def _is_bool(value: str) -> bool:
    return value.strip().lower() in _BOOL_TRUE.union(_BOOL_FALSE)


def _is_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except Exception:
        return False


def _is_timestamp(value: str) -> bool:
    v = value.strip()
    try:
        if v.endswith("Z"):
            v = v[:-1] + "+00:00"
        datetime.fromisoformat(v)
        return True
    except Exception:
        return False


def infer_column_type(values: list[str]) -> ColumnType:
    clean = [v.strip() for v in values if str(v).strip() != ""]
    if not clean:
        return "string"
    if all(_is_bool(v) for v in clean):
        return "bool"
    if all(_is_int(v) for v in clean):
        return "int"
    if all(_is_float(v) for v in clean):
        return "float"
    if all(_is_date(v) for v in clean):
        return "date"
    if all(_is_timestamp(v) for v in clean):
        return "timestamp"
    return "string"


def schema_fingerprint(headers: list[str], inferred_types: dict[str, ColumnType]) -> str:
    normalized = [
        {
            "name": _norm(h),
            "type": inferred_types.get(h, "string"),
        }
        for h in headers
    ]
    payload = json.dumps({"columns": normalized}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_snapshot(headers: list[str], rows: list[dict[str, str]]) -> TabularSnapshot:
    inferred: dict[str, ColumnType] = {}
    for h in headers:
        values = [r.get(h, "") for r in rows]
        inferred[h] = infer_column_type(values)
    fp = schema_fingerprint(headers, inferred)
    return TabularSnapshot(headers=headers, rows=rows, inferred_types=inferred, schema_fingerprint=fp)


def load_contract(raw: bytes) -> tuple[TabularContract, str]:
    if len(raw) > MAX_CONTRACT_BYTES:
        raise ValueError(f"Contract file too large (max {MAX_CONTRACT_BYTES} bytes)")
    if not raw:
        raise ValueError("Contract file is empty")

    try:
        import yaml  # type: ignore[import-untyped]
    except Exception as e:
        raise RuntimeError("YAML parsing requires PyYAML") from e

    try:
        payload = yaml.safe_load(raw.decode("utf-8"))
    except Exception as e:
        raise ValueError(f"Invalid contract YAML: {e}") from e

    if not isinstance(payload, dict):
        raise ValueError("Contract YAML must be a mapping/object")

    contract = TabularContract.model_validate(payload)
    return contract, hashlib.sha256(raw).hexdigest()


def _type_is_compatible(actual: ColumnType, expected: ColumnType) -> bool:
    if actual == expected:
        return True
    if expected == "float" and actual == "int":
        return True
    if expected == "timestamp" and actual == "date":
        return True
    return False


def validate_snapshot(snapshot: TabularSnapshot, contract: TabularContract) -> ContractValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    header_norm_to_raw = {_norm(h): h for h in snapshot.headers}
    snapshot_norm = set(header_norm_to_raw.keys())
    contract_cols = {_norm(c.name): c for c in contract.columns}
    contract_set = set(contract_cols.keys())

    missing_required: list[str] = []
    for norm_name, column in contract_cols.items():
        if column.required and norm_name not in snapshot_norm:
            missing_required.append(column.name)
    if missing_required:
        errors.append(f"Missing required columns: {', '.join(sorted(missing_required))}")

    if contract.strict:
        extra = sorted(snapshot_norm - contract_set)
        if extra:
            errors.append(f"Unexpected columns (strict mode): {', '.join(extra)}")

    for norm_name, column in contract_cols.items():
        raw_header = header_norm_to_raw.get(norm_name)
        if not raw_header:
            continue
        actual_type = snapshot.inferred_types.get(raw_header, "string")
        expected_type = column.type
        if not _type_is_compatible(actual_type, expected_type):
            errors.append(f"Column `{column.name}` expected type `{expected_type}` but found `{actual_type}`")

        if column.unique:
            seen: set[str] = set()
            dupes = 0
            for row in snapshot.rows:
                value = str(row.get(raw_header, "")).strip()
                if not value:
                    continue
                if value in seen:
                    dupes += 1
                seen.add(value)
            if dupes:
                errors.append(f"Column `{column.name}` expected unique values but found duplicates ({dupes})")

    row_count = len(snapshot.rows)
    if contract.checks.min_rows is not None and row_count < contract.checks.min_rows:
        errors.append(f"Row count {row_count} is below min_rows={contract.checks.min_rows}")

    for col_name, max_frac in contract.checks.max_null_fraction.items():
        raw_header = header_norm_to_raw.get(_norm(col_name))
        if raw_header is None:
            errors.append(f"Column `{col_name}` not found for checks.max_null_fraction")
            continue
        if row_count == 0:
            frac = 1.0
        else:
            nulls = 0
            for row in snapshot.rows:
                value = str(row.get(raw_header, "")).strip()
                if not value:
                    nulls += 1
            frac = float(nulls) / float(row_count)
        if frac > float(max_frac):
            errors.append(
                f"Column `{col_name}` null fraction {frac:.3f} exceeds max_null_fraction={float(max_frac):.3f}"
            )

    status: ValidationStatus
    if errors:
        status = "fail"
    elif warnings:
        status = "warn"
    else:
        status = "pass"
    return ContractValidationResult(status=status, errors=errors, warnings=warnings)
