#!/usr/bin/env python3
import os, json, time, argparse, yaml, re
import numbers
from pathlib import Path
import pandas as pd
from astropy.table import Table, vstack
from astroquery.simbad import Simbad
from astroquery.mast import Observations
from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive
from astropy.coordinates import SkyCoord
import astropy.units as u

# Optional VO for CARMENES DR1
try:
    import pyvo
    from pyvo.dal.exceptions import DALQueryError as SimbadDALQueryError
    HAS_PYVO = True
except ImportError:
    pyvo = None
    SimbadDALQueryError = None
    HAS_PYVO = False


BASE_SIMBAD_FIELDS = ["otypes", "flux(V)", "flux(B)", "pmra", "pmdec"]
SIMBAD_RENAMED_FIELDS = {
    "sp_type": ("sp_type", "sptype"),
    "rvz_radvel": ("rvz_radvel", "rv_value"),
    "plx_value": ("plx_value", "plx"),
    "rvz_redshift": ("rvz_redshift", "z_value"),
}

SIMBAD_ACTIVE_FIELDS = {}


def _reset_simbad_instance():
    global SIMBAD

    simbad = Simbad()
    simbad.TIMEOUT = 60

    for field in BASE_SIMBAD_FIELDS:
        try:
            simbad.add_votable_fields(field)
        except Exception:
            continue

    for key, options in SIMBAD_RENAMED_FIELDS.items():
        preferred = SIMBAD_ACTIVE_FIELDS.get(key)
        ordered = options
        if preferred in options:
            idx = options.index(preferred)
            ordered = options[idx:]

        selected = None
        for col in ordered:
            try:
                simbad.add_votable_fields(col)
            except Exception:
                continue
            selected = col
            break

        if selected is None:
            for col in options:
                try:
                    simbad.add_votable_fields(col)
                except Exception:
                    continue
                selected = col
                break

        if selected is not None:
            SIMBAD_ACTIVE_FIELDS[key] = selected

    SIMBAD = simbad


_reset_simbad_instance()

MAST_INSTR_HINTS = set(["STIS","COS","IUE","NIRSpec","NIRISS","NIRCam","MIRI","WFC3"])
MAST_COLLECTIONS = set(["HST","JWST","IUE","HLSP"])  # HLSP includes CALSPEC, MUSCLES, ASTRAL
ESO_INSTR_HINTS = set(["UVES","HARPS","ESPRESSO","XSHOOTER","HARPS-N"])  # subset via ESO; HN via TNG not ESO, kept for tag

def _decode_if_bytes(val):
    if isinstance(val, bytes):
        return val.decode()
    return val


def _get_first_value(table, *names):
    for name in names:
        key = name.upper()
        if key in table.colnames:
            value = table[key][0]
            if value is not None:
                return value
    return None


def _get_first_value_with_column(table, *names):
    if table is None:
        return None, None

    col_lookup = {col.lower(): col for col in table.colnames}
    for name in names:
        lookup = name.lower()
        column = col_lookup.get(lookup)
        if column is None:
            continue
        value = table[column][0]
        if value is None:
            continue
        if getattr(value, "mask", False):
            continue
        return value, column
    return None, None


RA_COLUMN_ALIASES = ("RA", "ra", "RA_ICRS", "RAJ2000", "RA_d")
DEC_COLUMN_ALIASES = ("DEC", "dec", "DEC_ICRS", "DEJ2000", "DEC_d")


def _coerce_degree_value(value, column_name):
    if value is None:
        return None, False

    value = _decode_if_bytes(value)
    column_key = column_name.upper() if column_name else ""
    column_suggests_deg = column_key.endswith("_D") or column_key.endswith("_DEG") or column_key.endswith("_DEGREES")

    if hasattr(value, "to"):
        try:
            return value.to_value(u.deg), True
        except Exception:
            pass

    if isinstance(value, numbers.Number):
        return float(value), True

    if column_suggests_deg:
        try:
            return float(value), True
        except (TypeError, ValueError):
            stripped = value.strip() if isinstance(value, str) else value
            try:
                return float(stripped), True
            except (TypeError, ValueError):
                return value, False

    return value, False


def _resolve_coordinates(table):
    ra_value, ra_column = _get_first_value_with_column(table, *RA_COLUMN_ALIASES)
    dec_value, dec_column = _get_first_value_with_column(table, *DEC_COLUMN_ALIASES)

    if ra_value is None or dec_value is None:
        return None, None, None

    ra_value, ra_is_degree = _coerce_degree_value(ra_value, ra_column)
    dec_value, dec_is_degree = _coerce_degree_value(dec_value, dec_column)

    if isinstance(ra_value, str):
        ra_value = ra_value.strip()
    if isinstance(dec_value, str):
        dec_value = dec_value.strip()

    unit = (u.deg, u.deg) if ra_is_degree and dec_is_degree else (u.hourangle, u.deg)
    return ra_value, dec_value, unit


