import os
import geopandas as gpd
import numpy as np
import pandas as pd
import regex as re
from string import ascii_uppercase


COLS_TO_DROP = ['periodid', 'periodname', 'periodcode', 'perioddescription', 'dataid', 'dataname',
                       'datacode', 'datadescription', 'Total', 'date_downloaded']
CHECK_DUPLICATE_COLS = ['orgunitlevel2', 'orgunitlevel3', 'orgunitlevel4', 'organisationunitid']
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
    data_frame[column_name] = data_frame[column_name].str.lower()
    for word in words_to_remove:
        data_frame[column_name] = data_frame[column_name].str.replace(word, "")
    data_frame[column_name] = data_frame[column_name].str.strip()
    data_frame[column_name] = data_frame[column_name].sort_values()
    return_list = data_frame[column_name].unique()
    return_list = return_list[~pd.isna(return_list)]
    return return_list

def remove_words_df(data_frame, column_name, words_to_remove=WORDS_TO_REMOVE):
    """ Remove words from strings in a specified column

    Args:
        data_frame: Pandas data frame
        column_name: Column name to remove words from
        words_to_remove: List of words

    Returns:
        Removes words in place

    """
    data_frame[column_name] = data_frame[column_name].str.lower()
    for word in words_to_remove:
        data_frame[column_name] = data_frame[column_name].str.replace(word, "")
    data_frame[column_name] = data_frame[column_name].str.strip()
    data_frame[column_name] = data_frame[column_name].sort_values()
    data_frame.drop_duplicates(subset=[column_name], keep='first', inplace=True)
    data_frame.dropna(subset=[column_name], inplace=True)
    return data_frame

def remove_from_front(location_list, words_to_remove):
    new_loc_list = []
    location_list = np.unique(location_list)
    for loc_word in location_list:
        for front_bad_word in words_to_remove:
            loc_word = re.sub(f"^{front_bad_word}\s", "", loc_word)

        new_loc_list.append(loc_word)
    new_loc_list = [x.strip() for x in new_loc_list]
    new_loc_list = np.unique(new_loc_list)
    return new_loc_list


def removeFF_lambda(word, words_to_remove):
    for front_bad_word in words_to_remove:
        word = re.sub(f"^{front_bad_word}\s", "", word)

    return word


def remove_from_front_df(data_frame, column_name, words_to_remove):
    data_frame[column_name] = data_frame[column_name].apply(lambda x: removeFF_lambda(x, words_to_remove))
    data_frame.drop_duplicates(subset=[column_name], keep='first', inplace=True)
    return data_frame


def get_geoboundaries(num_admin_levels, iso3):
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

def process_masterDF(input_dir, input_filename, num_org_levels, cols_to_drop=COLS_TO_DROP, check_dupe_cols=CHECK_DUPLICATE_COLS):
    master_table = pd.read_csv(os.path.join(input_dir, input_filename), low_memory=False)
    print(f"Len of original data: {len(master_table)}")
    master_table.drop(cols_to_drop, axis=1, inplace=True)
    master_table.drop_duplicates(subset=check_dupe_cols, keep='first', inplace=True)
    master_table.reset_index(inplace=True)
    print(f"Len of clean data: {len(master_table)}\n")

    for orgNum in range(2, num_org_levels+1):
        the_len = len(master_table[f"orgunitlevel{orgNum}"].unique())
        print(f"Unique Level {orgNum}: {the_len}")

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

def getName(row, num_org_levels):
    for org_idx in range(num_org_levels-1, 0, -1): # reverse order
        if pd.notna(row[f'orgunitlevel{org_idx}']):
            return row[f'orgunitlevel{org_idx}'].lower()

    return "none"

