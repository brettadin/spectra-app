from __future__ import annotations
import io, csv, re
import pandas as pd
import numpy as np

NUM_RE = re.compile(r'^\s*[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?\s*$')

def sniff_delimiter(sample: str) -> str:
    dialect = csv.Sniffer().sniff(sample, delimiters=",\t;| ")
    return dialect.delimiter

def find_header_start(lines):
    # Find first line with at least two numeric-like tokens when split by common delims
    for i, line in enumerate(lines):
        for delim in [",","\t",";","|"," "]:
            toks = [t for t in line.strip().split(delim) if t!=""]
            if len(toks) >= 2 and NUM_RE.match(toks[0] or "") and NUM_RE.match(toks[1] or ""):
                return i
    return 0

def read_table(file_bytes: bytes):
    # Try fast path
    bio = io.BytesIO(file_bytes)
    text = bio.read().decode("utf-8", errors="ignore")
    lines = text.splitlines()
    start = find_header_start(lines)
    sample = "\n".join(lines[start:start+10])
    delim = sniff_delimiter(sample) if sample.strip() else ","
    data = "\n".join(lines[start:])
    df = pd.read_csv(io.StringIO(data), sep=delim, engine="python", comment="#", skip_blank_lines=True, header=None)
    # Ensure at least 2 columns
    if df.shape[1] < 2:
        raise ValueError("Expected at least 2 columns (wavelength, intensity).")
    # Coerce numeric
    df[df.columns[0]] = pd.to_numeric(df[df.columns[0]], errors="coerce")
    df[df.columns[1]] = pd.to_numeric(df[df.columns[1]], errors="coerce")
    df = df.dropna().reset_index(drop=True)
    return df
