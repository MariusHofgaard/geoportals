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

st.set_page_config(layout="wide")

import json
from ipyleaflet import Map, WKTLayer
import random



# A fuction to push a list of values to an excel file named geoportals.xlsx
def push_to_excel(url, countries,sub_national_regions, sub_categories, regional_categories, wkt):
    list = [url, countries, sub_national_regions,sub_categories, regional_categories, wkt]
    df = pd.read_excel("geoportals.xlsx")
    

    df_appendable= pd.DataFrame([list], columns= ['url', 'countries','sub_national_regions', 'sub_categories', 'regional_categories', 'geojson_string'])

    # append the new row to the existing dataframe
    df = df.append(df_appendable, ignore_index=True)

    df.to_excel("geoportals.xlsx", index=False, header=True)

def app():

    default = None
    height = 600
    iso_3 = pickle.load(open("ISO_3.pkl", "rb"))

    with open("categories.txt", 'r') as f:
        # Read all lines from the file
        lines = f.readlines()
    sub_categories = [line for line in lines]

    with open("regional_categories.txt", 'r') as f:
        # Read all lines from the file
        lines = f.readlines()

    regional_categories = [line for line in lines]
    url = st.text_input("Enter the url of the Geoportal")
    countries = st.multiselect("Select ISO3 country code:", iso_3, default=default)
    sub_categories = st.multiselect("Select multiple categories matching what the geoportal provides", sub_categories, default=default)

    # remove new line from sub_categories, regional_categories
    sub_categories = [sub_category.replace('\n', '') for sub_category in sub_categories]
    regional_categories_selectable = [regional_category.replace('\n', '') for regional_category in regional_categories]

    # import an excel file to a dataframe
    # get the wkt based on the ISO4 country code from file in gadm folder
    wkt = []
    if  countries != []:
        for country in countries:
            try:
                gadm = gpd.read_file(f"gadm/{country}/gadm41_{country}_0.shp")
            except:
                gadm = gpd.read_file(f"gadm/{country}/gadm36_{country}_0.shp")
            
            gadm.geometry = gadm.geometry.simplify(.9)
            if len(gadm.to_crs(epsg=4326).to_json()) > 300000:
                st.write("Simplifying geometry")
                gadm.geometry = gadm.geometry.simplify(1)


            wkt.append(gadm.to_crs(epsg=4326).to_json())

    sub_national_regions = []
    if countries != []:        
        possible_regions = []
        for country in countries:
            try:
                gadm = gpd.read_file(f"gadm/{country}/gadm41_{country}_1.shp")
            except:
                gadm = gpd.read_file(f"gadm/{country}/gadm36_{country}_1.shp")

            gadm.geometry = gadm.geometry.simplify(.8)
            # st.write(gadm['NAME_1'].unique().tolist())
            possible_regions = gadm['NAME_1'].unique().tolist()

        sub_national_regions = st.multiselect("(OPTIONAL) Select a sub-national region", possible_regions, default=default)

    if len(countries) > 1:
        regional_categories = ["Coverage - Multinational"]
    elif sub_national_regions == []:
        regional_categories = ["Coverage - National"]
    elif sub_national_regions != []:
        regional_categories = ["Coverage - Sub-national"]

    # st.write("The regional category is estimated as:", str(regional_categories[0]))
    
    regional_categories_overwrite = st.multiselect("(OPTIONAL) Overwrite the regional category", regional_categories_selectable, default=regional_categories)
    if regional_categories_overwrite != []:
        regional_categories = regional_categories_overwrite



    if sub_national_regions != []:
        wkt = []
        for sub_national_region in sub_national_regions:
            gadm_sub_national = gadm[gadm['NAME_1'].str.contains(sub_national_region)]
            wkt.append(gadm_sub_national.to_crs(epsg=4326).to_json())
    
    # leaflet map where center is the centroid of the wkt
    m = leafmap.Map(zoom = 2, center = [0, 0], height=height)
         
    for wkt_geom in wkt:
        m.add_geojson(json.loads(wkt_geom), style_callback=lambda feat: {"color": random.choice(["red", "green", "black"])})
        
    m.to_streamlit(height=height)

    submitted = st.button(
                        "Submit to storage",
                        on_click=push_to_excel,
                        args=(url, countries,sub_national_regions, sub_categories, regional_categories, wkt),
                        )


    if submitted:
        st.experimental_rerun()
app()