def _attempt_simbad_fallback(exc):
    if SimbadDALQueryError is None or not isinstance(exc, SimbadDALQueryError):
        return False
    message = str(exc).lower()
    updated = False
    for key, options in SIMBAD_RENAMED_FIELDS.items():
        active = SIMBAD_ACTIVE_FIELDS.get(key)
        if not active or active == options[-1]:
            continue
        if active.lower() not in message:
            continue
        idx = options.index(active)
        for candidate in options[idx + 1 :]:
            SIMBAD_ACTIVE_FIELDS[key] = candidate
            updated = True
            break
    if updated:
        _reset_simbad_instance()
    return updated


def resolve_target(name):
    while True:
        try:
            r = SIMBAD.query_object(name)
        except Exception as exc:
            if not _attempt_simbad_fallback(exc):
                raise
            continue
        break

    if r is None or len(r) == 0:
        return None
    ra, dec, unit = _resolve_coordinates(r)
    if ra is None or dec is None:
        return None
    c = SkyCoord(ra, dec, unit=unit)

    canonical = _decode_if_bytes(r["MAIN_ID"][0])
    otype = _decode_if_bytes(_get_first_value(r, "otypes"))
    sptype = _decode_if_bytes(_get_first_value(r, "sp_type", "sptype"))
    parallax = _get_first_value(r, "plx_value", "plx")
    radial_velocity = _get_first_value(r, "rvz_radvel", "rvz_value", "rv_value")

    out = {
        "canonical_name": canonical,
        "ra_deg": float(c.ra.deg),
        "dec_deg": float(c.dec.deg),
        "otype": otype,
        "sptype": sptype,
        "parallax_mas": float(parallax) if parallax is not None else None,
        "rv_kms": float(radial_velocity) if radial_velocity is not None else None,
    }
    return out

def mast_observations(name, instr_hints):
    try:
        tbl = Observations.query_object(name)
    except Exception:
        tbl = Table()
    if tbl is None or len(tbl) == 0:
        return Table()
    # keep relevant missions/instruments
    keep = []
    for row in tbl:
        coll = row.get("obs_collection", None)
        inst = row.get("instrument_name", None)
        if coll in MAST_COLLECTIONS and (not instr_hints or (inst and any(h in inst for h in instr_hints))):
            keep.append(row)
    return Table(rows=keep, names=tbl.colnames) if keep else Table()

def mast_products(obs_table):
    all_prod = []
    for obsid in obs_table["obsid"]:
        prods = Observations.get_product_list(obsid)
        # spectra only
        pkeep = prods[(prods["dataproduct_type"] == "spectrum") |
                      (prods["productType"] == "SCIENCE")]
        if len(pkeep):
            # strip previews/calibration junk
            pkeep = pkeep[~pkeep["productFilename"].astype(str).str.contains("_preview|_thumb|jpg|png", regex=True)]
            all_prod.append(pkeep)
    if not all_prod:
        return Table()
    return vstack(all_prod, metadata_conflicts="silent")

def eso_phase3_query(name, ra_deg, dec_deg, radius_arcsec=5):
    # We avoid login-only raw. Phase 3 reduced products only.
    try:
        from astroquery.eso import Eso
        eso = Eso()
        eso.ROW_LIMIT = 10000
        # search Phase 3 around coordinates
        # Note: API uses strings for RA/DEC or SkyCoord
        r = eso.query_surveys("phase3_main", coord=SkyCoord(ra_deg*u.deg, dec_deg*u.deg),
                              radius=f"{radius_arcsec}s")
        if r is None or len(r) == 0:
            return Table()
        # spectra only
        r = r[r["DP.TYPE"] == "SPECTRUM"]
        return r
    except Exception:
        return Table()

def carmenes_dr1(coord):
    if not HAS_PYVO:
        return None
    # CARMENES DR1 via VO service (if reachable)
    try:
        svc = pyvo.dal.SCSService("https://dc.g-vo.org/carmenes/q/scs/scs.xml")
        res = svc.search(pos=coord, radius=5/3600)  # 5 arcsec
        return res.to_table()
    except Exception:
        return None

def exoplanets_for_host(hostname):
    try:
        tab = NasaExoplanetArchive.query_aliastable(hostname)
        host = None
        if tab is None or len(tab) == 0:
            # direct planet table join on default_name
            host = hostname
        else:
            # pick the default identifier for cross-match
            host = tab[tab['default_name'] == 1]['hostname'][0] if 'default_name' in tab.colnames else hostname
        pl = NasaExoplanetArchive.query_planetary_systems(hostname=host)
        return pl.to_pandas() if pl is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def summarize_star(meta, planets_df, tags):
    parts = []
    st = meta.get("sptype") or "unknown type"
    parts.append(f"{meta['canonical_name']}: {st}")
    if meta.get("parallax_mas"):
        try:
            dist_pc = 1000.0 / meta["parallax_mas"]
            parts.append(f"~{dist_pc:.1f} pc")
        except Exception:
            pass
    if planets_df is not None and len(planets_df):
        n = planets_df["pl_name"].nunique()
        meth = ", ".join(sorted({m for m in planets_df["discoverymethod"].dropna().unique()})) or "various methods"
        parts.append(f"{n} planet(s) known ({meth})")
    if tags:
        parts.append(f"tags: {', '.join(tags)}")
    return " | ".join(parts)

