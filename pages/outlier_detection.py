# Imports Libraries
# -----------------------------------------------------------
import streamlit as st
import joblib
import pandas as pd
import geemap
import eemont
import wxee

import geopandas as gpd
import ee
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score,accuracy_score,roc_curve,plot_roc_curve
from sys import modules

import os
import datetime

import folium
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import geemap.colormaps as cm
import geemap.foliumap as geemap
from datetime import date
from shapely.geometry import Polygon

st.set_page_config(layout="wide")
# -----------------------------------------------------------
#ee.Initialize()


# Main
# -----------------------------------------------------------
# App Title
st.title("Abandoned Buildings Classifier")


# Function for file upload
@st.cache
def uploaded_file_to_gdf(data):
    import tempfile
    import os
    import uuid

    _, file_extension = os.path.splitext(data.name)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(tempfile.gettempdir(), f"{file_id}{file_extension}")

    with open(file_path, "wb") as file:
        file.write(data.getbuffer())

    if file_path.lower().endswith(".kml"):
        gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"
        gdf = gpd.read_file(file_path, driver="KML")
    else:
        gdf = gpd.read_file(file_path)

    return gdf


# Remove unwanted columns from datasets
def remove_cols(dataset):

    st.write(dataset)
    st.write('perfoming remove_cols')
    if 'reducer' in dataset.columns:
        dataset = dataset.drop('reducer',axis=1)
    if 'date' in dataset.columns:
        dataset = dataset.drop('date',axis=1)
    if 'year' in dataset.columns:
        dataset = dataset.drop('year',axis=1)
    if 'month' in dataset.columns:
        dataset = dataset.drop('month',axis=1)
    if 'reducer_x' in dataset.columns:
        dataset = dataset.drop('reducer_x',axis=1)
    if 'reducer_y' in dataset.columns:
        dataset = dataset.drop('reducer_y',axis=1)
    if 'date_x' in dataset.columns:
        dataset = dataset.drop('date_x',axis=1)
    if 'date_y' in dataset.columns:
        dataset = dataset.drop('date_y',axis=1)           
    return dataset


# ---------------------------------------

# Add label to the pivots
def  preprocess(combined_dataset,geom):

    st.write('perfoming preprocessing')
    geom_gdf_test=geemap.ee_to_geopandas(geom)
    #st.write(geom_gdf_test)
    geom_gdf = geemap.ee_to_geopandas(geom['geometry'])
    #st.write(geom_gdf)
    labels = []
    #=combined_dataset['label']
    #st.write(combined_labeled)
    if('pivot' in combined_dataset):
        for i in combined_dataset['pivot'].unique():
            combined_dataset_2 = combined_dataset[combined_dataset['pivot']==i].reset_index().drop('index',axis=1)  #checks value of pivot
            #st.write(combined_dataset_2)
            labels.append(combined_dataset_2['label'].loc[0])
            st.write(len(labels))
            st.write('avg_Rad')
            st.write(combined_dataset_2['avg_rad'].mean())
            #st.write('vgnirbi')
            #st.write(combined_dataset_2['VgNIRBI'].mean())
            #st.write('ndbi')
            #st.write(combined_dataset_2['NDBI'].mean())
            st.write('Embi')
            st.write(combined_dataset_2['EMBI'].mean())
        st.write(len(labels) )
        st.write(len(geom_gdf)) # den douleuei to = logw len, checkare to length  tou geodataframe me auto,
        geom_gdf['label'] = labels
        geom_gdf['pivot'] = combined_dataset['pivot'].unique()
    else:
        geom_gdf['label'] = combined_dataset['label'].loc[0]
    #geom_gdf = geom_gdf.merge(labels,how='left',on='')
    # st.write(geom_gdf)
    # labels=[]
    # for i in combined_labeled.unique():
    #     labels.append(i)
    #     combined_labeled=pd.DataFrame({'label':labels})
    #     st.write(combined_labeled)
    
    # #labels= pd.DataFrame()
    # labels = []
    # #gdf_to_df = pd.DataFrame(geom_gdf)
    # for i in combined_labeled['label']:
    #     st.write(i)
    #     #prepei na valw sto df to swsto label gia kathe pivot
    #     #mexri twra epairne mono to teleutaio label 
    #     #ara prepei  na kanw append se kapoio buffer
    #     labels.append(i) 
    #     st.write(labels)
    #     #geom_gdf['label']=i
    # labels = pd.DataFrame({'label':labels}) #labels.append(geom_gdf['label'],ignore_index=True)
   
        #labels = labels.append(geom_gdf['label'],ignore_index=True)
    #gdf_to_df = geom_gdf.merge(geom_gdf,labels,axis=1,ignore_index=True)
    #gdf = gpd.GeoDataFrame(gdf_to_df) # geometry='geometry'
    #st.write(gdf_to_df) #  debugging
    st.write(geom_gdf)

        
        #gdf_ee= geemap.geopandas_to_ee(geom_gdf)
        
        #st.write(type(gdf_ee))
    return  geom_gdf

