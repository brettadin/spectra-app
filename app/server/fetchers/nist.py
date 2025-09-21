"""Fetch spectral line data from the NIST Atomic Spectra Database."""
from __future__ import annotations

"""Client helpers for fetching NIST Atomic Spectra Database line lists."""

import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:  # pragma: no cover - import guard executed at runtime
    import astropy.units as u
    from astroquery.nist import Nist
except Exception as exc:  # pragma: no cover - handled in fetch()
    ASTROQUERY_AVAILABLE = False
    _IMPORT_ERROR: Exception | None = exc
else:  # pragma: no cover - simple constant assignment
    ASTROQUERY_AVAILABLE = True
    _IMPORT_ERROR = None


@dataclass(frozen=True)
class ElementRecord:
    """Mapping between element names, symbols, and atomic numbers."""

    number: int
    symbol: str
    name: str
    aliases: Tuple[str, ...] = ()


_ELEMENTS: Tuple[ElementRecord, ...] = (
    ElementRecord(1, "H", "Hydrogen"),
    ElementRecord(2, "He", "Helium"),
    ElementRecord(3, "Li", "Lithium"),
    ElementRecord(4, "Be", "Beryllium"),
    ElementRecord(5, "B", "Boron"),
    ElementRecord(6, "C", "Carbon"),
    ElementRecord(7, "N", "Nitrogen"),
    ElementRecord(8, "O", "Oxygen"),
    ElementRecord(9, "F", "Fluorine"),
    ElementRecord(10, "Ne", "Neon"),
    ElementRecord(11, "Na", "Sodium"),
    ElementRecord(12, "Mg", "Magnesium"),
    ElementRecord(13, "Al", "Aluminium", ("Aluminum",)),
    ElementRecord(14, "Si", "Silicon"),
    ElementRecord(15, "P", "Phosphorus"),
    ElementRecord(16, "S", "Sulfur", ("Sulphur",)),
    ElementRecord(17, "Cl", "Chlorine"),
    ElementRecord(18, "Ar", "Argon"),
    ElementRecord(19, "K", "Potassium"),
    ElementRecord(20, "Ca", "Calcium"),
    ElementRecord(21, "Sc", "Scandium"),
    ElementRecord(22, "Ti", "Titanium"),
    ElementRecord(23, "V", "Vanadium"),
    ElementRecord(24, "Cr", "Chromium"),
    ElementRecord(25, "Mn", "Manganese"),
    ElementRecord(26, "Fe", "Iron"),
    ElementRecord(27, "Co", "Cobalt"),
    ElementRecord(28, "Ni", "Nickel"),
    ElementRecord(29, "Cu", "Copper"),
    ElementRecord(30, "Zn", "Zinc"),
    ElementRecord(31, "Ga", "Gallium"),
    ElementRecord(32, "Ge", "Germanium"),
    ElementRecord(33, "As", "Arsenic"),
    ElementRecord(34, "Se", "Selenium"),
    ElementRecord(35, "Br", "Bromine"),
    ElementRecord(36, "Kr", "Krypton"),
    ElementRecord(37, "Rb", "Rubidium"),
    ElementRecord(38, "Sr", "Strontium"),
    ElementRecord(39, "Y", "Yttrium"),
    ElementRecord(40, "Zr", "Zirconium"),
    ElementRecord(41, "Nb", "Niobium"),
    ElementRecord(42, "Mo", "Molybdenum"),
    ElementRecord(43, "Tc", "Technetium"),
    ElementRecord(44, "Ru", "Ruthenium"),
    ElementRecord(45, "Rh", "Rhodium"),
    ElementRecord(46, "Pd", "Palladium"),
    ElementRecord(47, "Ag", "Silver"),
    ElementRecord(48, "Cd", "Cadmium"),
    ElementRecord(49, "In", "Indium"),
    ElementRecord(50, "Sn", "Tin"),
    ElementRecord(51, "Sb", "Antimony"),
    ElementRecord(52, "Te", "Tellurium"),
    ElementRecord(53, "I", "Iodine"),
    ElementRecord(54, "Xe", "Xenon"),
    ElementRecord(55, "Cs", "Caesium", ("Cesium",)),
    ElementRecord(56, "Ba", "Barium"),
    ElementRecord(57, "La", "Lanthanum"),
    ElementRecord(58, "Ce", "Cerium"),
    ElementRecord(59, "Pr", "Praseodymium"),
    ElementRecord(60, "Nd", "Neodymium"),
    ElementRecord(61, "Pm", "Promethium"),
    ElementRecord(62, "Sm", "Samarium"),
    ElementRecord(63, "Eu", "Europium"),
    ElementRecord(64, "Gd", "Gadolinium"),
    ElementRecord(65, "Tb", "Terbium"),
    ElementRecord(66, "Dy", "Dysprosium"),
    ElementRecord(67, "Ho", "Holmium"),
    ElementRecord(68, "Er", "Erbium"),
    ElementRecord(69, "Tm", "Thulium"),
    ElementRecord(70, "Yb", "Ytterbium"),
    ElementRecord(71, "Lu", "Lutetium"),
    ElementRecord(72, "Hf", "Hafnium"),
    ElementRecord(73, "Ta", "Tantalum"),
    ElementRecord(74, "W", "Tungsten"),
    ElementRecord(75, "Re", "Rhenium"),
    ElementRecord(76, "Os", "Osmium"),
    ElementRecord(77, "Ir", "Iridium"),
    ElementRecord(78, "Pt", "Platinum"),
    ElementRecord(79, "Au", "Gold"),
    ElementRecord(80, "Hg", "Mercury"),
    ElementRecord(81, "Tl", "Thallium"),
    ElementRecord(82, "Pb", "Lead"),
    ElementRecord(83, "Bi", "Bismuth"),
    ElementRecord(84, "Po", "Polonium"),
    ElementRecord(85, "At", "Astatine"),
    ElementRecord(86, "Rn", "Radon"),
    ElementRecord(87, "Fr", "Francium"),
    ElementRecord(88, "Ra", "Radium"),
    ElementRecord(89, "Ac", "Actinium"),
    ElementRecord(90, "Th", "Thorium"),
    ElementRecord(91, "Pa", "Protactinium"),
    ElementRecord(92, "U", "Uranium"),
    ElementRecord(93, "Np", "Neptunium"),
    ElementRecord(94, "Pu", "Plutonium"),
    ElementRecord(95, "Am", "Americium"),
    ElementRecord(96, "Cm", "Curium"),
    ElementRecord(97, "Bk", "Berkelium"),
    ElementRecord(98, "Cf", "Californium"),
    ElementRecord(99, "Es", "Einsteinium"),
    ElementRecord(100, "Fm", "Fermium"),
    ElementRecord(101, "Md", "Mendelevium"),
    ElementRecord(102, "No", "Nobelium"),
    ElementRecord(103, "Lr", "Lawrencium"),
    ElementRecord(104, "Rf", "Rutherfordium"),
    ElementRecord(105, "Db", "Dubnium"),
    ElementRecord(106, "Sg", "Seaborgium"),
    ElementRecord(107, "Bh", "Bohrium"),
    ElementRecord(108, "Hs", "Hassium"),
    ElementRecord(109, "Mt", "Meitnerium"),
    ElementRecord(110, "Ds", "Darmstadtium"),
    ElementRecord(111, "Rg", "Roentgenium"),
    ElementRecord(112, "Cn", "Copernicium"),
    ElementRecord(113, "Nh", "Nihonium"),
    ElementRecord(114, "Fl", "Flerovium"),
    ElementRecord(115, "Mc", "Moscovium"),
    ElementRecord(116, "Lv", "Livermorium"),
    ElementRecord(117, "Ts", "Tennessine"),
    ElementRecord(118, "Og", "Oganesson"),
)


