from sys import modules
import ee
import os
import datetime
import geopandas as gpd
import folium
import streamlit as st
import geemap.colormaps as cm
import geemap.foliumap as geemap
from datetime import date
from shapely.geometry import Polygon


from cachetools import cached


st.set_page_config(layout="wide")

st.sidebar.title("About")
st.sidebar.info(
    """
    Stramlit for My Thesis

    Special Thanks to he creator of geemap, his work was crucial to the completion of my project!

    Web App URL: <https://geospatial.streamlitapp.com>
    GitHub repository: <https://github.com/giswqs/streamlit-geospatial>

    Qiusheng Wu: <https://wetlands.io>
    [GitHub](https://github.com/giswqs) | [Twitter](https://twitter.com/giswqs) | [YouTube](https://www.youtube.com/c/QiushengWu) | [LinkedIn](https://www.linkedin.com/in/qiushengwu)
    """
)

st.sidebar.title("Contact")
st.sidebar.info(
    """
    
    """
)



#@st.cache
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


def app():

    today = date.today()

    st.title("Create Satellite Timelapse")

    st.markdown(
        """
        An interactive web app for creating [Landsat](https://developers.google.com/earth-engine/datasets/catalog/landsat)/[GOES](https://jstnbraaten.medium.com/goes-in-earth-engine-53fbc8783c16) timelapse for any location around the globe. 
        The app was built using [streamlit](https://streamlit.io), [geemap](https://geemap.org), and [Google Earth Engine](https://earthengine.google.com). For more info, check out my streamlit [blog post](https://blog.streamlit.io/creating-satellite-timelapse-with-streamlit-and-earth-engine). 
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
        m = geemap.Map(
            basemap="HYBRID",
            plugin_Draw=True,
            Draw_export=True,
            locate_control=True,
            plugin_LatLngPopup=False,
        )
        m.add_basemap("ROADMAP")

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
                m.set_center(lng, lat, 12)
                st.session_state["zoom_level"] = 12

       



        add_outline = st.checkbox(
            "Overlay an administrative boundary on timelapse", False
        )

        if add_outline:

            with st.expander("Customize administrative boundary", True):

                overlay_options = {
                    "User-defined": None,
                    "Continents": "continents",
                    "Countries": "countries",
                    "US States": "us_states",
                    "China": "china",
                }

                overlay = st.selectbox(
                    "Select an administrative boundary:",
                    list(overlay_options.keys()),
                    index=2,
                )

                overlay_data = overlay_options[overlay]

                if overlay_data is None:
                    overlay_data = st.text_input(
                        "Enter an HTTP URL to a GeoJSON file or an ee.FeatureCollection asset id:",
                        "https://raw.githubusercontent.com/giswqs/geemap/master/examples/data/countries.geojson",
                    )

                overlay_color = st.color_picker(
                    "Select a color for the administrative boundary:", "#000000"
                )
                overlay_width = st.slider(
                    "Select a line width for the administrative boundary:", 1, 20, 1
                )
                overlay_opacity = st.slider(
                    "Select an opacity for the administrative boundary:",
                    0.0,
                    1.0,
                    1.0,
                    0.05,
                )
        else:
            overlay_data = None
            overlay_color = "black"
            overlay_width = 1
            overlay_opacity = 1

    with row1_col1:

        with st.expander(
            "Steps: Draw a rectangle on the map -> Export it as a GeoJSON -> Upload it back to the app -> Click the Submit button. Expand this tab to see a demo 👉"
        ):
            video_empty = st.empty()

        data = st.file_uploader(
            "Upload a GeoJSON file to use as an ROI. Customize timelapse parameters and then click the Submit button 😇👇",
            type=["geojson", "kml", "zip"],
        )

        crs = "epsg:2100"
       
        gdf = uploaded_file_to_gdf(data)
        st.session_state["roi"] = geemap.geopandas_to_ee(gdf, geodesic=False)
        m.add_gdf(gdf, "ROI")

#         gdf_2 = uploaded_file_to_gdf(data)

#         gdf_geom = geemap.geopandas_to_ee(gdf_2)
        
#         #st.session_state["roi split"]=  
#         split =geemap.fishnet(gdf_geom, rows=10, cols=10, delta=1)
#         st.session_state["roi split"]=  split
#         #m.add_gdf(split, "ROI  split")
#         m.addLayer(split, {}, 'ROI Fishnet')
#         m.to_streamlit(height=600)

        #m.to_streamlit(height=600)


        
app()