def create_final_pandas(ts_pandas):
    
    # Function that takes a time series dataframe as input
    # Checks if the user asked for gridded area
    # Does the Classification
    # Add labels accordingly
    # Returns the new time series dataframe with labels.
    ts_pandas=ts_pandas.drop(['IBI','VrNIRBI', 'NDBI' ,'NDVI','PISI','VgNIRBI'],axis=1)

    #ts_pandas=ts_pandas.drop(['IBI','VgNIRBI','VrNIRBI','EMBI', 'PISI' ],axis=1)
    #refer to this : https://stackoverflow.com/questions/28669482/appending-pandas-dataframes-generated-in-a-for-loop
    ts_df_buffer = pd.DataFrame() # empty df for appending

    if 'pivot' in ts_pandas:
        for i in ts_pandas['pivot'].unique():
            #print(i)
            ts_pandas_s2 = ts_pandas[ts_pandas['pivot']==i].reset_index().drop('index',axis=1)  #checks value of pivot
            # first  random  forest classifier
            # model = joblib.load('simple_classification.pkl')
            # prediction = model.predict(ts_pandas_s2.drop('pivot',axis=1))
            #random   forest  chicago classifier
            avg_embi_04_clf = "https://raw.githubusercontent.com/ckyriakos/Thesis--BI-through-ML-from-Satellite-Data/ocsvm_avg_rad_embi_04.pkl"
            model = joblib.load(avg_embi_04_clf)
            prediction = model.predict(ts_pandas_s2.drop('pivot',axis=1))
            st.write(prediction[0]) #  debugging

            # adds labels  according to the classification result
            if(prediction[0]==1):
                ts_pandas_s2['label'] =1
            elif(prediction[0]==-1):
                ts_pandas_s2['label'] =-1
            #st.write('ts_pandas_s2')  #debugging
            
            ts_df_buffer = ts_df_buffer.append(ts_pandas_s2,ignore_index=True)
            #st.write(ts_df_buffer) # debugging
        #st.write(ts_df_buffer) # debugging
        #st.write(ts_pandas_s2) # debugging
        return ts_df_buffer
    else:
        model = joblib.load('simple_classification.pkl')
        prediction = model.predict(ts_pandas)
        if(prediction[0]==0):
            ts_pandas['label'] =0
        elif(prediction[0]==1):
            ts_pandas['label'] = 1        
        return ts_pandas

