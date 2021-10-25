import os
import shutil
from time import time
import numpy as np
import geopandas as gpd
import shapely.geometry as shp

"""
General geometry/crs manipulation tools.
No functionality in this module should be API-specific. 

Contians some constants for sample image areas.

Also includes some misc printing.
"""

# Printing

def print_header(text: str, sep: str = '-'):
    """ Prints header text. """
    print(text)
    print(sep * len(text))


def file_size(filepath: str = None, size: int = None, decimals: int = 3) -> str:
    """ 
    Creates a formatted string representing byte size.
    Source: kirbykit/doc
    """
    SIZE_REF = [("TB", 1e12), ("GB", 1e09), ("MB", 1e06), ("KB", 1e03)]
    
    if filepath:
        size = float(os.path.getsize(filepath))
    elif size:
        size = float(size)
    else:
        raise RuntimeError("Either a file or the file size as an integer must be passed to format.")  
    for (tag, thresh) in SIZE_REF:
        if (size >= thresh): 
            adjusted = size / thresh
            return "{} {}".format(np.round(adjusted, decimals=decimals), tag)
    return "{} Bytes".format(size)


def count_data(data, a):
    """ Recursively count any element in iterable."""
    def compare(b, a):
        if not isinstance(b, type(a)):
            return False
        return (b == a)
    count = 0
    if isinstance(data, list):
        for item in data:
            count += count_data(item, a)
    elif isinstance(data, dict):
        for _, item in data.items():
            count += count_data(item, a)
    elif compare(data, a):
        return 1
    return count

def show_keys(data: dict) -> None:
    """
    Print dict as grid.
    Source: kirbykit/doc
    """
    header = f"Keys: (total = {len(data.keys())})"
    print(header)
    print('-' * len(header))
    
    key_buff = len(max(data.keys(), key = len))
    type_buff = len(max([type(item).__name__ for _, item in data.items()], key = len))
    
    key_string = '|'
    for idx, (key, item) in enumerate(data.items()):
        key_string += f" '{key}'".ljust(key_buff+3)
        key_string += f"({type(item).__name__})".ljust(type_buff+2)
        key_string += " |"
        if (len(key_string) > 150):
            print(key_string)
            key_string = '|'
        elif (idx+1 == len(data.keys())):
            print(key_string)


def show_dict(data: dict, title: str = "dict keys", depth: int = 0, max_depth: int = 4) -> None:
    """
    Prints grossly nested dictionaries.
    Source: kirbykit/doc
    """
    spaces = " " * depth
    if title and depth == 0:
        print(title)
        print("-"* len(title))
    for key, item in data.items():
        if isinstance(item, dict):
            if depth < max_depth:
                print(f"{spaces}- {key} ({type(item).__name__}):")
                show_dict(data=item, title="", depth=depth+1, max_depth=max_depth)
            else:
                print(f"{spaces}- {key} ({type(item).__name__}): {item.keys()}")
        elif isinstance(item, list):
            # List printing needs improvement.
            print(f"{spaces}- {key} ({type(item).__name__}): length={len(item)} type={type(item[0]).__name__}")
            print(f"{spaces}  {item}")
        else:
            print(f"{spaces}- {key} ({type(item).__name__}): {item}")
    if depth == 0:
        print()
        
# User input
def prompt_cities(dict_only: bool = False, prompt_type: str = 'jupyter'):
    """ 
    Prompt user for a list of bounding boxes to test the system with. 
        
    Args:
        dict_only (bool): optionally only return dict with coords.
            default = False
    
    Returns:
    if dict_only:
        dict: coordinate data for city.
    else: (default)
        dict: bounding coordinate floats and metadata for selected city
            - 'size' (str): Raster size    
            - 'filename' (str): filename used to label this set 
            - 'scale' (int): Pixel scale to sample (in meters)
             
            - 'west' (float): minimum longitude
            - 'south' (float): minimum latitude
            - 'east' (float): maximum longitude
            - 'north' (float): maximum latitude
            
    """
    
    if (prompt_type != "jupyter"):
        raise NotImplementedError("Only one prompt type available using the std lib 'input()'.")
    
    # Must have state tag as last four characters.     
    CITIES = {
        "Austin, TX": {
            'size': "14.601 MB",
            'filename': 'austin', 
            'west': -97.7699, 
            'south': 30.2237, 
            'east': -97.7212, 
            'north': 30.3040,
            'scale': 4
        },
        "New York, NY": {
            'size': "192.438 MB", 
            'filename': 'new_york',
            'west': -74.4034, 
            'south': 40.3712, 
            'east': -73.5918, 
            'north': 40.9359,
            'scale': 10
        },
        "Tuscaloosa, AL": {
            'size': "298.448 MB",
            'filename': 'tuscaloosa',
            'west': -87.57477, 
            'south': 33.16558, 
            'east': -87.48422, 
            'north': 33.23129,
            'scale': 1
        },
        "Victoria Beach, Canada": {
            'size': "NA",
            'filename': 'victoria_beach',
            'west': -96.5898, 
            'south': 50.6534, 
            'east': -96.4925, 
            'north': 50.7709,
            'scale': 1
        }
    }    
    options = []
    print_header("Available cities for download:")
    for idx, (name, data) in enumerate(CITIES.items()):
        print("{:02}. {}".format(idx, name))
        for k in ['size', 'scale', 'filename']:
            print(f"- {k}: {data[k]}")
        options.append((name, data))
    print()
    while True:
        selection = input("Select by index: ")
        
        if not selection.isdigit():
            print(f"Invalid Selection, please enter an integer within (0, {len(CITIES.keys())-1}).")
            continue
        
        selection = int(selection)
        if (selection > len(options)-1) or (selection < 0):
            print(f"Invalid index, must be between 0 and {len(options)} please try again.")
            continue
        
        print("Using selected city:", options[selection][0])
        print()
        return options[selection][1]
        

