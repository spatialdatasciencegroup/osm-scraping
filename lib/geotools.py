import ee
import rasterio as rio 
import geopandas as gpd
import shapely.geometry as shp

def raster_world_bounds(raster) -> dict:
    """ 
    Converts rio raster bounds to lat/long bounds tuple.

    Notes:
        Can run in batches if necessary. 
        
        Radiant sets do not keep crs and bounds for each tile, 
        making this useless for Radiant Sets
        
        for CRS conversion to Lat/Lon, this method works better than:
        - Creating Proj Objects
        - Creating Transformer object from ESPG codes
        - Converting cords seperately

    Args:
        raster (rio.DatasetReader): Raster to draw bounds from.
    Returns:
        dict: Lat/Lon Bounds of raster image
            'south' (float): Minimum Lat coord
            'west' (float): Minimum Long coord
            'north' (float): Maximum Lat coord
            'east' (float): Maximum Long coord
    """
    bounding_poly = shp.box(*(raster.bounds))
    gdf = gpd.GeoDataFrame(geometry=[bounding_poly], crs=raster.crs)
    gdf = gdf.to_crs('EPSG:4326')
    (min_x, min_y, max_x, max_y) = gdf.geometry[0].bounds
    return {'west': min_x, 'south': min_y, 'east': max_x, 'north': max_y}


def to_region(bounds) -> list:
    """ 
    Converts a bounding geometry or 
    dict into an EE-parsable list of bounding coords. 
    
    Args: 
        bounds (dict/geom/list): Bounding object to convert, if a list
                                 is passed, the shape is checked and returned. 
    Returns:    
        List of coordinate tuples representing region for query.
    """ 
    if isinstance(bounds, list):
        coords = bounds
        if (len(coords) != 5) or (len(coords[0]) != 2):
            raise RuntimeError(f"Invalid coordinate shape from passed list:\nExpected: (5, 2)\tRecieved: ({len(coords)}, {len(coords)[0]})") 
    if isinstance(bounds, ee.geometry.Geometry):
        coords = bounds.coordinates().getInfo()[0]
        if (len(coords) != 5) or (len(coords[0]) != 2):
            raise RuntimeError(f"Invalid coordinate shape extracted from passed geometry:\nExpected: (5, 2)\tRecieved: ({len(coords)}, {len(coords)[0]})") 
    elif isinstance(bounds, dict):
        dir_keys = ['south', 'north', 'west', 'east'] 
        for dk in dir_keys:
            if dk not in bounds.keys():
                raise KeyError(f"Bounds argument missing expected key '{dk}': {bounds.keys()}. Must have all of: {dir_keys}")
            elif not isinstance(bounds[dk], float):
                raise TypeError(f"Expected (float) type for bounding dict key '{dk}', recieved ({type(bounds[dk])}): {bounds[dk]}.") 
        coords = [
            [bounds['west'],bounds['south']], 
            [bounds['west'],bounds['north']], 
            [bounds['east'],bounds['north']], 
            [bounds['east'],bounds['south']]
        ]
    
    return coords