def app():

    today = date.today()

    st.markdown(
        """
        An interactive web app for finding the existence of abandoned buildings over a selected area
        using satellite data and  machine learning). 
    """
    )

    row1_col1, row1_col2 = st.columns([2, 1])

    if st.session_state.get("zoom_level") is None:
        st.session_state["zoom_level"] = 4

    st.session_state["ee_asset_id"] = None
    st.session_state["bands"] = None
    st.session_state["palette"] = None
    st.session_state["vis_params"] = None

    with row1_col1:
        Map = geemap.Map(
            basemap="HYBRID",
            plugin_Draw=True,
            Draw_export=True,
            locate_control=True,
            plugin_LatLngPopup=False,
        )
        Map.add_basemap("ROADMAP")

    with row1_col2:

        keyword = st.text_input("Search for a location:", "")
        if keyword:
            locations = geemap.geocode(keyword)
            if locations is not None and len(locations) > 0:
                str_locations = [str(g)[1:-1] for g in locations]
                location = st.selectbox("Select a location:", str_locations)
                loc_index = str_locations.index(location)
                selected_loc = locations[loc_index]
                lat, lng = selected_loc.lat, selected_loc.lng
                folium.Marker(location=[lat, lng], popup=location).add_to(m)
                Map.set_center(lng, lat, 12)
                st.session_state["zoom_level"] = 12
        #roi_options = ["Uploaded GeoJSON"]
        # sample_roi = st.selectbox(
        #     "Select a sample ROI or upload a GeoJSON file:",
        #     roi_options,
        #     index=0,
        # )

    with row1_col1:

        with st.expander(
            "Steps: Draw a rectangle on the map -> Export it as a GeoJSON -> Upload it back to the app -> Click the Submit button. Expand this tab to see a demo 👉"
        ):
        
        #if sample_roi != "Uploaded GeoJSON":
        #    st.session_state["roi"] = geemap.geopandas_to_ee(gdf, geodesic=False)
        #    m.add_gdf(gdf, "ROI")
            data = st.file_uploader(
            "Upload a GeoJSON file to use as an ROI. Customize timelapse parameters and then click the Submit button 😇👇",
            type=["geojson", "kml", "zip"],
            )

            #data = st.empty()
        # if sample_roi != "Uploaded GeoJSON":
        #     st.session_state["roi"] = geemap.geopandas_to_ee(gdf, geodesic=False)
        #     m.add_gdf(gdf, "ROI")
        crs = "epsg:4326"

        gdf = uploaded_file_to_gdf(data)
        st.session_state["ROI"] = geemap.geopandas_to_ee(gdf, geodesic=False)
        Map.add_gdf(gdf, "ROI")

        # gdf_2 = uploaded_file_to_gdf(data)

        # gdf_geom = geemap.geopandas_to_ee(gdf_2)
        
        # #st.session_state["roi split"]=  
        # split =geemap.fishnet(gdf_geom, rows=10, cols=10, delta=1)
        # st.session_state["roi split"]=  split
        # #m.add_gdf(split, "ROI  split")
        # m.addLayer(split, {}, 'ROI Fishnet')
        Map.to_streamlit(height=600)
        return gdf,Map

        #filepath  = 'https://raw.githubusercontent.com/ckyriakos/Thesis--BI-through-ML-from-Satellite-Data/master/nea_ionia.geojson'
        
def  do_stats(dataset):
    st.write('correlation   matrix')
    
    # fig, ax = plt.subplots()
    # sns.heatmap(dataset.corr(), ax=ax)
    # st.write(fig)

    #outliers=[]

    # def detect_outlier(dataset):
        
    #     threshold=3
    #     mean_1 = np.mean(dataset)
    #     std_1 =np.std(dataset)
        
        
    #     for y in dataset:
    #         z_score= (y - mean_1)/std_1 
    #         if np.abs(z_score) > threshold:
    #             outliers.append(y)
    #     return outliers
    #     #nea_ionia  = gpd.read_file(filepath)
    # st.write('outliers')
    # outlier_datapoints = detect_outlier(dataset)
    # st.write(outlier_datapoints)
    # q1, q3= np.percentile(dataset,[25,75])
    # iqr = q3 - q1
    # st.write('iqr')
    # st.write(iqr)
    # st.write('bounds: lower and upper then')
    # lower_bound = q1 - (1.5 * q1)
    # upper_bound = q3 + (1.5 * q3)
    # st.write(lower_bound)
    # st.write(upper_bound)

