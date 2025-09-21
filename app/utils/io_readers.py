from __future__ import annotations

import csv
import io
import re
from typing import Dict, List, NamedTuple, Sequence, Tuple, Union

import pandas as pd


NUM_RE = re.compile(r"^\s*[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?\s*$")
NUMERIC_TOKEN_RE = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


class TableReadResult(NamedTuple):
    """Container describing the parsed table and any leading headers."""

    dataframe: pd.DataFrame
    header_lines: List[str]
    column_labels: List[str]
    delimiter: str
    orientation: str


def sniff_delimiter(sample: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;| ")
        return dialect.delimiter
    except csv.Error:
        return ","


def find_header_start(lines: Sequence[str]) -> int:
    """Return the index of the first numeric row inside ``lines``."""

    for index, line in enumerate(lines):
        for delim in [",", "\t", ";", "|", " "]:
            tokens = [token for token in line.strip().split(delim) if token != ""]
            if len(tokens) < 2:
                continue
            if NUM_RE.match(tokens[0] or "") and NUM_RE.match(tokens[1] or ""):
                return index
    return 0


def _parse_column_labels(line: str, delimiter: str) -> List[str]:
    """Attempt to extract column labels from a header row."""

    stripped = line.strip().lstrip("#").strip()
    if not stripped:
        return []
    tokens = [token.strip() for token in stripped.split(delimiter)]
    tokens = [token for token in tokens if token]
    if len(tokens) < 2:
        return []
    if all(NUM_RE.match(token) for token in tokens[:2]):
        return []
    return tokens


def _extract_numeric_tokens(text: str) -> List[float]:
    numbers: List[float] = []
    for token in NUMERIC_TOKEN_RE.findall(text):
        try:
            numbers.append(float(token))
        except ValueError:
            continue
    return numbers


def _normalise_vertical_label(label: str, seen: Dict[str, int]) -> str:
    cleaned = label.strip().lstrip("#").strip()
    cleaned = cleaned.rstrip(":")
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        cleaned = "column"
    base = cleaned
    counter = seen.get(base, 0)
    if counter:
        cleaned = f"{base}_{counter + 1}"
    seen[base] = counter + 1
    return cleaned


def _parse_vertical_series(lines: Sequence[str]) -> Tuple[pd.DataFrame, List[str]] | None:
    sections: List[Tuple[str, List[float]]] = []
    current_label: str | None = None
    current_values: List[float] = []

    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            stripped = stripped.lstrip("#").strip()
            if not stripped:
                continue

        label_part: str | None = None
        numeric_fragment: str = stripped

        for separator in (":", "="):
            if separator in stripped:
                left, right = stripped.split(separator, 1)
                if any(char.isalpha() for char in left):
                    label_part = left.strip()
                    numeric_fragment = right.strip()
                    break

        match = NUMERIC_TOKEN_RE.search(stripped)
        if label_part is None and match:
            prefix = stripped[: match.start()]
            if any(char.isalpha() for char in prefix):
                label_part = prefix.strip()
                numeric_fragment = stripped[match.start() :]

        tokens = _extract_numeric_tokens(numeric_fragment)

        if label_part is not None:
            if current_label and current_values:
                sections.append((current_label, current_values.copy()))
            current_label = label_part.strip().rstrip(":")
            current_values = []
            if tokens:
                current_values.extend(tokens)
            continue

        if tokens:
            if current_label is None:
                continue
            current_values.extend(tokens)
            continue

        if any(char.isalpha() for char in stripped):
            if current_label and current_values:
                sections.append((current_label, current_values.copy()))
            current_label = stripped
            current_values = []

    if current_label and current_values:
        sections.append((current_label, current_values.copy()))

    filtered = [(label, values) for label, values in sections if len(values) >= 2]
    if len(filtered) < 2:
        return None

    min_length = min(len(values) for _, values in filtered)
    seen_labels: Dict[str, int] = {}
    data: Dict[str, List[float]] = {}
    column_labels: List[str] = []

    for label, values in filtered:
        normalised = _normalise_vertical_label(label, seen_labels)
        truncated = [float(value) for value in values[:min_length]]
        data[normalised] = truncated
        column_labels.append(normalised)

    dataframe = pd.DataFrame.from_dict(data, orient="columns")
    dataframe = dataframe.dropna().reset_index(drop=True)

    if dataframe.shape[1] < 2 or dataframe.empty:
        return None

    return dataframe, column_labels


def read_table(
    file_bytes: bytes,
    *,
    include_header: bool = False,
) -> Union[pd.DataFrame, TableReadResult]:
    """Parse tabular ASCII spectral data into a dataframe.

    Parameters
    ----------
    file_bytes:
        Raw file payload.
    include_header:
        When ``True`` the return value includes any leading header lines and the
        detected delimiter in addition to the dataframe.
    """

    text = io.BytesIO(file_bytes).read().decode("utf-8", errors="ignore")
    lines = text.splitlines()
    if not lines:
        raise ValueError("No content available for table parsing.")

    start_index = find_header_start(lines)
    header_lines = lines[:start_index]

    data_start = start_index
    if start_index == 0:
        prefix: List[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "!", ";")):
                prefix.append(line)
                continue
            break
        header_lines = prefix
        data_start = len(prefix)

    data_lines = lines[data_start:]
    if not any(line.strip() for line in data_lines):
        raise ValueError("No data rows detected in the ASCII table.")

    sample = "\n".join(data_lines[:10])
    delimiter = sniff_delimiter(sample) if sample.strip() else ","

    column_labels: List[str] = []
    if data_start > 0 and data_start <= len(lines):
        header_index = data_start - 1
        if header_index >= 0:
            column_labels = _parse_column_labels(lines[header_index], delimiter)

    orientation = "row"
    parse_error: Exception | None = None

    try:
        dataframe = pd.read_csv(
            io.StringIO("\n".join(data_lines)),
            sep=delimiter,
            engine="python",
            comment="#",
            skip_blank_lines=True,
            header=None,
        )
        if dataframe.shape[1] < 2:
            raise ValueError("Expected at least two columns (wavelength and flux).")

        if column_labels and len(column_labels) >= dataframe.shape[1]:
            dataframe.columns = column_labels[: dataframe.shape[1]]
        else:
            dataframe.columns = [str(col) for col in dataframe.columns]
            column_labels = list(dataframe.columns)

        numeric_cols = dataframe.columns[:2]
        for column in numeric_cols:
            dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

        dataframe = dataframe.dropna(subset=list(numeric_cols)).reset_index(drop=True)
        if dataframe.empty:
            raise ValueError("No numeric samples found in the ASCII table.")
    except Exception as exc:
        parse_error = exc
        column_labels = []
        dataframe = None  # type: ignore[assignment]

    if parse_error or dataframe is None:
        vertical = _parse_vertical_series(data_lines)
        if not vertical:
            raise parse_error if parse_error else ValueError("Unable to parse ASCII spectral table.")
        dataframe, column_labels = vertical
        delimiter = "vertical"
        orientation = "columnar"
    else:
        orientation = "row"

    if include_header:
        return TableReadResult(dataframe, header_lines, column_labels, delimiter, orientation)
    return dataframe
