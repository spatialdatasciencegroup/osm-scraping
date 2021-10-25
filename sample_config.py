"""
Example Config File
-------------------
Contains environment-specific paths and keys. 
When runnning CLI and notebook, update these 
parameters and rename to config.py.

Variables
---------
gdrive_settings_fp : str
    Absolute path to .yaml file used to configue instance of PyDrive Client.
    https://pythonhosted.org/PyDrive/oauth.html

root_out_dir : str
    Local absolute/relative path for data output. 

gdrive_folder : str
    Name of folder in your google drive root to output rasters.
    The rasters may get big so be cautious 
"""

# PyDrive Authentication File
gdrive_settings_fp = '~/geo-scraping/keys/settings.yaml'

# Output folder for downloaded data
local_root = './data'

# Google Drive output folder
drive_folder_name = 'geo-scrape-sets'