def time_series_by_regions(gdf,Map):
        st.write('perfoming time_series')

        st.write(grid_col)
        st.write(grid_row)
        st.write('gdf   in time_series_by_regions before  fishnet')
        st.write(gdf)
        st.write(len(gdf))
        # Turn the geopandas into a ee.FeatureCollection
        gdf_geom = geemap.geopandas_to_ee(gdf)
        st.write('gdf_geom   in time_series_by_regions before  fishnet')
        st.write(gdf_geom)
        st.write(len(gdf_geom))
        gdf_fishnet = geemap.fishnet(gdf_geom, rows=grid_row, cols=grid_col, delta=1)

        gdf_fishnet_gdf = geemap.ee_to_geopandas(gdf_fishnet['geometry'])
        gdf_fishnet_gdf.crs = "EPSG:4326"
        st.write('gdf_fishnet_gdf  in time_series_by_regions after  fishnet')
        st.write(gdf_fishnet_gdf)
        st.write(len(gdf_fishnet_gdf))
        st.session_state["Fishnet"] = geemap.geopandas_to_ee(gdf_fishnet_gdf, geodesic=False)
        Map.add_gdf(gdf_fishnet_gdf, "Fishnet")
        # Make an equal-size polygon grid
        #gdf_fishnet = geemap.fishnet(gdf_geom, rows=grid_row, cols=grid_col, delta=1)
        Map.centerObject(gdf_geom, 9)
        #m.addLayer(gdf_geom, {}, 'Nea Ionia')

       # m.addLayer(gdf_fishnet, {}, 'Nea Ionia Fishnet')

        gdf_fishnet_geom = geemap.ee_to_geopandas(gdf_fishnet['geometry'])
        #nea_ionia_gdf = geemap.ee_to_geopandas(nea_ionia_fishnet)
        ## Add pivot

        st.write('fishnet gdf in time_series by regions')
        st.write(gdf_fishnet_geom)
        # I don't think this is a good practice but otherwise I got an error
        gdf_fishnet_geom['pivot'] = 1
        st.write(len(gdf_fishnet_geom))
        for i in range(len(gdf_fishnet_geom)):
            gdf_fishnet_geom['pivot'].loc[i] = i
        # set crs for greece
        gdf_fishnet_geom.crs = "EPSG:4326"
        #nea_ionia_gdf.crs = "EPSG:2100"
        st.write('fishnet gdf in time_series by regions after adding labels')
        st.write(len(gdf_fishnet_geom))
        fishnet_fc = geemap.geopandas_to_ee(gdf_fishnet_geom)

        #### time_series  #####
    
        #without getting monthly  mean
        
        s2 = (ee.ImageCollection("COPERNICUS/S2_SR")
                .filterDate('2021-06-01','2022-06-01')
                .filterBounds(fishnet_fc)
                .maskClouds()
                .scaleAndOffset()
                .spectralIndices(['NDVI','NDBI','IBI','EMBI','VgNIRBI','VrNIRBI','PISI'],online=True)).select([ 'NDVI', 'NDBI', 'IBI', 
                                                                                             'EMBI','VgNIRBI','VrNIRBI','PISI'])
        st.write(len(s2))
                #.spectralIndices(['NDVI','NDBI','UI','IBI']))
        st.write('done collecting')
        st.write('Now filtering')
        ts = s2.wx.to_time_series() 
        # getting monthly mean
        cloudless = ts.filterBounds(fishnet_fc).filterMetadata("CLOUDY_PIXEL_PERCENTAGE", "less_than", 5)
        ts_mean =  cloudless.aggregate_time(frequency="month",reducer=ee.Reducer.mean())
        #st.write('done collecting')
        st.write('Now getting time series')
        ts = ts_mean.getTimeSeriesByRegions(collection = fishnet_fc,
                                       #bands = ['NDVI','NDBI','UI','IBI'],
                                       bands=['NDVI','NDBI','IBI','EMBI','VgNIRBI','VrNIRBI','PISI'],
                                       reducer = [ee.Reducer.mean()],
                                       scale = 10)
        st.write(len(ts)) 
        # if(ts.size().getInfo() >=5000):
        #   print('size  bigger than 5000')
        #   #getting first 5000 elements
        #   reduced_ts = ts.toList(5000)
        #   #making fc of said list
        #   ts = ee.FeatureCollection(reduced_ts)
        #   #reduced_fc.size().getInfo()
        # print('done specifying ts')
        st.write('Now creating dataframe')
        tsPandas = geemap.ee_to_pandas(ts)
        #st.write('done calculating')
        tsPandas[tsPandas == -9999] = np.nan
        tsPandas['date'] = pd.to_datetime(tsPandas['date'],infer_datetime_format = True)
        tsPandas['NDVI']=tsPandas['NDVI'].fillna(tsPandas['NDVI'].mean())
        tsPandas['NDBI']=tsPandas['NDBI'].fillna(tsPandas['NDBI'].mean())
        #tsPandas['UI']=tsPandas['UI'].fillna(tsPandas['UI'].mean())
        #tsPandas['IBI']=tsPandas['IBI'].fillna(tsPandas['IBI'].mean())

   
        tsPandas['EMBI']=tsPandas['EMBI'].fillna(tsPandas['EMBI'].mean())
        tsPandas['IBI']=tsPandas['IBI'].fillna(tsPandas['IBI'].mean())
        tsPandas['VgNIRBI']=tsPandas['VgNIRBI'].fillna(tsPandas['VgNIRBI'].mean())
        tsPandas['VrNIRBI']=tsPandas['VrNIRBI'].fillna(tsPandas['VrNIRBI'].mean())
        tsPandas['PISI']=tsPandas['PISI'].fillna(tsPandas['PISI'].mean())
        st.write('done calculating')
        #ts_pandas = remove_cols(tsPandas)

        #################  get for  viirs ###########################
        viirs = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG").filterDate('2021-06-01','2022-06-01').select('avg_rad').scaleAndOffset()
        st.write('Now collecting VIIRS')
        st.write(len(viirs))

        ts_viirs = viirs.getTimeSeriesByRegions(ee.Reducer.mean(),
                              collection = fishnet_fc,
                              scale = 10,
                              #bestEffort = True,
                              #maxPixels = 2e9,
                              dateFormat = 'YYYYMMdd'
                              )
        st.write(len(ts_viirs))
        st.write('Done collecting VIIRS')
        st.write('Start making  VIIRS  datafrane')
        viirs_df = geemap.ee_to_pandas(ts_viirs)
        viirs_df[viirs_df == -9999] = np.nan
        viirs_df['date'] = pd.to_datetime(viirs_df['date'],infer_datetime_format = True)
        st.write('display some stats for  debugging')
        
        ############# merge them based on year,month #########################
        tsPandas['year']=tsPandas['date'].dt.year
        tsPandas['month']=tsPandas['date'].dt.month
        viirs_df['year']=viirs_df['date'].dt.year
        viirs_df['month']=viirs_df['date'].dt.month
        st.write('Done,  start merging...')
        merge_dataset = tsPandas.merge(viirs_df,how='left',on=['year','month','pivot'])
    ################################################################################################
        ts_pandas = remove_cols(merge_dataset)

        st.write('do  some  stats')
        do_stats(ts_pandas)


        return ts_pandas,fishnet_fc
        
        #m.to_streamlit(height=600)