def write_manifest(outdir, name, star_meta, mast_meta, mast_products_tbl, eso_tbl, carm_tbl, planets_df, tags):
    outdir = Path(outdir) / name.replace(" ", "_")
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": name,
        "canonical_name": star_meta.get("canonical_name"),
        "coordinates": {"ra_deg": star_meta.get("ra_deg"), "dec_deg": star_meta.get("dec_deg")},
        "star": {
            "otype": star_meta.get("otype"),
            "sptype": star_meta.get("sptype"),
            "parallax_mas": star_meta.get("parallax_mas"),
            "rv_kms": star_meta.get("rv_kms"),
        },
        "planets": planets_df.to_dict(orient="records") if planets_df is not None else [],
        "summaries": {"auto": summarize_star(star_meta, planets_df, tags)},
        "provenance": {"generated_by": "build_registry.py", "date": pd.Timestamp.utcnow().isoformat()},
        "datasets": {"mast": [], "eso_phase3": [], "carmenes_dr1": []}
    }
    # MAST observations and products
    if mast_meta is not None and len(mast_meta):
        manifold = mast_meta.to_pandas()[["obsid","obs_collection","instrument_name","target_name","filters","t_min","t_max"]].fillna("").to_dict(orient="records")
        manifest["datasets"]["mast"] = manifold
    if mast_products_tbl is not None and len(mast_products_tbl):
        prods = mast_products_tbl.to_pandas()[["obsid","productFilename","productType","dataproduct_type","productURL","description"]]
        manifest["datasets"]["mast_products"] = prods.to_dict(orient="records")
    # ESO Phase 3
    if eso_tbl is not None and len(eso_tbl):
        cols = [c for c in ["DP.ID","INSTRUME","TARGET","DP.DATATYPE","DP.TYPE","MJD-OBS","DP.DID"] if c in eso_tbl.colnames]
        manifest["datasets"]["eso_phase3"] = eso_tbl[cols].to_pandas().to_dict(orient="records")
    # CARMENES
    if carm_tbl is not None and len(carm_tbl):
        manifest["datasets"]["carmenes_dr1"] = Table(carm_tbl).to_pandas().to_dict(orient="records")

    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roster", required=True)
    ap.add_argument("--out", default="data_registry")
    ap.add_argument("--download", action="store_true", help="Also download spectra files where possible")
    ap.add_argument("--sleep", type=float, default=0.6, help="Delay between queries to avoid rate limits")
    args = ap.parse_args()

    roster = yaml.safe_load(Path(args.roster).read_text())
    rows = []
    Path(args.out).mkdir(parents=True, exist_ok=True)

    for t in roster["targets"]:
        name = t["name"]
        tags = t.get("tags", [])
        hints = set(t.get("instrument_hints", []))
        print(f"[build] {name}")
        meta = resolve_target(name)
        if not meta:
            print(f"  ! SIMBAD failed for {name}")
            continue

        # planets
        planets_df = exoplanets_for_host(meta["canonical_name"])
        # MAST obs/products
        mast_obs = mast_observations(meta["canonical_name"], hints & MAST_INSTR_HINTS)
        mast_prod = mast_products(mast_obs) if len(mast_obs) else Table()
        # ESO Phase 3 (reduced spectra around coords)
        eso_tbl = eso_phase3_query(meta["canonical_name"], meta["ra_deg"], meta["dec_deg"])
        # CARMENES DR1 (optional)
        coord = SkyCoord(meta["ra_deg"]*u.deg, meta["dec_deg"]*u.deg)
        carm_tbl = carmenes_dr1(coord) if HAS_PYVO else None

        manifest = write_manifest(args.out, name, meta, mast_obs, mast_prod, eso_tbl, carm_tbl, planets_df, tags)

        rows.append({
            "name": name,
            "canonical_name": meta["canonical_name"],
            "ra_deg": meta["ra_deg"], "dec_deg": meta["dec_deg"],
            "sptype": meta.get("sptype"),
            "n_planets": int(planets_df["pl_name"].nunique()) if len(planets_df) else 0,
            "has_mast": bool(len(mast_obs)),
            "has_eso": bool(len(eso_tbl)),
            "has_carmenes": bool(carm_tbl is not None and len(carm_tbl)),
            "summary": manifest["summaries"]["auto"]
        })

        time.sleep(args.sleep)

    catalog = pd.DataFrame(rows)
    catalog.to_csv(Path(args.out) / "catalog.csv", index=False)
    print(f"[done] wrote {len(rows)} targets to {args.out}/catalog.csv")

if __name__ == "__main__":
    main()
