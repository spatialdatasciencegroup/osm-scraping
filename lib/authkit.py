import os
from datetime import datetime as dt

"""
authkit.py
----------
Authentication tools and shorthands.

Todo:
Create setup script for keys. 
"""

import ee 
def ee_client(verbose=False):
    """
    Authenticates and initializes ee client.
    Returns synced time.
    
    Args:
        user (bool): Optionally force user auth for drive connection
            default = True
        verbose (bool): enable printing
            defualt = False
    """ 
    credentials_fp = ee.oauth.get_credentials_path() # This func may not work on windows, uses '/'
    if not os.path.exists(credentials_fp):
        ee.Authenticate()
    else:
        if verbose:
            print("> EE Auth: Loading user credentials from storage.")
        creds = ee.data.get_persistent_credentials() 
    ee.Initialize(creds)
    if verbose:
        print("> EE Auth: Initialization complete.")
    
    # Sync time
    ee_date = ee.Date('2020-01-01')
    py_date = dt.utcfromtimestamp(ee_date.getInfo()['value']/1000.0)
    if verbose:
        print("> EE Auth: Synced time.")
    return py_date



from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
def get_drive(settings_fp: str='settings.yaml', verbose: bool=False) -> GoogleDrive:
    """
    Authenticates PyDrive, returning the drive object.
    
    Notes:
        For configuring the settings file:
        https://pythonhosted.org/PyDrive/oauth.html
    
    Parameters:
        settings_fp (str): setttings file for pydrive. Must be yaml
            default = 'settings.yaml'
    Returns:
        GoogleDrive: Authenticated drive object
    Raises:
        RuntimeError: If passed settings file is not yaml.
    """
    
    if ('.yaml' not in os.path.splitext(settings_fp)[1]):
        raise RuntimeError(f"Can't use passed settings file, must be yaml format. Recieved:\n'{settings_fp}'")
    
    gauth = GoogleAuth(settings_file=settings_fp)   
    if ((settings_fp != 'settings.yaml') and verbose):
        print(f"> Drive Auth: Loaded settings from: '{settings_fp}'")
    gauth.LocalWebserverAuth()
    gdrive = GoogleDrive(auth=gauth)
    
    return gdrive