def time_series_by_region(gdf):
        st.write('perfoming time_series  by region')
        st.write(grid_row)
        st.write(grid_col)
        # Turn the geopandas into a ee.FeatureCollection
        gdf_geom = geemap.geopandas_to_ee(gdf)
        #gdf_fishnet = geemap.fishnet(gdf_geom, rows=grid_row, cols=grid_col, delta=1)

        
        s2 = (ee.ImageCollection("COPERNICUS/S2_SR")
                .filterDate('2020-01-01','2022-06-01')
                .filterBounds(gdf_geom)
                .maskClouds()
                .scaleAndOffset()
                .spectralIndices(['NDVI','NDBI','UI','IBI']))
        st.write('done collecting')
        st.write('Now filtering')
        ts = s2.wx.to_time_series()   
        # getting monthly mean
        cloudless = ts.filterBounds(gdf_geom).filterMetadata("CLOUDY_PIXEL_PERCENTAGE", "less_than", 5)
        ts_mean =  cloudless.aggregate_time(frequency="month",reducer=ee.Reducer.mean())
        #st.write('done collecting')
        st.write('Now getting time series')
        ts = ts_mean.getTimeSeriesByRegion(geometry = gdf_geom,
                                       bands = ['NDVI','NDBI','UI','IBI'],
                                       reducer = [ee.Reducer.mean()],
                                       scale = 10)
        # if(ts.size().getInfo() >=5000):
        #   print('size  bigger than 5000')
        #   #getting first 5000 elements
        #   reduced_ts = ts.toList(5000)
        #   #making fc of said list
        #   ts = ee.FeatureCollection(reduced_ts)
        #   #reduced_fc.size().getInfo()
        # print('done specifying ts')
        st.write('Now creating dataframe')
        tsPandas = geemap.ee_to_pandas(ts)
        #st.write('done calculating')
        tsPandas[tsPandas == -9999] = np.nan
        tsPandas['date'] = pd.to_datetime(tsPandas['date'],infer_datetime_format = True)
        tsPandas['NDVI']=tsPandas['NDVI'].fillna(tsPandas['NDVI'].mean())
        tsPandas['NDBI']=tsPandas['NDBI'].fillna(tsPandas['NDBI'].mean())
        tsPandas['UI']=tsPandas['UI'].fillna(tsPandas['UI'].mean())
        tsPandas['IBI']=tsPandas['IBI'].fillna(tsPandas['IBI'].mean())
        st.write('done calculating')
        ts_pandas = remove_cols(tsPandas)
        
        return  ts_pandas,gdf_geom

