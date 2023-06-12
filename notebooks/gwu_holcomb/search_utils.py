import os, sys
import geopandas as gpd
import jellyfish
import numpy as np
import pandas as pd
from geopy.geocoders import GeoNames, Nominatim, Bing, GoogleV3
from shapely.geometry import Point
from tqdm import tqdm
from thefuzz import fuzz
import regex as re
from thefuzz import process
import matplotlib.pyplot as plt
from string import ascii_uppercase
import contextily as ctx
from os.path import join
from dotenv import load_dotenv, find_dotenv


def match_name_old(name, list_names, min_score=0):
    """ Uses fuzzy matching between one string and a list of candidate names.

    Args:
        name: string
        list_names: list of candidate names to match
        min_score: minimum score allowed

    Returns:
        Returns name with the highest match, and match score
        If no match is higher than min score, returns "" and -1
    """
    # -1 score incase we don't get any matches
    max_score = -1
    # Returning empty name for no match as well
    max_name = ""
    # Iterating over all names in the other
    for name2 in list_names:
        # Finding fuzzy match score
        score = fuzz.ratio(name, name2)
        # Checking if we are above our threshold and have a better score
        if (score > min_score) & (score > max_score):
            max_name = name2
            max_score = score
    return (max_name, max_score)

def match_name(name, list_names, min_score=0, phonetic_threshold=75):
    """ Uses fuzzy matching between one string and a list of candidate names.

    Args:
        name: string
        list_names: list of candidate names to match
        min_score: minimum score allowed
        phonetic_threshold: minimum phonetic score allowed

    Returns:
        Returns name with the highest match, and match score
        If no match is higher than min score, returns "" and -1
    """
    # -1 score incase we don't get any matches
    max_score = -1
    # Returning empty name for no match as well
    max_name = ""
    # Iterating over all names in the other
    for name2 in list_names:

        # First try string matching - if we get an exact match, stop
        special_char_regex = r"[^\w\d]"

        regex_name = re.sub(special_char_regex, '', name.lower())
        try:
            regex_name2 = re.sub(special_char_regex, '', name2.lower())
        except:
            print(f"Error with name2: [{name2}]")
            regex_name2 = ""

        if regex_name == regex_name2:
            max_name = name2
            max_score = 100
            #print(f"Exact Match! [{regex_name}] == [{regex_name2}]")
            break

        # Finding fuzzy match score
        else:
            # get the phonetic score
            phon1 = jellyfish.metaphone(name) #.soundex(name)
            try:
                phon2 = jellyfish.metaphone(name2) #.soundex(name2)
                phon_score = fuzz.ratio(phon1, phon2)
            except:
                print(f"Error with name2: [{name2}]")
                phon_score = 0

            # get the fuzzy score
            try:
                fuzzy_score = fuzz.ratio(name, name2)
            except:
                print(f"Error with name2: [{name2}]")
                fuzzy_score = 0

            #print(f"{name} vs {name2}: phon: {phon_score}, fuzzy: {fuzzy_score}")
            winning_score = phon_score if (phon_score >= fuzzy_score and phon_score > phonetic_threshold) else fuzzy_score
            # Checking if we are above our threshold and have a better score
            if (winning_score > min_score) & (winning_score > max_score):
                max_name = name2
                max_score = winning_score

    return (max_name, max_score)


def match_to_closest(row, gdf, column='ADMIN2'):
    """ Spatial join using closest distance algorithm.

    Args:
        row: row from geo data frame
        gdf: gdf with attributes to join
        column: attribute to join

    Returns:
        Returns specified attribute of closest feature
    """
    distances = [row.geometry.distance(pol) for pol in gdf.geometry]
    min_id = np.argmin(distances)
    closest = gdf.iloc[min_id]
    return closest[column]

def find_matches(org_level_list, geob_list, min_score, curr_org_lvl, curr_geob_lvl):
    # List for dicts for easy dataframe creation
    dict_list = []
    # iterating over our players without salaries found above
    already_found = []
    search_list = geob_list
    for name in org_level_list:

        # Use our method to find best match, we can set a threshold here
        match = match_name(name, search_list, min_score)
        # print(f"{name}: {match}")

        # If the score is 100, remove it from the search list and add it to the found list
        if match[1] == 100:
            already_found.append(match[0])
            search_list.remove(match[0])

        # New dict for storing data
        dict_ = {}
        dict_.update({f"name_level{curr_org_lvl}": name})
        dict_.update({f"name_geob{curr_geob_lvl}": match[0]})
        dict_.update({"score": match[1]})
        dict_list.append(dict_)

    table_adm = pd.DataFrame(dict_list)
    table_adm_matches = table_adm[table_adm.score >= 80]

    return table_adm_matches

def find_matches_old(org_level_list, geob_list, min_score, curr_org_lvl, curr_geob_lvl):
    # List for dicts for easy dataframe creation
    dict_list = []
    # iterating over our players without salaries found above
    # already_found = []
    search_list = geob_list
    for name in org_level_list:

        # Use our method to find best match, we can set a threshold here
        match = match_name_old(name, search_list, min_score)
        # print(f"{name}: {match}")

        # New dict for storing data
        dict_ = {}
        dict_.update({f"name_level{curr_org_lvl}": name})
        dict_.update({f"name_geob{curr_geob_lvl}": match[0]})
        dict_.update({"score": match[1]})
        dict_list.append(dict_)

    table_adm = pd.DataFrame(dict_list)
    table_adm_matches = table_adm[table_adm.score >= 80]

    return table_adm_matches