_SYMBOL_TO_ELEMENT = {rec.symbol.lower(): rec for rec in _ELEMENTS}
_NAME_TO_ELEMENT = {
    rec.name.lower(): rec for rec in _ELEMENTS
}
for rec in _ELEMENTS:
    for alias in rec.aliases:
        _NAME_TO_ELEMENT[alias.lower()] = rec


_ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


class NistUnavailableError(RuntimeError):
    """Raised when astroquery is not available to service NIST requests."""


class NistQueryError(RuntimeError):
    """Raised when a NIST request cannot be satisfied."""


def _roman_to_int(token: str) -> Optional[int]:
    token = token.strip().upper()
    if not token or any(ch not in _ROMAN_VALUES for ch in token):
        return None
    total = 0
    prev = 0
    for ch in reversed(token):
        value = _ROMAN_VALUES[ch]
        if value < prev:
            total -= value
        else:
            total += value
            prev = value
    return total or None


def _int_to_roman(value: int) -> str:
    if value <= 0:
        raise ValueError("Ion stage must be positive")
    numerals = (
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    )
    remaining = value
    parts: List[str] = []
    for magnitude, symbol in numerals:
        while remaining >= magnitude:
            parts.append(symbol)
            remaining -= magnitude
    return "".join(parts)


def _parse_plus_notation(token: str) -> Optional[int]:
    token = token.strip()
    if not token or not set(token) <= {"+"}:
        return None
    return len(token) + 1


