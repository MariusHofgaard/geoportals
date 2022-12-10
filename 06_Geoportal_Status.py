import ast
import streamlit as st
import leafmap.foliumap as leafmap

from csv import writer
from owslib.wms import WebMapService
from shapely.geometry import Polygon
from shapely import wkt
import shapely
import tempfile
import streamlit.components.v1 as components
import folium
import geojson

import pickle
import pandas as pd 
import re
import geopandas as gpd

from io import StringIO

import json
from ipyleaflet import Map, WKTLayer

import csv

import random
st.set_page_config(layout="wide")


def app():

    iso_3 = pickle.load(open("ISO_3.pkl", "rb"))

    with open("categories.txt", 'r') as f:
        # Read all lines from the file
        lines = f.readlines()
    sub_categories = [line for line in lines]

    with open("regional_categories.txt", 'r') as f:
        # Read all lines from the file
        lines = f.readlines()
    regional_categories = [line for line in lines]

    width = 800
    height = 600
    layers = None
    default = None

    countries = st.multiselect(
        "Select ISO3 country code to view on the map:", iso_3, default=default)
    sub_categories = st.multiselect(
        "Select a category to view on the map (if no category is selected all is shown)", sub_categories, default=default
    )
    regional_categories_selected = st.multiselect(
        "Select a data granularity to view on the map (if no granularity is selected all is shown)", regional_categories, default=default
    )

    # remove new line from sub_categories, regional_categories
    sub_categories = [sub_category.replace('\n', '') for sub_category in sub_categories]
    regional_categories_selected = [regional_category.replace('\n', '') for regional_category in regional_categories_selected]

    if countries != [] or sub_categories != []:
        st.write(f"You have selected country: {countries} and category: {sub_categories}")

        m = leafmap.Map(zoom = 2, center = [0, 0], height=height)

        # for each in storage
        geoportals = pd.read_excel("geoportals.xlsx", header=0)
        # st.write(geoportals.head())
        
        # create an empthy dataframe 
        all_filtered_1 = pd.DataFrame()
        if countries != []:
            for country in countries:

                st.write(country)
                all_filtered_temp = geoportals[geoportals['countries'].str.contains(country)]
                
                # append all_filtered to all_filtered_1
                all_filtered_1 = all_filtered_1.append(all_filtered_temp)

        # st.write(all_filtered_1.head())

        if sub_categories != []:
            all_filtered_2 = pd.DataFrame()
            for sub_category in sub_categories:
                all_filtered_temp = all_filtered_1[all_filtered_1['sub_categories'].str.contains(sub_category)]
                all_filtered_2 = all_filtered_2.append(all_filtered_temp)
        else:
            all_filtered_2 = all_filtered_1

        if regional_categories_selected != []:
            # st.info("Filtering by data granularity")

            all_filtered_3 = pd.DataFrame()
            for regional_category in regional_categories_selected:

                # st.info(regional_category)

                all_filtered_temp = all_filtered_2[all_filtered_2['regional_categories'].str.contains(regional_category)]
                all_filtered_3 = all_filtered_3.append(all_filtered_temp)
        else:
            all_filtered_3 = all_filtered_2



        # check if lenght of all_paths is greater than 0
        if len(all_filtered_3) > 0:

            # open the alt_filteres_2 in the map

            list_of_text_geojson = list(all_filtered_3.geojson_string)

            list_of_gdf = []

            for i, text_geojson in enumerate(list_of_text_geojson):
                # convert text_geojson to gdf
                # convert the string representation of a list text_geojson to a list
                try:

                    # Gets the WKT from the dataframe
                    list_geojson = ast.literal_eval('''{}'''.format(text_geojson))

                    for j, geojson in enumerate(list_geojson):
                            json_geojson = json.loads(geojson)
                            # convert the string representation of a geojson to a geopandas dataframe
                            gdf = gpd.GeoDataFrame.from_features(json_geojson["features"])
                            gdf[all_filtered_3.columns.difference(["geojson_string"])] = all_filtered_3.iloc[i][all_filtered_3.columns.difference(["geojson_string"])]
                            gdf = gdf.set_crs("Epsg:4326")
                            list_of_gdf.append(gdf)
                    
                    for gdf in list_of_gdf:
                        m.add_gdf(gdf, fill_colors = ["green"])
                except: 

                    # GETS THE WKT FROM FILE
                    st.info("Error parsing geometry. Geometry is likely too large for storage, extracting from saved file.")
                    list_geojson = []
                    if regional_categories_selected != []:
                        try:
                            gadm = gpd.read_file(f"gadm/{country}/gadm41_{country}_1.shp")
                        except:
                            gadm = gpd.read_file(f"gadm/{country}/gadm36_{country}_1.shp")
                        

                        for sub_national_region in list(all_filtered_3["NAME_1"].unique()):
                            gadm_sub_national = gadm[gadm['NAME_1'].str.contains(sub_national_region)]
                            gadm_sub_national.geometry = gadm_sub_national.geometry.simplify(.6)
                            list_geojson.append(gadm_sub_national.to_crs(epsg=4326).to_json())
                    
                    elif countries != []:
                        for country in countries:
                            try:
                                gadm = gpd.read_file(f"gadm/{country}/gadm41_{country}_0.shp")
                            except:
                                gadm = gpd.read_file(f"gadm/{country}/gadm36_{country}_0.shp")
                            


                            gadm[all_filtered_3.columns.difference(["geojson_string"])] = all_filtered_3.iloc[i][all_filtered_3.columns.difference(["geojson_string"])]

                            # st.write(gadm.columns)
                            gadm.geometry = gadm.geometry.simplify(.6)

                            list_geojson.append(gadm.to_crs(epsg=4326).to_json())


                    for wkt_geom in list_geojson:
                        try:
                            m.add_geojson(json.loads(wkt_geom), fill_colors = ["green"]) 
                        except:
                            st.error("No matching data found")
        else:
            st.subheader("no data found")
        m.to_streamlit(height=height)

        st.write(all_filtered_3.head()) 

# excel_file = "file_name.xlsx"

# dataframe.to_excel(excel_file)


app()
