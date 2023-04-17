import os, sys
import geopandas as gpd
import jellyfish
import pandas as pd
from geopy.geocoders import GeoNames, Nominatim, Bing, GoogleV3
from shapely.geometry import Point
from tqdm import tqdm
from thefuzz import fuzz
from thefuzz import process
import matplotlib.pyplot as plt
from string import ascii_uppercase
import contextily as ctx
from os.path import join
from dotenv import load_dotenv, find_dotenv

COLS_TO_DROP = ['periodid', 'periodname', 'periodcode', 'perioddescription', 'dataid', 'dataname',
                       'datacode', 'datadescription', 'Total', 'date_downloaded']
CHECK_DUPLICATE_COLS = ['orgunitlevel2', 'orgunitlevel3', 'orgunitlevel4', 'organisationunitid',
                                         'organisationunitname']
WORDS_TO_REMOVE = ['community', 'clinic', 'centre', 'center', 'hospital', 'health', 'government']

def remove_words(data_frame, column_name, words_to_remove=WORDS_TO_REMOVE):
    """ Remove words from strings in a specified column

    Args:
        data_frame: Pandas data frame
        column_name: Column name to remove words from
        words_to_remove: List of words

    Returns:
        Removes words in place

    """
    for word in words_to_remove:
        data_frame[column_name] = data_frame[column_name].str.replace(word, "")
    data_frame[column_name] = data_frame[column_name].str.strip()
    data_frame[column_name] = data_frame[column_name].sort_values()
    return_list = data_frame[column_name].unique()
    return return_list

def get_geoboundares(num_admin_levels, iso3):
    """ Get the geoBoundaries for a specific country

        Args:
            num_admin_levels: The number of Admin levels available in The geoBoundaries Global Database
                                of Political Administrative Boundaries Database
            iso3: the iso3 country code

        Returns:
            an array of geo boundaries

        """
    base_url = "https://github.com/wmgeolab/geoBoundaries/raw/b7dd6a5/releaseData/gbOpen/"
    geob_arr = []

    for idx in range(1, num_admin_levels+1):
        geob = gpd.read_file(f"{base_url}{iso3}/ADM{idx}/geoBoundaries-{iso3}-ADM{idx}.geojson")
        geob_arr.append(geob)

    return geob_arr

def process_masterDF(input_dir, input_filename, cols_to_drop=COLS_TO_DROP, check_dupe_cols=CHECK_DUPLICATE_COLS):
    master_table = pd.read_csv(os.path.join(input_dir, input_filename), low_memory=False)
    print(f"Len of original data: {len(master_table)}")
    master_table.drop(cols_to_drop, axis=1, inplace=True)
    master_table.drop_duplicates(subset=check_dupe_cols, keep='first', inplace=True)
    master_table.reset_index(inplace=True)
    print(f"Len of clean data: {len(master_table)}\n")

    print(f"Unique Level 2: {len(master_table.orgunitlevel2.unique())}")
    print(f"Unique Level 3: {len(master_table.orgunitlevel3.unique())}")
    print(f"Unique Level 4: {len(master_table.orgunitlevel4.unique())}")
    print(f"Unique Level 5: {len(master_table.organisationunitname.unique())}")

    return master_table

def inspect_level_names(org_unit_level, org_level_list, geob_level, geob_list):
    for letter in ascii_uppercase:
        level_sublist = [name for name in org_level_list if name[0] == letter]
        geob_sublist = [name for name in geob_list if name[0] == letter]

        if len(level_sublist) > 0:
            print(f"Master list level {org_unit_level} ({len(level_sublist)})")
            print("\t" + str(level_sublist))
        if len(geob_sublist) > 0:
            print(f"Geoboundaries adm{geob_level} ({len(geob_sublist)})")
            print("\t" + str(geob_sublist))

        print("\n")

