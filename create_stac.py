"""Create a STAC catalog from downloaded PRISM TIFs.

One STAC Item per date directory, with one asset per variable (ppt, tmean, …).
Uses the proj and raster extensions via rio-stac.
"""

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

import pystac
import rasterio
import rio_stac

# Pattern: prism_<variable>_us_30s_<date>.tif
TIF_RE = re.compile(r"prism_(\w+)_us_30s_(\d{8})\.tif")


def _tif_metadata(tif_path: Path) -> dict:
    """Read GDAL metadata tags from a TIF."""
    with rasterio.open(tif_path) as src:
        return src.tags()


def create_item(date_dir: Path, collection_id: str) -> pystac.Item:
    """Build a single STAC Item from all TIFs in a date directory."""
    tifs = sorted(date_dir.glob("prism_*_us_30s_*.tif"))
    if not tifs:
        raise FileNotFoundError(f"No TIFs found in {date_dir}")

    # Parse date from directory name
    date_str = date_dir.name  # e.g. "20251216"
    dt = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=timezone.utc)

    # Use the first TIF to seed the item geometry / bbox via rio-stac,
    # then attach remaining TIFs as additional assets.
    first_tif = tifs[0]
    first_match = TIF_RE.match(first_tif.name)
    first_var = first_match.group(1) if first_match else "data"

    # Collect common metadata tags from the first TIF
    tags = _tif_metadata(first_tif)
    properties = {f"prism:{k.lower()}": v for k, v in tags.items()}

    item = rio_stac.create_stac_item(
        source=str(first_tif),
        input_datetime=dt,
        id=f"prism_us_30s_{date_str}",
        collection=collection_id,
        properties=properties,
        asset_name=first_var,
        asset_roles=["data"],
        asset_media_type=pystac.MediaType.GEOTIFF,
        with_proj=True,
        with_raster=True,
        geom_precision=6,
    )

    # Add remaining TIFs as assets
    for tif in tifs[1:]:
        match = TIF_RE.match(tif.name)
        var = match.group(1) if match else tif.stem
        asset = pystac.Asset(
            href=str(tif),
            media_type=pystac.MediaType.GEOTIFF,
            roles=["data"],
        )
        item.assets[var] = asset

        # Merge any unique tags from this TIF into properties
        extra_tags = _tif_metadata(tif)
        for k, v in extra_tags.items():
            prop_key = f"prism:{k.lower()}"
            if prop_key not in item.properties:
                item.properties[prop_key] = v

    return item


def main():
    parser = argparse.ArgumentParser(description="Create STAC catalog from PRISM TIFs.")
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Root directory containing date sub-directories with TIFs (default: data)",
    )
    parser.add_argument(
        "--stac-dir",
        default="stac",
        help="Output directory for the STAC catalog (default: stac)",
    )
    args = parser.parse_args()

    data_root = Path(args.data_dir)
    stac_root = Path(args.stac_dir)
    stac_root.mkdir(parents=True, exist_ok=True)

    collection_id = "prism-daily-800m"

    # Discover date directories (only dirs whose name is 8 digits)
    date_dirs = sorted(
        d for d in data_root.iterdir() if d.is_dir() and re.fullmatch(r"\d{8}", d.name)
    )
    if not date_dirs:
        print(f"No date directories found in {data_root}")
        return

    # Build items
    items = []
    for date_dir in date_dirs:
        print(f"Processing {date_dir.name} ...")
        item = create_item(date_dir, collection_id)
        items.append(item)

    # Compute collection extent from items
    bboxes = [item.bbox for item in items]
    datetimes = [item.datetime for item in items]
    spatial_extent = pystac.SpatialExtent(
        bboxes=[[
            min(b[0] for b in bboxes),
            min(b[1] for b in bboxes),
            max(b[2] for b in bboxes),
            max(b[3] for b in bboxes),
        ]]
    )
    temporal_extent = pystac.TemporalExtent(intervals=[[min(datetimes), max(datetimes)]])

    collection = pystac.Collection(
        id=collection_id,
        description="PRISM daily 800m meteorological data for CONUS",
        extent=pystac.Extent(spatial=spatial_extent, temporal=temporal_extent),
    )
    for item in items:
        collection.add_item(item)

    # Create root catalog
    catalog = pystac.Catalog(
        id="prism-stac",
        description="STAC catalog for PRISM meteorological data",
    )
    catalog.add_child(collection)

    # Make asset hrefs relative and save
    catalog.normalize_hrefs(str(stac_root))
    catalog.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)

    print(f"\nCatalog written to {stac_root}/")
    print(f"  Items: {len(items)}")
    print(f"  Catalog: {stac_root / 'catalog.json'}")


if __name__ == "__main__":
    main()
