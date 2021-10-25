import numpy as np
import pandas as pd

"""
Visualization only for geometry and raster analysis.
"""


def gdf_relational_nulls(gdf, keys):
    
    null_report = {key: [] for key in keys}
    
    for _, row in gdf.iterrows():
        null_series = row.isnull()
        for key, item in null_report.items():
            is_filled = not null_series.get(key)
            item.append(is_filled)
            
    for key, item in null_report.items():
        null_report.update({key: np.asarray(item)})
    
    finished_key_a = []
    for idx, (key_a, item_a) in enumerate(null_report.items()):
        if idx+1 == len(null_report.keys()):
            break
        print(f"Comparing '{key_a}' ({np.count_nonzero(item_a == True)})")
        for key_b, item_b in null_report.items():
            if (key_a != key_b) and (key_b not in finished_key_a):
                print(f" - '{key_a}' and '{key_b}': {np.logical_and(item_a, item_b).sum()}")
        finished_key_a.append(key_a)

    return null_report

def gdf_null_values(gdf, blacklist: list = []):
    """ Gets number of null values in Geodataframe.
    
    Args:
        gdf (GeoDataFrame): Frame to print from 
        blacklist (list):   List of keys (str) to skip when printing.
        
    Returns:
        pd.DataFrame: Contains filled/empty counts labeled by column key
                        For passed GDF.
    """

    total = len(gdf.geometry) 
    count_data = []
    for key in gdf.columns:
        if key in blacklist:
            continue
        empty_count = gdf[key].isnull().sum()
        count_data.append({'key': key, 'filled': (total-empty_count), 'nulls': empty_count})

    counts = pd.DataFrame(count_data)
    counts.sort_values('nulls', inplace=True)
    return counts

def gdf_value_columns(gdf, keys: list = None, verbose: bool = True):
    """ Prints Value counts for each column in the passed list of keys. """
    if not keys:
        keys = [k for k in gdf.columns if k not in ['geometry', 'index']]
    elif isinstance(keys, str):
        keys = [keys]
    
    value_data = {}
    for key in keys:
        if key not in gdf.columns:
            print(f"Skipping missing key: '{key}'")
            continue
        values = gdf.value_counts(key)
        if verbose:
            print(f"{key} ({values.count()})")
        for value, count in values.iteritems():
            if verbose:
                print(f"  - '{value}': {count}")
        if verbose:
            print()
        value_data.update({key: values})
    return value_data



def print_unique_subkeys(gdf, key: str, name: str = "GDF"):
    unique_subkeys = {}
    for _, r in gdf.iterrows():
        category = r[key]
        rfulls = r.notnull()
        if category in gdf.columns:
            if category not in unique_subkeys:
                unique_subkeys.update({category: {'filled': 0, 'total': 0}})
            
            if rfulls.get(category):
                unique_subkeys[category]['filled'] += 1
            unique_subkeys[category]['total'] += 1


    print(f"{name}: '{key}'")
    for subkey, subdata in unique_subkeys.items():
        print(f"- '{subkey}':")
        for k, count in subdata.items():
            print(f'\t- {k}: {count}')
            
            
            
def gdf_overview(gdf, title):
    header = f"{title}:"
    print(header)
    print('-' * len(header))
    print(f"- Rows: {len(gdf.geometry)}")
    print(f"- Keys: {len(gdf.columns)}")
    print()