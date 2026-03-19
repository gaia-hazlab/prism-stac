# prism-stac
STAC catalog for subset of [PRISM meterological data](https://prism.oregonstate.edu)

*Just for 800m, CONUS, 2025/12/01 -> present, ppt and tmean for now*

URL params:
```
region = "us, ak, hi, pr (Corresponding to: CONUS, Alaska, Hawaii, Puerto Rico)"
data = "an, lt" (Corresponding to: All Networks, Long-term)
resolution = "800m, 4km"
variable = "ppt, tmin, tmax, tmean, tdmean, vpdmin, vpdmax"
temporal = "daily, monthly"
year = "2025"
filename = "prism_[variable]_[region]_[resolution]_[temporal]_[year].zip"
```

All Data Variables:
```
ppt (precipitation)
tmin (minimum temperature)
tmax (maximum temperature)
tmean (mean temperature)
tdmean (mean dewpoint)
vpdmin (minimum vapor pressure deficit)
vpdmax (maximum vapor pressure deficit)
```

## Catalog structure

Data is stored as COGs,,, but they are zipped! So we'll unzip them and put into a bucket for direct range requests.

```bash
export GDAL_DISABLE_READDIR_ON_OPEN=EMPTY_DIR
#export CPL_DEBUG=ON

gdal raster info /vsizip/vsicurl/https://data.prism.oregonstate.edu/time_series/us/an/800m/ppt/daily/2025/prism_ppt_us_30s_20251201.zip/prism_ppt_us_30s_20251201.tif

# NOTE: 4km data -> 25m filename, 800m data -> 30s filename
gdal raster info /vsizip/vsicurl/https://data.prism.oregonstate.edu/time_series/us/an/4km/ppt/daily/2025/prism_ppt_us_25m_20251201.zip/prism_ppt_us_25m_20251201.tif
```

```bash
prism-stac/catalog.json
prism-stac/20251201/
    prism_ppt_us_30s_20250101.tif
    prism_tmean_us_30s_20250101.tif
    prism_us_30s_20250101_stac.json
```

## Catalog creation

Server limits are strict (can request 1 file, once per day!), so we'll download each zip to local directory and work from that (`wget https://data.prism.oregonstate.edu/time_series/us/an/800m/ppt/daily/2025/prism_ppt_us_30s_20251201.zip`)

We'll use `rio-stac` to generate the STAC metadata for each COG, and then we'll add some custom properties to the STAC items to capture the URL of the original zip file and the filename of the original zip file.