def _parse_ion_token(token: str | int | None) -> Optional[int]:
    if token is None:
        return None
    if isinstance(token, int):
        return max(1, token)
    cleaned = token.strip()
    if not cleaned:
        return None
    plus = _parse_plus_notation(cleaned)
    if plus:
        return plus
    if cleaned.isdigit():
        return max(1, int(cleaned))
    roman = _roman_to_int(cleaned)
    if roman:
        return roman
    return None


def _lookup_element(identifier: str) -> ElementRecord:
    token = identifier.strip().lower()
    if not token:
        raise ValueError("Element identifier is empty")
    element = _SYMBOL_TO_ELEMENT.get(token) or _NAME_TO_ELEMENT.get(token)
    if element:
        return element
    raise ValueError(f"Unknown element identifier: {identifier!r}")


def _resolve_spectrum(
    *,
    element: str | None = None,
    linename: str | None = None,
    ion_stage: str | int | None = None,
) -> Tuple[ElementRecord, int, str, str]:
    """Return the element record and formatted spectrum identifier."""

    chosen_element: Optional[ElementRecord] = None
    stage_value: Optional[int] = _parse_ion_token(ion_stage)

    def inspect_tokens(tokens: Iterable[str]) -> None:
        nonlocal chosen_element, stage_value
        for token in tokens:
            token = token.strip()
            if not token:
                continue
            if chosen_element is None:
                try:
                    chosen_element = _lookup_element(token)
                    if chosen_element:
                        continue
                except ValueError:
                    pass
            parsed = _parse_ion_token(token)
            if parsed:
                stage_value = stage_value or parsed

    if linename:
        inspect_tokens(re.split(r"[\s,/;]+", linename))
    if element and not chosen_element:
        inspect_tokens(re.split(r"[\s,/;]+", element))

    if chosen_element is None:
        if linename:
            raise ValueError(f"Could not resolve element from spectrum identifier {linename!r}")
        raise ValueError("Element must be provided")

    stage_value = stage_value or 1
    stage_roman = _int_to_roman(stage_value)
    spectrum = f"{chosen_element.symbol} {stage_roman}"
    label = f"{chosen_element.symbol} {stage_roman} (NIST ASD)"
    return chosen_element, stage_value, stage_roman, spectrum, label


_FLOAT_PATTERN = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")


def _extract_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if math.isnan(value):
            return None
        return float(value)
    text = str(value).strip()
    if not text or text in {"-", "--"}:
        return None
    match = _FLOAT_PATTERN.search(text.replace(",", ""))
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


_ANGSTROM_PATTERN = re.compile(r"(ångstr(?:ö|o)m|angstrom|\bå\b|\[aa\])", re.IGNORECASE)
_NANOMETER_PATTERN = re.compile(r"\bnm\b|nanomet(?:er|re)s?", re.IGNORECASE)
_MICRON_PATTERN = re.compile(
    r"\bµm\b|\bμm\b|\bum\b|micron(?:s)?|micromet(?:er|re)s?", re.IGNORECASE
)


def _guess_scale_from_text(text: Any) -> Optional[float]:
    """Return a conversion factor inferred from textual metadata."""

    if text is None:
        return None
    if isinstance(text, bytes):
        try:
            text = text.decode()
        except Exception:
            text = text.decode(errors="ignore")
    text_str = str(text).strip()
    if not text_str:
        return None
    normalised = text_str.lower()

    if _NANOMETER_PATTERN.search(normalised):
        return 1.0
    if _ANGSTROM_PATTERN.search(normalised):
        return 0.1
    if _MICRON_PATTERN.search(normalised):
        return 1000.0
    return None