def prompt_filename(default_name: str):
    """ Allows user to enter a filename, it's cleaned and returned. """
    filename = input(f"Enter a file name or use default ('{default_name}'):")
    
    mods = 0
    if filename == '':
        filename = default_name
        print(f"Using default filename: '{default_name}'")
        return default_name
    
    if ' ' in filename:
        filename = filename.replace(' ', '_')
        mods += 1
    if '.tif' in filename:
        filename = filename.replace('.tif', '')
        mods += 1
    print(f"Using provided filename after {mods} modifications: '{filename}'")
    return filename

# Pathing
def make_set_folder(root: str, name: str):
    """ Create directory for data output, indexing duplicate names """
    if not os.path.exists(root):
        os.mkdir(root)
    else:
        # Stores highest index, saves at +1
        max_index = 0
        for f in os.listdir(root):
            fpath = os.path.join(root, f)
            if (len(os.listdir(fpath)) == 0):
                print(f"> Removing empty test folder: '{fpath}'")
                os.rmdir(fpath)
            elif name in f:
                if f[-7] == '_': # Has index
                    current_index = int(f[-3:])
                    if max_index < current_index:
                        max_index = current_index
        if max_index > 0:
            name += "_{:02}".format(max_index+1)
    output_dir = os.path.join(root, name)
    os.mkdir(output_dir)
    return name, output_dir

def fmt_time(time_data) -> str:
    """ 
    Formats a time interval as string. 
    
    Args:
        time_data (float/iterable): Represents volume of time for formatting  
            if float:
                Treated as seconds
            if iterable, len(2):
                Treated as two timestamps to compare for output.
            if iterable, len(>2): [Not implemented]
                treated as a sequence of timestamps, 
                returns a list of strings representing 
                the time elapsed between each stamp.

    Returns:
        str: Formatted time as string
    """
    if isinstance(time_data, (float, int)):
        seconds = time_data
    elif isinstance(time_data, (list, tuple)):
        for s in time_data:
            if not isinstance(s, (float, int)):
                raise NotImplementedError(f"Only accepts output of time.perf_counter() for list/tuple items. Recieved: {type(s)}")
            
        if (len(time_data) > 2):
            time_intervals = []
            for i in range(0, (len(time_data)-1)):
                time_intervals.append(fmt_time((time_data[i], time_data[i+1])))
            return time_intervals
        elif (len(time_data) == 1):
            seconds = time_data[0]
        else:
            seconds = time_data[1] - time_data[0]
        
    if (seconds <= 1):
        return "{:.3f}s".format(seconds)
    
    t = {
        'h': np.floor(seconds / 3600),
        'm': np.floor((seconds % 3600) / 60),
        's': np.floor(seconds % 60),
    }
    t_string = ''
    for key, tdata in t.items():
        if (tdata >= 1):
            t_string += '{:02}{} '.format(int(tdata), key)
            
    return t_string

def color_excepthook():     
    """ 
    Exception coloring hook
    -----------------------
    from kirbykit/util
    """
    import sys, traceback
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import TerminalFormatter

    lexer = get_lexer_by_name("pytb" if sys.version_info.major < 3 else "py3tb")
    formatter = TerminalFormatter()

    def myexcepthook(type, value, tb):
        tbtext = ''.join(traceback.format_exception(type, value, tb))
        sys.stderr.write(highlight(tbtext, lexer, formatter))

    sys.excepthook = myexcepthook