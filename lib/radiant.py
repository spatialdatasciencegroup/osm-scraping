import os, json, tarfile
from re import S
from typing import Collection

import radiant_mlhub as rhub
"""
radiant.py
----------
Tools to process Radiant ML Hub Data. 
Resource has since proven to be less than valuable.

STAC (SpatioTemporal Asset Catalog) is the standard format for 
spatial temporal data catalogs. This module seeks to parse it.
https://stacspec.org/STAC-api.html
"""


def list_datasets() -> None:
    """ Prints datasets from Radiant ML Hub. 
    
    TODO:
    Returns:
        list, containing a dict for each dataset:
            - 'idx' (int):  index of set, as it was printed. 
            - 'id' (str):   Original dataset ID assigned by radiant ml hub
            - 'size' (str): Size of dataset, formatted into a string.
    """
    print("Datasets in Radiant")
    print("-" * 19)
    for idx, dataset in enumerate(rhub.Dataset.list()):
        print("- {:02}. {}".format((idx+1), dataset.id))
        print("- Title: {}".format(dataset.title))
        print("- Image Sets: {}".format(len(dataset.collections.labels)))
        print("- Label Sets: {}".format(len(dataset.collections.source_imagery)))
        size_in_bytes = dataset.total_archive_size
        if isinstance(size_in_bytes, type(None)):
            print("- Size: NA")
        elif (size_in_bytes < 1e06):
            print("- Size: {} Bytes".format(size_in_bytes))
        elif (size_in_bytes < 1e09):
            print("- Size: {:.2f} MB".format(size_in_bytes / 1e06))
        else:
            print("- Size: {:.2f} GB".format(size_in_bytes / 1e09))
        print()
    return 

def show_labels(collection_id: str) -> None:
    
    items = rhub.client.list_collection_items(collection_id, limit=1)
    first_item = next(items)

    label_classes = first_item['properties']['label:classes']
    for label_class in label_classes:
        print(f'Classes for {label_class["name"]}')
        for c in sorted(label_class['classes']):
            print(f'- {c}')
            

def show_collection(collection_id: str) -> None:
    collection = rhub.client.get_collection(collection_id)
    print(collection_id.title())
    print(f'- Description: {collection["description"]}')
    print(f'- License: {collection["license"]}')
    print(f'- DOI: {collection["sci:doi"]}')
    print(f'- Citation: {collection["sci:citation"]}')
    
    
def download_dataset(root: str, set_id: str) -> None:
    """ 
    Get source imagery from dataset, download to folder,
    and extract datasets from tar.gz format. 

    Args:
        root (str):     Root folder for install 
        set_id (str):   ID for set assigned by Radiant
    Returns:
        list(str): List of archive paths.
    """
    # Create root dir if missing
    if not os.path.exists(root):
        os.mkdir(root)
        print(f"Created missing root directory: '{root}'")

    dataset = rhub.Dataset.fetch(set_id)
    
    set_dir = os.path.join(root, set_id)
    if not os.path.exists(set_dir): os.mkdir(set_dir)

    image_col_ids = [col.id for col in dataset.collections.source_imagery]
    
    output_paths = []

    for idx, collection in enumerate(dataset.collections):
        if (collection.id in image_col_ids):
            col_type = 'images'    
        else:
            col_type = 'labels'

        # Unsure if images and labels should be in different folders.
        out_dir = set_dir
        #out_dir = os.path.join(set_dir, col_type)
        #if not os.path.exists(out_dir): os.mkdir(out_dir)
        
        print(f"- Downloading {col_type}: '{collection.id}'")
        out_fp = collection.download(output_dir=out_dir)
        output_paths.append(out_fp)

        print(f"- Extracting {col_type}: '{collection.id}'")
        col_data = tarfile.open(out_fp)
        col_data.extractall(set_dir)
        col_data.close()

    return output_paths

def display_collection_folder(collection_dir: str):
    """ Prints contents of collection folder. """

    #! add checks for folder integrity...

    all_subfolders = os.listdir(collection_dir)

    print(f"Reading from collection: '{os.path.split(collection_dir)[1]}'")
    print(f"- Total Samples: {len(all_subfolders)-1}")
      
    if "collection.json" in all_subfolders:
       metadata_fp = os.path.join(collection_dir, "collection.json")
       print(f"- has metadata: '...{metadata_fp[-20:]}'") 

    sample_folder = all_subfolders[0]
    sample_fp = os.path.join(collection_dir, all_subfolders[0])

    print(f"- Sample Subfolder contents: ({os.path.split(sample_fp)[1]})")
    for sub_item in os.listdir(sample_fp):
        print(f"  - {sub_item}")


def get_parent_dataset(collection_id: str) -> str:
    """ 
    Returns ID of parent dataset to passed collection, 
    or None if not found. """
    dataset_ids = [dset.id for dset in rhub.Dataset.list()]
    for dset_id in dataset_ids:
        if dset_id in collection_id:
            return dset_id
    return None

def pull_collection(collection_id: str, root: str = './data/radiant_sets') -> str:
    """
    Downloads and extracts collection from Radiant ML Hub.pass
    
    Args:
        collection_id (str): ID of collection in Radiant ML Hub.
        root (str): Local root directory for all radiant sets.
    Returns:
        str: path to folder where data has been extracted for this collection.
    """

    parent_id = get_parent_dataset(collection_id=collection_id)
    parent_dir = os.path.join(root, parent_id)
    if not os.path.exists(parent_dir): os.mkdir(parent_dir)

    print(f"Downloading '{collection_id}'")
    collection = rhub.Collection.fetch(collection_id)
    out_fp = collection.download(output_dir=parent_dir)
    
    print(f"- Extracting '{out_fp}'")
    col_data = tarfile.open(out_fp)
    col_data.extractall(parent_dir)
    col_data.close()
    
    return out_fp[:-7]