gdf_roi,Map = app()
col1, col2, col3= st.columns(3)

grid_col = col1.number_input("Enter your grid columns",min_value=0,step=1)
grid_row = col1.number_input("Enter your grid rows",min_value=0,step=1)

if st.button('Say hello'):
        st.write('Gridding and Finding Abandoned Buildings, pleas wait...')
        if(grid_col==0 and grid_row==0 ):
            st.write('gotta work')
            ts_pandas,gdf_geom =time_series_by_region(gdf_roi)
            ts = create_final_pandas(ts_pandas)
            st.write(ts) #debugging
            gdf = preprocess(ts,gdf_geom)
            Map=geemap.Map(basemap='HYBRID')
            st.write(type(gdf))
            st.write(type(gdf['label']))
            
            if (gdf['label'].loc[0]==0):
                gdf.crs = "EPSG:4326"
                st.session_state["Abandoned/Not_Abandoned"] = geemap.geopandas_to_ee(gdf, geodesic=False)
            
                Map.add_data(gdf,'label',colors=['green'], labels=['Not Abandoned'],layer_name='Abandoned/Not_Abandoned')

            else:
                gdf.crs = "EPSG:4326"
                st.session_state["Abandoned/Not_Abandoned"] = geemap.geopandas_to_ee(gdf, geodesic=False)
                Map.add_data(gdf,'label',colors=['red'], labels=['Abandoned'],layer_name='Abandoned/Not_Abandoned')
            Map.add_gdf(gdf_roi,'Original Roi')
            Map.to_streamlit(height=600)
        else:
            ts_pandas,gdf_fishnet_geom =time_series_by_regions(gdf_roi,Map)
            ts= create_final_pandas(ts_pandas)
            st.write(ts) #debugging
            gdf = preprocess(ts,gdf_fishnet_geom)
            gdf.crs = "EPSG:4326"
            Map_fish=geemap.Map(basemap='HYBRID')

            #st.session_state["Abandoned/Not_Abandoned"] = geemap.geopandas_to_ee(gdf, geodesic=False)
            #for i in range(len(gdf)):
            a=gdf[gdf['label']== 1]
            b=gdf[gdf['label']== -1]
                #if (gdf['label'].loc[i] == 0):
                #st.session_state["Abandoned/Not_Abandoned"] = geemap.geopandas_to_ee(gdf, geodesic=False)
            #st.session_state["Not_Abandoned"] = geemap.geopandas_to_ee(a, geodesic=False)
            if(len(a)>0):
                Map_fish.add_data(a,'label',colors=['green'], labels=['Not Abandoned'],layer_name='Not_Abandoned')
                #else:
            #st.session_state["Abandoned"] = geemap.geopandas_to_ee(b, geodesic=False)
            if(len(b)>0):
                Map_fish.add_data(b,'label',colors=['red'], labels=['Abandoned'],layer_name='Abandoned')
                #Map_fish.add_data(gdf,'label',colors=['green','red'], labels=['Not Abandoned','Abandoned'],layer_name='Abandoned/Not_Abandoned')
            Map_fish.add_gdf(gdf_roi,'Original Roi')
    #m.add_data(gdf,'label',colors=['green','red'],info_mode='on_hover',layer_name='Abandoned/Not_Abandoned',zoom_to_layer=False)
    #Map.add_gdf(gdf,fill_colors=['green','red'],layer_name='Abandoned/Not_Abandoned',zoom_to_layer=False)
            Map_fish.to_streamlit(height=600)
        #simple_classification(m,ts_pandas)
#
#https://ttgeospatial.com/2020/04/22/machine-learning-to-predict-urbanization-from-modis-and-viirs-satellite-data/

# A description



# Read geojson.
# This will be replaced with a way for the user to submit his own geojson
# For now this works for a roi in Nea Ionia,Volos, Greece

#nea_ionia_s2_fp = 'https://raw.githubusercontent.com/ckyriakos/Thesis--BI-through-ML-from-Satellite-Data/master/nea_ionia_mean.csv'
#nea_ionia_s2 = pd.read_csv(nea_ionia_s2_fp)


    # SIDEBAR
# -----------------------------------------------------------
# sidebar = st.sidebar
# df_display = sidebar.checkbox("Display Raw Data", value=True)
# if df_display:
#      st.write(ts_df)

#st.write(nea_ionia_s2)

