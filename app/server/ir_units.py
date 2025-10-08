from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class IRMeta:
    yunits: str
    yfactor: float = 1.0
    path_m: float | None = None
    mole_fraction: float | None = None


def to_A10(y_raw: np.ndarray, meta: IRMeta):
    y = np.asarray(y_raw, dtype=float) * (meta.yfactor or 1.0)
    u = (meta.yunits or "").lower()
    u = u.replace("μ", "µ")
    u = u.replace("^-1", "-1")
    prov = {"yfactor": meta.yfactor, "yunits_in": meta.yunits}

    def need_pl():
        return meta.path_m is None or meta.mole_fraction is None

    if "transmittance" in u or "%t" in u:
        T = y / 100.0 if "%" in u or "%t" in u else y
        A10 = -np.log10(np.clip(T, 1e-12, 1.0))
        prov |= {"from": "T", "percent": "%" in u or "%t" in u}
        return A10, prov

    if "absorbance" in u and ("base e" in u or "napier" in u):
        prov |= {"from": "Ae", "factor": "1/2.303"}
        return y / 2.303, prov

    if "absorbance" in u:
        prov |= {"from": "A10"}
        return y, prov

    if "m-1" in u and "base 10" in u:
        if need_pl():
            raise ValueError("Need path length (m) and mole fraction to convert α10 → A10.")
        A10 = y * meta.mole_fraction * meta.path_m
        prov |= {
            "from": "alpha10",
            "path_m": meta.path_m,
            "mole_fraction": meta.mole_fraction,
        }
        return A10, prov

    if "m-1" in u and ("base e" in u or "napier" in u):
        if need_pl():
            raise ValueError("Need path length (m) and mole fraction to convert αe → A10.")
        A10 = (y * meta.mole_fraction * meta.path_m) / 2.303
        prov |= {
            "from": "alpha_e",
            "path_m": meta.path_m,
            "mole_fraction": meta.mole_fraction,
            "factor": "1/2.303",
        }
        return A10, prov

    raise ValueError(f"Unsupported YUNITS: {meta.yunits}")


__all__ = ["IRMeta", "to_A10"]
