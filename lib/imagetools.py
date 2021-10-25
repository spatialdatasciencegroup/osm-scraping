import os
import ee
import geopandas as gpd
from google.oauth2.challenges import REAUTH_ORIGIN
import shapely.geometry as shp

from lib.geotools import to_region
from lib.misc import file_size, print_header, show_dict, show_keys

from datetime import datetime as dt
from pytz import timezone 
tz = timezone("US/Central")

"""
imagetools.py
-------------
Tools for manipulating and downloading raster imagery.
"""

# Earth Engine Tools        

def export_naip_image(gdrive, drive_folder, dset_data) -> str:
    """
    Exports an image from the NAIP dataset to the provided google drive.
    
    Args:
        - gdrive (GoogleDrive): Google Drive object to check for duplicate files.
        - drive_folder:         PyDrive File object, represents folder where rasters 
                                will be exported in Google Drive.
        - dset_data (dict):     Dict containing keyed data on area to extract.
                                - 'west','south',...:   lat/lon bounds as floats
                                - 'scale' (int):        resolution in meters per pixel
                                - 'filename' (str):     name to store output under
    Returns:
        str: filename as it appears in drive. Indexed '_{:02}' if a duplicate was located.
    """  
    drive_fp = dset_data['filename'] + '.tif'

    # Check for duplicate filename
    file_list = gdrive.ListFile({'q': f"title='{drive_fp}' and \
                                        '{drive_folder['id']}' in parents and \
                                        trashed=false and \
                                        mimeType='image/tiff'"}).GetList()
    
    if len(file_list) > 0:
        raise RuntimeError(f"Can't export image to google drive, file already exists under passed name: '{dset_data['filename']}'")
    
    naip_data = ee.ImageCollection("USDA/NAIP/DOQQ").filter(ee.Filter.date('2017-01-01', '2019-01-01'))
    naip_image = naip_data.mosaic()

    # Create 'task' to export the image, specifying scale and region.
    task = ee.batch.Export.image.toDrive(image=naip_image,          # EE Image to export
                                         description=dset_data['filename'],      # (str) Desription of task, will become exported file name
                                         fileFormat='GeoTIFF',      # (str) File export format
                                         region=to_region(dset_data),  # (list(5,2)) Bounds to crop image to
                                         folder=drive_folder['title'],       # (str) Ouput folder in drive
                                         scale=dset_data['scale'])               # (int) Pixel res in meters

    # Run Export task verbosely
    task.start()
    print(f"Started Image export of '{drive_folder['title']}/{drive_fp}' to drive.")
    last_state = None
    while True:
        if task.status()['state'] != last_state:
            print('>', task.status()['state'], dt.now(tz).strftime("[%H:%M:%S]"))
            last_state = task.status()['state']
            if (last_state == "COMPLETED"):
                print()
                return
            elif (last_state == "FAILED"):
                raise RuntimeError(task.status()['error_message'])
            
# Google drive tools

def show_rasters(gdrive):
    """ Prints all .tif files in drive. """
    query_string = f"title contains '.tif'"
    raster_list = gdrive.ListFile({'q': query_string}).GetList()
    # remove files without proper mimetype and extension
    raster_list = [f for f in raster_list if (('tif' in f['fileExtension']) and ('tif' in f['mimeType']))]
    show_drive_files(file_list=raster_list, name="rasters")
    
    
def show_drive_files(file_list: list, name: str = None): 
    """ Prints all files from query result in a pretty way. """
    if name:
        header = f"{name}: (total = {len(file_list)})"
        print(header)
        print('-' * len(header))
    for idx, f in enumerate(file_list):
        print("{:02}: {}".format(idx, f['title']))
        print("- size: {}".format(file_size(size=f['size'])))
        print("- version: {}".format(f['version']))
        print("- download:  {}".format(f['downloadURL']))
        print("- created: {}".format(f['createdDate']))
        print("- modified: {}".format(f['modifiedDate']))


def show_raster_keys(gdrive, show_items: bool = False):
    """ Prints keys for raster files as they appear in drive. """
    query_string = f"title contains '.tif'"
    raster_file = gdrive.ListFile({'q': query_string}).GetList()[0]
    if show_items:
        show_dict(raster_file)
    else:
        show_keys(raster_file)
    return raster_file


def download_raster(gdrive, drive_folder, set_name: str, out_dir: str, skip_conf: bool = False) -> str:
    """ 
    Downloads GeoTiff raster to file by name. 
    
    Note:
        Need to change argument to accept all dset data as dict.
    
    Args:
        - gdrive (GoogleDrive): Google Drive object to check for duplicate files.
        - drive_folder:         PyDrive File object, represents folder where rasters 
                                will be exported in Google Drive.
        - set_name (str):       Name for the output raster, must also appear under 
                                this name in drive with .tif ext.
        - out_dir (str):        Local output folder for raster.
        - skip_conf (bool):     When True, skips confirmation prompt.
                                    default : False
    Returns:
        str: filename as it appears locally.
    """
    
    # Query Drive
    query_string = f"title='{set_name}.tif' and \
                     '{drive_folder['id']}' in parents and \
                     trashed=false and \
                     mimeType='image/tiff'"
    file_list = gdrive.ListFile({'q': query_string}).GetList()
    if (len(file_list) == 0):
        print(f"No files found containing passed name: '{set_name}.tif' in folder '{drive_folder['title']}'. Returning None")
        return None
    elif (len(file_list) > 1):
        print(f"Multiple files found - Selection not implemented. Returning list.")
        return file_list
    
    target_file = file_list[0]
    
    # Prepare output path, assumes parent directory has been created
    out_path = os.path.join(out_dir, f'{set_name}.tif')

    print_header("Preparing for download:")
    print(f"- src:  {target_file['title']}")
    print(f"- size: {file_size(size=target_file['fileSize'])}")
    print(f"- out:  '{out_path}'")
    print()
    
    if skip_conf:
        choice = 'y'
    else:
        choice = input("Confirm download (y/[n]) ")
    
    if ('y' in choice):
        target_file.GetContentFile(out_path, 'image/tif')
        print(f"> Completed Raster download: '{out_path}'")
        return out_path
    else:
        print("Cancelled.")
        return None
    
    
def create_drive_folder(gdrive, name: str, verbose: bool=True):
    """ Creates folder in drive if it does not already exist. """
    
    # Check for existing folder.
    query_string = f"title='{name}' and mimeType='application/vnd.google-apps.folder'"
    results = gdrive.ListFile({'q': query_string}).GetList()
    if len(results) > 0:
        return results[0]
    
    # Create missing folder
    folder_metadata = {
        'name': f"create_folder:'{name}'",
        'title': name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = gdrive.CreateFile(folder_metadata)
    folder.Upload()
    
    if verbose:
        print("> Created folder in drive:", name)
    return folder
    