def _unit_to_nm_scale(candidate: Any) -> Optional[float]:
    """Resolve a conversion factor from assorted unit representations."""

    if candidate is None:
        return None
    if isinstance(candidate, dict):
        for key in ("unit", "units", "Unit", "Units"):
            if key in candidate:
                scale = _unit_to_nm_scale(candidate[key])
                if scale is not None:
                    return scale
        for value in candidate.values():
            scale = _unit_to_nm_scale(value)
            if scale is not None:
                return scale
        return None
    if isinstance(candidate, (list, tuple, set, frozenset)):
        for item in candidate:
            scale = _unit_to_nm_scale(item)
            if scale is not None:
                return scale
        return None
    if isinstance(candidate, bytes):
        try:
            candidate = candidate.decode()
        except Exception:
            candidate = candidate.decode(errors="ignore")

    if isinstance(candidate, str):
        text_scale = _guess_scale_from_text(candidate)
        if text_scale is not None:
            return text_scale

    try:
        parsed_unit = u.Unit(candidate)
    except Exception:
        return None

    if parsed_unit == u.dimensionless_unscaled:
        return 1.0

    try:
        return (1 * parsed_unit).to(u.nm).value
    except Exception:
        if hasattr(u, "AA") and parsed_unit == u.AA:
            return 0.1
        return None


def _infer_scale_from_metadata(table, column: str) -> Optional[float]:
    """Attempt to infer the wavelength scale using table metadata."""

    if table is None or column not in getattr(table, "colnames", []):
        return None

    try:
        col = table[column]
    except Exception:
        return None

    info = getattr(col, "info", None)
    metadata_candidates = [
        getattr(col, "meta", None),
        getattr(col, "description", None),
        getattr(col, "format", None),
        getattr(col, "name", None),
        getattr(info, "meta", None) if info is not None else None,
        getattr(info, "description", None) if info is not None else None,
        getattr(info, "format", None) if info is not None else None,
        getattr(info, "name", None) if info is not None else None,
        column,
    ]

    table_meta = getattr(table, "meta", None)
    if isinstance(table_meta, dict):
        metadata_candidates.extend(
            [
                table_meta.get(column),
                table_meta.get(column.lower()),
                table_meta.get(column.upper()),
                table_meta.get("comments"),
                table_meta.get("Comments"),
                table_meta.get("COMMENT"),
            ]
        )
        units_map = table_meta.get("units")
        if isinstance(units_map, dict):
            metadata_candidates.extend(
                [
                    units_map.get(column),
                    units_map.get(column.lower()),
                    units_map.get(column.upper()),
                ]
            )

    for candidate in metadata_candidates:
        scale = _unit_to_nm_scale(candidate)
        if scale is not None:
            return scale
    return None


