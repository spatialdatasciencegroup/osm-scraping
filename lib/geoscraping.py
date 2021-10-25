import geopandas as gpd
import overpass
import overpy
import pandas as pd
import shapely.geometry as geometry
from shapely.ops import linemerge, polygonize, polygonize_full, unary_union



# Get the API key (this uses default key)
api = overpass.API()
over = overpy.Overpass()



# method of converting ways from Overpass query to polygons
def linetopoly(lines):
    """
    Parameters:
    lines (list of Overpy Way objects): the ways associated with query results, stored in Overpy Way objects

    Returns:
    polygons (list of Shapely Polygons): the polygons of building footprints from query
    tags (list of strings): the associated tags of the buildings
    """
    lss = []
    tags = []
    # iterate through ways in query
    for ii_w, way in enumerate(lines):
        ls_coords = []
        tags.append(way.tags)

        # go through each node of the way
        for node in way.nodes:
            ls_coords.append((node.lon, node.lat))  # create a list of node coordinates

        lss.append(geometry.LineString(ls_coords))  # create a LineString from coords

    merged = linemerge([*lss])  # merge LineStrings
    borders = unary_union(merged)  # linestrings to a MultiLineString
    polygons = list(polygonize(borders))  # polygon from MultiLineString
    return polygons, tags

def querytoframe(query):
    """
    Parameters:
    query (Overpy Result object): the results of a query, stored in the Result structure of Overpy

    Returns:
    final (GeoDataFrame): a GeoDataFrame of the results, including the polygons and associated tags
    """
    # get lists of building polygons and associated tags
    polygons, tags = linetopoly(query.ways)

    # convert tags to a Dataframe and insert polygons
    tags = pd.DataFrame(tags)
    polygons = pd.DataFrame(polygons)
    polygons.columns = ["geometry"]
    polygons = polygons.join(tags, how="left")

    # convert to a GeoDataFrame and return
    final = gpd.GeoDataFrame(polygons)
    return final



# converts possible query values to the correct format
def formatquery(bounds, key, value):
    """
    Parameters:
    bounds (list or comma-seperated values): set of bounds for bbox
    key (string): key for the overpass query
    value (string): value for the overpass query

    Returns:
    bounds (string): string format of bbox
    key (string): reformatted key, if needed
    """
    bounds = str(bounds)

    # if the bounds are a list, replace brackets with parentheses
    if bounds[0] == "[":
        bounds = bounds.replace("[", "(")
        bounds = bounds.replace("]", ")")

    # determine how to format key and value
    if value != "":
        key = key + "="
    return bounds, key


# queries buildings using input
def buildingquery(bounds, building_key, building_value):
    """
    Parameters:
    bounds (list or comma-seperated values): set of bounds for bbox
    building_key (string): key for the overpass query (ex. amenity, building, etc.)
    building_value (string): value for the overpass query (ex. hospital, restaurant, etc.)

    Returns:
    result (Overpy Result object): the results of the query
    """

    bounds, building_key = formatquery(bounds, building_key, building_value)

    # this uses the overpy query method
    # example query is amenity=restaurant
    result = over.query(
        "way" + bounds + " [" + building_key + building_value + "]; (._;>;);out body;"
    )
    return result


# queries roads using input
def roadquery(bounds, road_key, road_value):
    """
    Parameters:
    bounds (list or comma-seperated values): set of bounds for bbox
    road_key (string): key for the overpass query (ex. highway, cycleway, etc.)
    road_value (string): value for the overpass query (ex. sidewalk, path, etc.)

    Returns:
    result (GeoDataFrame): the results of the query
    """

    bounds, road_key = formatquery(bounds, road_key, road_value)

    # this uses the overpass query method
    # example query is highway=footway
    api_data = api.get(
        "way" + bounds + " [" + road_key + road_value + "];(._;>;);",
        verbosity="geom",
    )

    # Make a GeoDataFrame from the data gathered from the query
    gdf = gpd.GeoDataFrame.from_features(api_data["features"])

    # Filter out all results except for the actual polylines
    result = gdf[gdf["geometry"].apply(lambda x: x.type == "LineString")]
    return result
