import geopandas as gpd
import pandas as pd
from geopy.geocoders import GeoNames, Nominatim, Bing, GoogleV3
from shapely.geometry import Point


def report_geocoding(records):
    """ Report value counts and % from geocoding_method column.

    Args:
        records: Pandas data frame

    Returns:
        Table with count stats
    """
    table = records[['NAME', 'geocoding_method']].groupby('geocoding_method').count().rename(columns={'NAME': 'count'})
    table.loc[:, "pct"] = table /(table['count'].sum())
    table = table.style.format({
        'pct': '{:,.1%}'.format,
    })
    return (table)


def run_geocoding(idx, row, master_table, admin_area, components, country_code, geolocator_bing, geolocator_osm, geolocator_google):
    """
    Geocoding workflow to be applied to each row in a dataset

    Args:
        idx: index
        row: row with index and names to geocode
        master_table: master table to store results
        admin_area: gdf of admin area to ensure result falls within
        components: list of names of attributes to use in query
        country_code: two letter iso code

    Returns:
        Stores geocoding results in master_table object
    """
    admin_bounds = admin_area.bounds

    try:
        bb = [(admin_bounds.iloc[0].miny, admin_bounds.iloc[0].minx),
              (admin_bounds.iloc[0].maxy, admin_bounds.iloc[0].maxx)]
    except:
        print(f"Error getting bounds for: {admin_area.shapeName}")
        bb = []

    method = ' and '.join(components)
    items = [row[item] for item in components]
    #print(f"Items: {items}")
    query = ', '.join(items)

    geocoding_result = None
    geocoding_method = "None"

    # Try Geocoding with OSM
    try:
        res = geolocator_osm.geocode(query, country_codes=country_code)
        # if within admin
        if admin_area.contains(Point(res.longitude, res.latitude)).values[0] == True:
            geocoding_result = res
            geocoding_method = f"{method} query OSM"
        else:
            raise Exception("OSM point not valid or not within polygon")
    except:
        # Try Geocoding with Bing Maps
        try:
            res = geolocator_bing.geocode(query)
            # if within admin
            if admin_area.contains(Point(res.longitude, res.latitude)).values[0] == True:
                geocoding_result = res
                geocoding_method = f"{method} query Bing"
            else:
                raise Exception("Bing point not valid or not within polygon")
        except:
            if len(bb) > 0:
                # Try Geocoding with Google
                try:
                    res = geolocator_google.geocode(query=query, region=country_code, bounds=bb)
                    if res:
                        # if within admin
                        if admin_area.contains(Point(res.longitude, res.latitude)).values[0] == True:
                            geocoding_result = res
                            geocoding_method = f"{method} query Google"
                except:
                    print(f"{admin_area.shapeName} not within polygon")
                    raise Exception("Google point not valid or not within polygon")
            else:
                print("Didn't find with BING or OSM, no bounding box for Google")

    master_table.loc[idx, "geocoding_method"] = geocoding_method
    if geocoding_result:
        master_table.loc[idx, "longitude"] = res.longitude
        master_table.loc[idx, "latitude"] = res.latitude
    else:
        master_table.loc[idx, "longitude"] = None
        master_table.loc[idx, "latitude"] = None

    return master_table

