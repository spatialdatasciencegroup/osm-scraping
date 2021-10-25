import overpass 
import pandas as pd
import geopandas as gpd
import shapely.geometry as shp
from geojson.feature import FeatureCollection

op = overpass.API()

""" 
osmtools.py
-----------
OpenStreetMap API toolkit for querying geometries and parsing responses. 

May want to pass the API object later.
"""

def overpass_bounds(b):
    """ Converts bounding data to string formatted for overpass QL. """
    
    OVERPASS_FORMAT = ['south', 'west', 'north', 'east']

    if isinstance(b, list):
        if (len(b) == 4):
            bounds_list = b
        else: 
            raise TypeError(f"Passed bounding list has invalid length: {len(b)}. Expected length: 4. Expected format: {OVERPASS_FORMAT}")
    elif isinstance(b, dict):
        bounds_list = []
        for key in OVERPASS_FORMAT:
            bounds_list.append(b[key])
    else:
        raise NotImplementedError("Overpass bounding conversion requires list or dict.")    

    bounds_str = str(bounds_list)
    bounds_str = bounds_str.replace("[", "(")
    bounds_str = bounds_str.replace("]", ")")
    return bounds_str

    

def geojson_to_gdf(response: FeatureCollection):
    """ Convert a GeoJSON response object to clean GeoDataFrame. """
    way_features = [f for f in response.features if f.geometry['type'] == "LineString"]
    gdf = gpd.GeoDataFrame.from_features(way_features)
    gdf.reset_index(inplace=True)
    return gdf

def drop_empty_cols(gdf):
    empty_keys = [k for k in gdf.columns if gdf[k].notnull().sum() == 0]
    return gdf.drop(empty_keys, axis=1) 

    
def get_categories(gdf, main_key: str) -> pd.Series:
    """ 
    Gets the second-level labels as 
    a pandas series from OSM GDF.
    
    Args:
        gdf (GeoDataFrame): GeoDataFrame with labels to parse.
        main_key (str):     Key holding top-level labels.
    Returns:
        pd.Series: Series containing second-level labels as assigned by main column.
    """
    categories = []
    for _, row in gdf.iterrows():
        filled = row.notnull()
        label = row[main_key]
        if (label in gdf.columns) and filled.get(label):
            categories.append(row[label])
        else:
            categories.append(None)
    
    return pd.Series(categories)

    
def get_osm_gdf(bounds):
        
    # Query returns building footprints and roads
    response = op.get(
        "way" + overpass_bounds(bounds) + ";(._;>;);",
        verbosity="geom",
    )
    
    # Remove nodes before conversion, this is ~25x faster than removing from GDF
    way_features = [f for f in response.features if f.geometry['type'] == "LineString"]
    gdf = gpd.GeoDataFrame.from_features(way_features)
    gdf = gdf.drop([k for k in gdf.columns if 'tiger' in k], axis=1)
    
    buildings = gdf[gdf.building.notnull()]
    building_second_labels = drop_empty_cols(buildings)
    
    roads = gdf[gdf.highway.notnull()]
    roads = drop_empty_cols(roads)
    
    other = gdf[gdf.highway.isnull() & gdf.building.isnull()]
    other = drop_empty_cols(other)
    
    roads.drop([key for key in roads.columns if key not in ['highway', 'service', 'geometry', 'index']])
    buildings.drop([key for key in buildings.columns if key not in ['building', 'geometry', 'index']])
    
    return gdf

def parse_osm_gdf(gdf, main_key: str):
    """ 
    Parses OSM GDF keeping first and second-order labels only.     
    Acceptable parsing technique for all except name.
    Sets CRS, could make this a hyperparameter.

    Args:
        gdf (GeoDataFrame): GeoDataFrame for parsing from a Overpass query.
        main_key (str):     Column key to use as source of top-level labels.
        
    Returns:
        GeoDataFrame: GeoDataFrame with Geometry.
    """
        
    # Extract second-order categories
    categories = []
    for _, row in gdf.iterrows():
        filled = row.notnull()
        label = row[main_key]
        if (label in gdf.columns) and filled.get(label):
            categories.append(row[label])
        else:
            categories.append(None)
    categories = pd.Series(categories)
    
    if (categories.notnull().sum() == 0):
        # Series has no values
        print(f"'category' column skipped, top-level labels '{main_key}' have no sub-categories.")
    else:
        gdf.insert(loc=2, 
                   column='category', 
                   value=categories) 
    gdf = gdf.rename(columns={main_key: 'label'})

    
    KEY_WHITELIST = ['index', 'geometry', 'name', 'category', 'label']
    return gdf.drop([k for k in gdf.columns if k not in KEY_WHITELIST], axis=1)

                
def gdf_polygonize(line_gdf):
    polys = []
    for idx, row in line_gdf.iterrows():
        poly = shp.Polygon(row.geometry.coords)
        polys.append(poly)
        row.geometry = poly
    return pd.Series(polys)