def _infer_scale_from_values(
    table, column: str, requested_range_nm: Optional[Tuple[float, float]]
) -> Optional[float]:
    """Fallback heuristic that inspects numeric values to determine scaling."""

    if table is None or column not in getattr(table, "colnames", []):
        return None

    values: List[float] = []
    for row in table:
        raw_value = None
        if hasattr(row, "get"):
            raw_value = row.get(column)
        if raw_value is None:
            try:
                raw_value = row[column]
            except Exception:
                raw_value = None
        extracted = _extract_float(raw_value)
        if extracted is not None and math.isfinite(extracted):
            values.append(extracted)

    if not values:
        return None

    values.sort()
    min_value = values[0]
    max_value = values[-1]
    if not math.isfinite(min_value) or not math.isfinite(max_value):
        return None

    if len(values) % 2 == 1:
        median_value = values[len(values) // 2]
    else:
        lower_mid = values[len(values) // 2 - 1]
        upper_mid = values[len(values) // 2]
        median_value = (lower_mid + upper_mid) / 2

    candidate_scales = [1.0, 0.1, 10.0, 1000.0]

    if requested_range_nm is not None:
        req_min, req_max = requested_range_nm
        if req_min > req_max:
            req_min, req_max = req_max, req_min
        span = req_max - req_min
        tolerance = max(1.0, span * 0.1 if span else max(abs(req_min), abs(req_max), 1.0) * 0.1)
        for scale in candidate_scales:
            scaled_min = min_value * scale
            scaled_max = max_value * scale
            if scaled_min > scaled_max:
                scaled_min, scaled_max = scaled_max, scaled_min
            if scaled_max < req_min - tolerance or scaled_min > req_max + tolerance:
                continue
            return scale

    if median_value > 1500:
        return 0.1
    if median_value < 0.1:
        return 1000.0
    if 50 <= median_value <= 1500:
        return 1.0
    if median_value < 50 and max_value <= 50:
        return 1000.0

    return None


def _column_scale_to_nm(
    table,
    column: str,
    requested_range_nm: Optional[Tuple[float, float]] = None,
) -> float:
    """Return a multiplicative factor that converts the column to nm."""

    default_scale = 0.1  # Historical default assumes Å when unit metadata is missing.
    if table is None or column not in getattr(table, "colnames", []):
        return default_scale

    col = table[column]

    for candidate in (
        getattr(col, "unit", None),
        getattr(getattr(col, "info", None), "unit", None),
    ):
        scale = _unit_to_nm_scale(candidate)
        if scale is not None:
            return scale

    metadata_scale = _infer_scale_from_metadata(table, column)
    if metadata_scale is not None:
        return metadata_scale

    inferred = _infer_scale_from_values(table, column, requested_range_nm)
    if inferred is not None:
        return inferred

    return default_scale


def _split_energy(value: Any) -> Tuple[Optional[float], Optional[float]]:
    text = str(value).strip()
    if not text or text in {"-", "--"}:
        return (None, None)
    matches = _FLOAT_PATTERN.findall(text.replace(",", ""))
    if not matches:
        return (None, None)
    lower = float(matches[0]) if matches else None
    upper = float(matches[1]) if len(matches) > 1 else None
    return (lower, upper)


def _clean_text(value: Any) -> Optional[str]:
    text = str(value).strip()
    if not text or text in {"-", "--"}:
        return None
    return re.sub(r"\s+", " ", text)


DEFAULT_LOWER_WAVELENGTH_NM = 380.0
DEFAULT_UPPER_WAVELENGTH_NM = 750.0


def fetch(
    *,
    element: str | None = None,
    linename: str | None = None,
    ion_stage: str | int | None = None,
    lower_wavelength: float | None = None,
    upper_wavelength: float | None = None,
    wavelength_unit: str = "nm",
    use_ritz: bool = True,
    wavelength_type: str = "vacuum",
) -> Dict[str, Any]:
    """Fetch spectral line data from the NIST ASD service.

    Parameters
    ----------
    element:
        Element symbol or name (e.g. ``"Fe"`` or ``"Iron"``). Ignored if
        ``linename`` is provided but still used for metadata resolution.
    linename:
        Explicit spectrum identifier (e.g. ``"Fe II"``). If omitted, the
        identifier will be constructed from ``element`` and ``ion_stage``.
    ion_stage:
        Ionisation stage expressed as an integer, Roman numeral, or count of
        ``+`` characters (``"++"`` becomes ``III``). Defaults to neutral.
    lower_wavelength / upper_wavelength:
        Wavelength bounds expressed in ``wavelength_unit`` units. Defaults to
        the optical range of 380-750 nm when not supplied.
    wavelength_unit:
        Unit label for the wavelength inputs. Supported values: ``"nm"``,
        ``"Angstrom"``/``"Å"``, ``"um"``/``"µm"``.
    use_ritz:
        Prefer the Ritz wavelength when available; otherwise fall back to the
        observed value.
    wavelength_type:
        Forwarded to the ASD query. ``"vacuum"`` (default) returns vacuum
        wavelengths, while ``"vac+air"`` toggles air/vacuum switching.
    """

    if not ASTROQUERY_AVAILABLE:
        raise NistUnavailableError(
            "astroquery.nist is required to fetch NIST spectra"  # pragma: no cover - defensive branch
        ) from _IMPORT_ERROR

    element_record, stage_value, stage_roman, spectrum, label = _resolve_spectrum(
        element=element,
        linename=linename,
        ion_stage=ion_stage,
    )

    unit_normalised = wavelength_unit.strip().lower() if wavelength_unit else "nm"
    if unit_normalised in {"ang", "angstrom", "ångström", "å", "aa"}:
        unit = u.AA
    elif unit_normalised in {"um", "µm", "micron", "micrometer", "micrometre"}:
        unit = u.um
    else:
        unit = u.nm

    lower = lower_wavelength if lower_wavelength is not None else DEFAULT_LOWER_WAVELENGTH_NM
    upper = upper_wavelength if upper_wavelength is not None else DEFAULT_UPPER_WAVELENGTH_NM
    if lower > upper:
        lower, upper = upper, lower

    min_wav = lower * unit
    max_wav = upper * unit

    try:
        table = Nist.query(
            min_wav,
            max_wav,
            linename=spectrum,
            wavelength_type=wavelength_type,
        )
    except Exception as exc:  # pragma: no cover - network failure path
        raise NistQueryError(f"Failed to query NIST ASD: {exc}") from exc

    lines: List[Dict[str, Any]] = []
    max_relative_intensity = 0.0

    try:
        requested_range_nm: Optional[Tuple[float, float]] = (
            float(min_wav.to(u.nm).value),
            float(max_wav.to(u.nm).value),
        )
    except Exception:
        requested_range_nm = None

    observed_scale = (
        _column_scale_to_nm(table, "Observed", requested_range_nm) if table is not None else 0.1
    )
    ritz_scale = (
        _column_scale_to_nm(table, "Ritz", requested_range_nm) if table is not None else 0.1
    )

    if table is not None:
        for row in table:
            observed_value = _extract_float(row.get("Observed"))
            ritz_value = _extract_float(row.get("Ritz"))

            observed_nm = (
                observed_value * observed_scale if observed_value is not None else None
            )
            ritz_nm = ritz_value * ritz_scale if ritz_value is not None else None

            if use_ritz and ritz_nm is not None:
                chosen_nm = ritz_nm
            elif observed_nm is not None:
                chosen_nm = observed_nm
            else:
                chosen_nm = ritz_nm
            if chosen_nm is None:
                continue

            relative_intensity = _extract_float(row.get("Rel."))
            if relative_intensity is not None:
                max_relative_intensity = max(max_relative_intensity, relative_intensity)

            aki = _extract_float(row.get("Aki"))
            fik = _extract_float(row.get("fik"))
            energy_lower, energy_upper = _split_energy(row.get("Ei           Ek"))

            line_record = {
                "wavelength_nm": chosen_nm,
                "observed_wavelength_nm": observed_nm,
                "ritz_wavelength_nm": ritz_nm,
                "relative_intensity": relative_intensity,
                "transition_probability_s": aki,
                "oscillator_strength": fik,
                "accuracy": _clean_text(row.get("Acc.")),
                "lower_level": _clean_text(row.get("Lower level")),
                "upper_level": _clean_text(row.get("Upper level")),
                "transition_type": _clean_text(row.get("Type")),
                "transition_probability_reference": _clean_text(row.get("TP")),
                "line_reference": _clean_text(row.get("Line")),
                "lower_level_energy_ev": energy_lower,
                "upper_level_energy_ev": energy_upper,
            }
            lines.append(line_record)

    if not lines:
        meta = {
            "source_type": "reference",
            "archive": "NIST ASD",
            "label": label,
            "element_symbol": element_record.symbol,
            "element_name": element_record.name,
            "atomic_number": element_record.number,
            "ion_stage": stage_roman,
            "ion_stage_number": stage_value,
            "query": {
                "linename": spectrum,
                "lower_wavelength": float(lower),
                "upper_wavelength": float(upper),
                "wavelength_unit": str(unit),
                "wavelength_type": wavelength_type,
                "use_ritz": use_ritz,
            },
            "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
            "citation": "NIST ASD Team, https://physics.nist.gov/asd",
            "note": "No spectral lines returned for requested range.",
        }
        return {
            "wavelength_nm": [],
            "intensity": [],
            "intensity_normalized": [],
            "lines": [],
            "meta": meta,
        }

    if max_relative_intensity <= 0:
        max_relative_intensity = None

    for line in lines:
        rel = line["relative_intensity"]
        if rel is None or max_relative_intensity is None:
            line["relative_intensity_normalized"] = None
        else:
            line["relative_intensity_normalized"] = rel / max_relative_intensity if max_relative_intensity else None

    meta = {
        "source_type": "reference",
        "archive": "NIST ASD",
        "label": label,
        "element_symbol": element_record.symbol,
        "element_name": element_record.name,
        "atomic_number": element_record.number,
        "ion_stage": stage_roman,
        "ion_stage_number": stage_value,
        "query": {
            "linename": spectrum,
            "lower_wavelength": float(lower),
            "upper_wavelength": float(upper),
            "wavelength_unit": str(unit),
            "wavelength_type": wavelength_type,
            "use_ritz": use_ritz,
        },
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "citation": "Kramida, A. et al. (NIST ASD), https://physics.nist.gov/asd",
    }

    return {
        "wavelength_nm": [line["wavelength_nm"] for line in lines],
        "intensity": [line.get("relative_intensity") for line in lines],
        "intensity_normalized": [line.get("relative_intensity_normalized") for line in lines],
        "lines": lines,
        "meta": meta,
    }
