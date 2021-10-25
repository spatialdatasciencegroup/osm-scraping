import re, os, sys
import overpass
import rasterio as rio
import geopandas as gpd
from shapely.geometry.base import deserialize_wkb

import lib.misc as m
import lib.osmtools as ost
import lib.imagetools as img
from lib.authkit import ee_client, get_drive

from time import perf_counter
from datetime import datetime as dt
from pytz import timezone 
tz = timezone("US/Central")

"""
pipe_script.py
--------------
CLI script for OSM Pipeline.
Change available sample areas in lib/misc.py.
"""

""" Hyperparameters """
#? Filepaths
# Drive Authentication File
GDRIVE_SETTINGS = './keys/pydrive/settings.yaml'
# Output folder for downloaded data
LOCAL_ROOT = './data/osm-sets'
# Google Drive output folder
DRIVE_FOLDER_NAME = 'geo-scrape-sets'

#? Flags 
# Use '-y' flag to skip confirmation prompts
SKIP_PROMPT = ('-y' in sys.argv)
# Use '-v' for verbose
VERBOSE = ('-v' in sys.argv)
""" --------------- """

# Verbosity printing
def printv(*args):
    if VERBOSE:
        print(*args)
    else:
        return
    

# Authenticate
trecord = [("Authentication", perf_counter())] # init time tracker
op = overpass.API()
gdrive = get_drive(settings_fp=GDRIVE_SETTINGS, verbose=VERBOSE)
ee_client()


# Creates output folder in drive if missing. 
trecord.append(("Drive Folder Creation", perf_counter()))
drive_folder = img.create_drive_folder(gdrive, DRIVE_FOLDER_NAME)

# Create output folder from user-selected city.
trecord.append(("User Prompt", perf_counter()))
dset_data = m.prompt_cities()

trecord.append(("Local Folder Prep", perf_counter()))
dset_name, dset_folder = m.make_set_folder(LOCAL_ROOT, dset_data['filename'])

dset_data.update({'filename': dset_name})
print("updated filename:", dset_data['filename'])


# Export from EE Cloud to personal drive
trecord.append(("EE to Drive", perf_counter()))
result = img.export_naip_image(gdrive=gdrive, 
                      drive_folder=drive_folder, 
                      dset_data=dset_data)

if result: 
    # Failed, check output here
    print(result.keys())
    sys.exit(0)

# Download to local
trecord.append(("Raster Download", perf_counter()))
raster_fp = img.download_raster(gdrive=gdrive, 
                                drive_folder=drive_folder,
                                set_name=dset_name, 
                                out_dir=dset_folder,
                                skip_conf=SKIP_PROMPT)

trecord.append(("OSM Query", perf_counter()))
response = op.get(
    "way" + ost.overpass_bounds(dset_data) + ";(._;>;);",
    verbosity="geom",
)
printv("> Parsing OSM Query...")
# Remove nodes before conversion, this is ~25x faster than removing from GDF
trecord.append(("Parse Query", perf_counter()))
way_features = [f for f in response.features if f.geometry['type'] == "LineString"]
gdf = gpd.GeoDataFrame.from_features(way_features)
gdf.set_crs(epsg=4326, inplace=True)
printv("> Parsed raw response as gdf.")

# Parse building perimiters (Linestrings)
trecord.append(("Parse Building GDF", perf_counter()))
build_gdf = gdf[gdf.building.notnull()].reset_index()
build_gdf = ost.parse_osm_gdf(gdf=build_gdf, main_key='building')
perimeter_fp = os.path.join(dset_folder, 'building_perimeters.shp')
build_gdf.to_file(perimeter_fp)
# Polygonize, save footprints
build_gdf['geometry'] = ost.gdf_polygonize(build_gdf)
footprint_fp = os.path.join(dset_folder, 'buildings.shp')
build_gdf.to_file(footprint_fp)
printv(">> Building footprints saved as labeled polygons.")

# Parse Roads
trecord.append(("Parse Road GDF", perf_counter()))
road_gdf = gdf[gdf.highway.notnull()].reset_index()
road_gdf = ost.parse_osm_gdf(gdf=road_gdf, main_key='highway')
raw_road_fp = os.path.join(dset_folder, 'roads.shp')
road_gdf.to_file(raw_road_fp)
printv(">> Roads saved as labeled linestrings.")

# Parse ungrouped
trecord.append(("Parse Ungrouped GDF", perf_counter()))
other_gdf = gdf[gdf.highway.isnull() & gdf.building.isnull()]
other_gdf = ost.drop_empty_cols(other_gdf)
other_gdf.reset_index(inplace=True)
other_fp = os.path.join(dset_folder, 'ungrouped.shp')
other_gdf.to_file(other_fp)
printv(">> Ungrouped shapes saved as uncleaned labeled linestrings.\n")

# Print results and save in md
md_data = []
md_data.append(f"# {dset_data['filename']} Dataset Info\n")
md_data.append(dt.now(tz=tz).strftime("### %a, %D - [%I:%M %p]\n"))
md_data.append('\n---\n')
md_data.append("\n")

# Add Raster Info
md_data.append("## Exported Raster\n")
with rio.open(raster_fp) as raster:
    md_data.append(f"- City:  {re.compile('[^a-zA-Z]').sub('', dset_data['filename'])}\n")  
    md_data.append(f"- Type:  {raster.dtypes}\n")  
    md_data.append(f"- Shape: ({raster.count}, {raster.height}, {raster.width})\n")
    md_data.append(f"- Path:  '{raster_fp}'\n")
    md_data.append(f"- Size:  {m.file_size(filepath=raster_fp)}\n") 
md_data.append("\n")

md_data.append("## Parsed OSM GeoDataFrames\n")
gdf_data = [("Raw", gdf), ("Buildings", build_gdf), ("Roads", road_gdf), ("Ungrouped", other_gdf)]
for (name, frame) in gdf_data:
    md_data.append(f"### {name} frame:\n")
    md_data.append(f" - Rows: {frame.rows}\n")
    md_data.append(f" - Cols: {frame.cols}\n")
    md_data.append(f" - CRS:  {frame.crs}\n")
    md_data.append(f" - Geom Type: {type(frame.geometry[0]).__name__}\n")
    if name != 'Raw':
        fp = f"{dset_folder}/{name.lower()}.shp"
        md_data.append(f" - Path: '{fp}'\n")
        md_data.append(f" - Size: {m.file_size(filepath=fp)}\n")  
    md_data.append("\n")
md_data.append("\n")

md_data.append("## Time Data\n")
for idx, (title, tstamp) in enumerate(trecord):
    next_stamp = perf_counter()
    if ((idx+1) < len(trecord)):
        next_stamp = trecord[(idx+1)][1]
    elapsed = m.fmt_time((tstamp - next_stamp))
    md_data.append(f"- {title}: {elapsed}\n")
    

printv("> Writing to Markdown")
markdown_fp = os.path.join(dset_folder, dset_data['filename']+"_info.md")
with open(markdown_fp, 'w+') as md:
    md.writelines(md_data)    


fin_time = dt.now(tz=tz).strftime("%D - [%I:%M %p]")
if SKIP_PROMPT:
    print(f"Completed EE dataset export. {fin_time}\nResults here: '{markdown_fp}'")
else:
    show_results = input("Print results? (y/N) ")
    if 'y' in show_results.lower():
        for mdline in md_data:
            print(mdline.replace('\n', ''))
    print("\n\nCompleted EE dataset export.", fin_time)