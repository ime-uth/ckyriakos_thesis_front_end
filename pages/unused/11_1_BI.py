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

goes_rois = {
    "Creek Fire, CA (2020-09-05)": {
        "region": Polygon(
            [
                [-121.003418, 36.848857],
                [-121.003418, 39.049052],
                [-117.905273, 39.049052],
                [-117.905273, 36.848857],
                [-121.003418, 36.848857],
            ]
        ),
        "start_time": "2020-09-05T15:00:00",
        "end_time": "2020-09-06T02:00:00",
    },
    "Bomb Cyclone (2021-10-24)": {
        "region": Polygon(
            [
                [-159.5954, 60.4088],
                [-159.5954, 24.5178],
                [-114.2438, 24.5178],
                [-114.2438, 60.4088],
            ]
        ),
        "start_time": "2021-10-24T14:00:00",
        "end_time": "2021-10-25T01:00:00",
    },
    "Hunga Tonga Volcanic Eruption (2022-01-15)": {
        "region": Polygon(
            [
                [-192.480469, -32.546813],
                [-192.480469, -8.754795],
                [-157.587891, -8.754795],
                [-157.587891, -32.546813],
                [-192.480469, -32.546813],
            ]
        ),
        "start_time": "2022-01-15T03:00:00",
        "end_time": "2022-01-15T07:00:00",
    },
    "Hunga Tonga Volcanic Eruption Closer Look (2022-01-15)": {
        "region": Polygon(
            [
                [-178.901367, -22.958393],
                [-178.901367, -17.85329],
                [-171.452637, -17.85329],
                [-171.452637, -22.958393],
                [-178.901367, -22.958393],
            ]
        ),
        "start_time": "2022-01-15T03:00:00",
        "end_time": "2022-01-15T07:00:00",
    },
}


landsat_rois = {
    "Aral Sea": Polygon(
        [
            [57.667236, 43.834527],
            [57.667236, 45.996962],
            [61.12793, 45.996962],
            [61.12793, 43.834527],
            [57.667236, 43.834527],
        ]
    ),
    "Dubai": Polygon(
        [
            [54.541626, 24.763044],
            [54.541626, 25.427152],
            [55.632019, 25.427152],
            [55.632019, 24.763044],
            [54.541626, 24.763044],
        ]
    ),
    "Hong Kong International Airport": Polygon(
        [
            [113.825226, 22.198849],
            [113.825226, 22.349758],
            [114.085121, 22.349758],
            [114.085121, 22.198849],
            [113.825226, 22.198849],
        ]
    ),
    "Las Vegas, NV": Polygon(
        [
            [-115.554199, 35.804449],
            [-115.554199, 36.558188],
            [-113.903503, 36.558188],
            [-113.903503, 35.804449],
            [-115.554199, 35.804449],
        ]
    ),
    "Pucallpa, Peru": Polygon(
        [
            [-74.672699, -8.600032],
            [-74.672699, -8.254983],
            [-74.279938, -8.254983],
            [-74.279938, -8.600032],
        ]
    ),
    "Sierra Gorda, Chile": Polygon(
        [
            [-69.315491, -22.837104],
            [-69.315491, -22.751488],
            [-69.190006, -22.751488],
            [-69.190006, -22.837104],
            [-69.315491, -22.837104],
        ]
    ),
}

modis_rois = {
    "World": Polygon(
        [
            [-171.210938, -57.136239],
            [-171.210938, 79.997168],
            [177.539063, 79.997168],
            [177.539063, -57.136239],
            [-171.210938, -57.136239],
        ]
    ),
    "Africa": Polygon(
        [
            [-18.6983, 38.1446],
            [-18.6983, -36.1630],
            [52.2293, -36.1630],
            [52.2293, 38.1446],
        ]
    ),
    "USA": Polygon(
        [
            [-127.177734, 23.725012],
            [-127.177734, 50.792047],
            [-66.269531, 50.792047],
            [-66.269531, 23.725012],
            [-127.177734, 23.725012],
        ]
    ),
}

ocean_rois = {
    "Gulf of Mexico": Polygon(
        [
            [-101.206055, 15.496032],
            [-101.206055, 32.361403],
            [-75.673828, 32.361403],
            [-75.673828, 15.496032],
            [-101.206055, 15.496032],
        ]
    ),
    "North Atlantic Ocean": Polygon(
        [
            [-85.341797, 24.046464],
            [-85.341797, 45.02695],
            [-55.810547, 45.02695],
            [-55.810547, 24.046464],
            [-85.341797, 24.046464],
        ]
    ),
    "World": Polygon(
        [
            [-171.210938, -57.136239],
            [-171.210938, 79.997168],
            [177.539063, 79.997168],
            [177.539063, -57.136239],
            [-171.210938, -57.136239],
        ]
    ),
}

#### Function that enables the use of a geojson as ROI.
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

        collection = st.selectbox(
            "Select a satellite image collection: ",
            [
                "Any Earth Engine ImageCollection",
                "Landsat TM-ETM-OLI Surface Reflectance",
                "Sentinel-2 MSI Surface Reflectance",
               # "Geostationary Operational Environmental Satellites (GOES)",
               # "MODIS Vegetation Indices (NDVI/EVI) 16-Day Global 1km",
               # "MODIS Gap filled Land Surface Temperature Daily",
               # "MODIS Ocean Color SMI",
               # "USDA National Agriculture Imagery Program (NAIP)",
            ],
            index=1,
        )
        # checks for the dataset that the user selected
        if collection in [
            "Landsat TM-ETM-OLI Surface Reflectance",
            "Sentinel-2 MSI Surface Reflectance",
        ]:
            roi_options = ["Uploaded GeoJSON"] + list(landsat_rois.keys())

        elif collection == "Geostationary Operational Environmental Satellites (GOES)":
            roi_options = ["Uploaded GeoJSON"] + list(goes_rois.keys())

        elif collection in [
            "MODIS Vegetation Indices (NDVI/EVI) 16-Day Global 1km",
            "MODIS Gap filled Land Surface Temperature Daily",
        ]:
            roi_options = ["Uploaded GeoJSON"] + list(modis_rois.keys())
        elif collection == "MODIS Ocean Color SMI":
            roi_options = ["Uploaded GeoJSON"] + list(ocean_rois.keys())
        else:
            roi_options = ["Uploaded GeoJSON"]

        if collection == "Any Earth Engine ImageCollection":
            keyword = st.text_input("Enter a keyword to search (e.g., MODIS):", "")
            if keyword:

                assets = geemap.search_ee_data(keyword)
                ee_assets = []
                for asset in assets:
                    if asset["ee_id_snippet"].startswith("ee.ImageCollection"):
                        ee_assets.append(asset)

                asset_titles = [x["title"] for x in ee_assets]
                dataset = st.selectbox("Select a dataset:", asset_titles)
                if len(ee_assets) > 0:
                    st.session_state["ee_assets"] = ee_assets
                    st.session_state["asset_titles"] = asset_titles
                    index = asset_titles.index(dataset)
                    ee_id = ee_assets[index]["id"]
                else:
                    ee_id = ""

                if dataset is not None:
                    with st.expander("Show dataset details", False):
                        index = asset_titles.index(dataset)
                        html = geemap.ee_data_html(st.session_state["ee_assets"][index])
                        st.markdown(html, True)
            # elif collection == "MODIS Gap filled Land Surface Temperature Daily":
            #     ee_id = ""
            else:
                ee_id = ""

            asset_id = st.text_input("Enter an ee.ImageCollection asset ID:", ee_id)

            if asset_id:
                with st.expander("Customize band combination and color palette", True):
                    try:
                        col = ee.ImageCollection.load(asset_id)
                        st.session_state["ee_asset_id"] = asset_id
                    except:
                        st.error("Invalid Earth Engine asset ID.")
                        st.session_state["ee_asset_id"] = None
                        return

                    img_bands = col.first().bandNames().getInfo()
                    if len(img_bands) >= 3:
                        default_bands = img_bands[:3][::-1]
                    else:
                        default_bands = img_bands[:]
                    bands = st.multiselect(
                        "Select one or three bands (RGB):", img_bands, default_bands
                    )
                    st.session_state["bands"] = bands

                    if len(bands) == 1:
                        palette_options = st.selectbox(
                            "Color palette",
                            cm.list_colormaps(),
                            index=2,
                        )
                        palette_values = cm.get_palette(palette_options, 15)
                        palette = st.text_area(
                            "Enter a custom palette:",
                            palette_values,
                        )
                        st.write(
                            cm.plot_colormap(cmap=palette_options, return_fig=True)
                        )
                        st.session_state["palette"] = eval(palette)

                    if bands:
                        vis_params = st.text_area(
                            "Enter visualization parameters",
                            "{'bands': ["
                            + ", ".join([f"'{band}'" for band in bands])
                            + "]}",
                        )
                    else:
                        vis_params = st.text_area(
                            "Enter visualization parameters",
                            "{}",
                        )
                    try:
                        st.session_state["vis_params"] = eval(vis_params)
                        st.session_state["vis_params"]["palette"] = st.session_state[
                            "palette"
                        ]
                    except Exception as e:
                        st.session_state["vis_params"] = None
                        st.error(
                            f"Invalid visualization parameters. It must be a dictionary."
                        )

        elif collection == "MODIS Gap filled Land Surface Temperature Daily":
            with st.expander("Show dataset details", False):
                st.markdown(
                    """
                See the [Awesome GEE Community Datasets](https://samapriya.github.io/awesome-gee-community-datasets/projects/daily_lst/).
                """
                )

            MODIS_options = ["Daytime (1:30 pm)", "Nighttime (1:30 am)"]
            MODIS_option = st.selectbox("Select a MODIS dataset:", MODIS_options)
            if MODIS_option == "Daytime (1:30 pm)":
                st.session_state[
                    "ee_asset_id"
                ] = "projects/sat-io/open-datasets/gap-filled-lst/gf_day_1km"
            else:
                st.session_state[
                    "ee_asset_id"
                ] = "projects/sat-io/open-datasets/gap-filled-lst/gf_night_1km"

            palette_options = st.selectbox(
                "Color palette",
                cm.list_colormaps(),
                index=90,
            )
            palette_values = cm.get_palette(palette_options, 15)
            palette = st.text_area(
                "Enter a custom palette:",
                palette_values,
            )
            st.write(cm.plot_colormap(cmap=palette_options, return_fig=True))
            st.session_state["palette"] = eval(palette)
        elif collection == "MODIS Ocean Color SMI":
            with st.expander("Show dataset details", False):
                st.markdown(
                    """
                See the [Earth Engine Data Catalog](https://developers.google.com/earth-engine/datasets/catalog/NASA_OCEANDATA_MODIS-Aqua_L3SMI).
                """
                )

            MODIS_options = ["Aqua", "Terra"]
            MODIS_option = st.selectbox("Select a satellite:", MODIS_options)
            st.session_state["ee_asset_id"] = MODIS_option
            # if MODIS_option == "Daytime (1:30 pm)":
            #     st.session_state[
            #         "ee_asset_id"
            #     ] = "projects/sat-io/open-datasets/gap-filled-lst/gf_day_1km"
            # else:
            #     st.session_state[
            #         "ee_asset_id"
            #     ] = "projects/sat-io/open-datasets/gap-filled-lst/gf_night_1km"

            band_dict = {
                "Chlorophyll a concentration": "chlor_a",
                "Normalized fluorescence line height": "nflh",
                "Particulate organic carbon": "poc",
                "Sea surface temperature": "sst",
                "Remote sensing reflectance at band 412nm": "Rrs_412",
                "Remote sensing reflectance at band 443nm": "Rrs_443",
                "Remote sensing reflectance at band 469nm": "Rrs_469",
                "Remote sensing reflectance at band 488nm": "Rrs_488",
                "Remote sensing reflectance at band 531nm": "Rrs_531",
                "Remote sensing reflectance at band 547nm": "Rrs_547",
                "Remote sensing reflectance at band 555nm": "Rrs_555",
                "Remote sensing reflectance at band 645nm": "Rrs_645",
                "Remote sensing reflectance at band 667nm": "Rrs_667",
                "Remote sensing reflectance at band 678nm": "Rrs_678",
            }

            band_options = list(band_dict.keys())
            band = st.selectbox(
                "Select a band",
                band_options,
                band_options.index("Sea surface temperature"),
            )
            st.session_state["band"] = band_dict[band]

            colors = cm.list_colormaps()
            palette_options = st.selectbox(
                "Color palette",
                colors,
                index=colors.index("coolwarm"),
            )
            palette_values = cm.get_palette(palette_options, 15)
            palette = st.text_area(
                "Enter a custom palette:",
                palette_values,
            )
            st.write(cm.plot_colormap(cmap=palette_options, return_fig=True))
            st.session_state["palette"] = eval(palette)

        sample_roi = st.selectbox(
            "Select a sample ROI or upload a GeoJSON file:",
            roi_options,
            index=0,
        )

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

        crs = "epsg:4326"
        if sample_roi == "Uploaded GeoJSON":
            if data is None:
                # st.info(
                #     "Steps to create a timelapse: Draw a rectangle on the map -> Export it as a GeoJSON -> Upload it back to the app -> Click Submit button"
                # )
                if collection in [
                    "Geostationary Operational Environmental Satellites (GOES)",
                    "USDA National Agriculture Imagery Program (NAIP)",
                ] and (not keyword):
                    m.set_center(-100, 40, 3)
                # else:
                #     m.set_center(4.20, 18.63, zoom=2)
        else:
            if collection in [
                "Landsat TM-ETM-OLI Surface Reflectance",
                "Sentinel-2 MSI Surface Reflectance",
            ]:
                gdf = gpd.GeoDataFrame(
                    index=[0], crs=crs, geometry=[landsat_rois[sample_roi]]
                )
            elif (
                collection
                == "Geostationary Operational Environmental Satellites (GOES)"
            ):
                gdf = gpd.GeoDataFrame(
                    index=[0], crs=crs, geometry=[goes_rois[sample_roi]["region"]]
                )
            elif collection == "MODIS Vegetation Indices (NDVI/EVI) 16-Day Global 1km":
                gdf = gpd.GeoDataFrame(
                    index=[0], crs=crs, geometry=[modis_rois[sample_roi]]
                )

        if sample_roi != "Uploaded GeoJSON":

            if collection in [
                "Landsat TM-ETM-OLI Surface Reflectance",
                "Sentinel-2 MSI Surface Reflectance",
            ]:
                gdf = gpd.GeoDataFrame(
                    index=[0], crs=crs, geometry=[landsat_rois[sample_roi]]
                )
            elif (
                collection
                == "Geostationary Operational Environmental Satellites (GOES)"
            ):
                gdf = gpd.GeoDataFrame(
                    index=[0], crs=crs, geometry=[goes_rois[sample_roi]["region"]]
                )
            elif collection in [
                "MODIS Vegetation Indices (NDVI/EVI) 16-Day Global 1km",
                "MODIS Gap filled Land Surface Temperature Daily",
            ]:
                gdf = gpd.GeoDataFrame(
                    index=[0], crs=crs, geometry=[modis_rois[sample_roi]]
                )
            elif collection == "MODIS Ocean Color SMI":
                gdf = gpd.GeoDataFrame(
                    index=[0], crs=crs, geometry=[ocean_rois[sample_roi]]
                )
            st.session_state["roi"] = geemap.geopandas_to_ee(gdf, geodesic=False)
            m.add_gdf(gdf, "ROI")

        elif data:
            gdf = uploaded_file_to_gdf(data)
            st.session_state["roi"] = geemap.geopandas_to_ee(gdf, geodesic=False)
            m.add_gdf(gdf, "ROI")

        m.to_streamlit(height=600)

    with row1_col2:

        if collection in [
            "Landsat TM-ETM-OLI Surface Reflectance",
            "Sentinel-2 MSI Surface Reflectance",
        ]:

            if collection == "Landsat TM-ETM-OLI Surface Reflectance":
                sensor_start_year = 1984
                timelapse_title = "Landsat Timelapse"
                timelapse_speed = 5
            elif collection == "Sentinel-2 MSI Surface Reflectance":
                sensor_start_year = 2015
                timelapse_title = "Sentinel-2 Timelapse"
                timelapse_speed = 5
            video_empty.video("https://youtu.be/VVRK_-dEjR4")

            with st.form("submit_landsat_form"):

                roi = None
                if st.session_state.get("roi") is not None:
                    roi = st.session_state.get("roi")
                out_gif = geemap.temp_file_path(".gif")

                title = st.text_input(
                    "Enter a title to show on the timelapse: ", timelapse_title
                )
                RGB = st.selectbox(
                    "Select an RGB band combination:",
                    [
                        "Red/Green/Blue",
                        "NIR/Red/Green",
                        "SWIR2/SWIR1/NIR",
                        "NIR/SWIR1/Red",
                        "SWIR2/NIR/Red",
                        "SWIR2/SWIR1/Red",
                        "SWIR1/NIR/Blue",
                        "NIR/SWIR1/Blue",
                        "SWIR2/NIR/Green",
                        "SWIR1/NIR/Red",
                        "SWIR2/NIR/SWIR1",
                        "SWIR1/NIR/SWIR2",
                    ],
                    index=9,
                )

                frequency = st.selectbox(
                    "Select a temporal frequency:",
                    ["year", "quarter", "month"],
                    index=0,
                )

                with st.expander("Customize timelapse"):

                    speed = st.slider("Frames per second:", 1, 30, timelapse_speed)
                    dimensions = st.slider(
                        "Maximum dimensions (Width*Height) in pixels", 768, 2000, 768
                    )
                    progress_bar_color = st.color_picker(
                        "Progress bar color:", "#0000ff"
                    )
                    years = st.slider(
                        "Start and end year:",
                        sensor_start_year,
                        today.year,
                        (sensor_start_year, today.year),
                    )
                    months = st.slider("Start and end month:", 1, 12, (1, 12))
                    font_size = st.slider("Font size:", 10, 50, 30)
                    font_color = st.color_picker("Font color:", "#ffffff")
                    apply_fmask = st.checkbox(
                        "Apply fmask (remove clouds, shadows, snow)", True
                    )
                    font_type = st.selectbox(
                        "Select the font type for the title:",
                        ["arial.ttf", "alibaba.otf"],
                        index=0,
                    )
                    fading = st.slider(
                        "Fading duration (seconds) for each frame:", 0.0, 3.0, 0.0
                    )
                    mp4 = st.checkbox("Save timelapse as MP4", True)

                empty_text = st.empty()
                empty_image = st.empty()
                empty_fire_image = st.empty()
                empty_video = st.container()
                submitted = st.form_submit_button("Submit")
                if submitted:

                    if sample_roi == "Uploaded GeoJSON" and data is None:
                        empty_text.warning(
                            "Steps to create a timelapse: Draw a rectangle on the map -> Export it as a GeoJSON -> Upload it back to the app -> Click the Submit button. Alternatively, you can select a sample ROI from the dropdown list."
                        )
                    else:

                        empty_text.text("Computing... Please wait...")

                        start_year = years[0]
                        end_year = years[1]
                        start_date = str(months[0]).zfill(2) + "-01"
                        end_date = str(months[1]).zfill(2) + "-30"
                        bands = RGB.split("/")

                        try:
                            if collection == "Landsat TM-ETM-OLI Surface Reflectance":
                                out_gif = geemap.landsat_timelapse(
                                    roi=roi,
                                    out_gif=out_gif,
                                    start_year=start_year,
                                    end_year=end_year,
                                    start_date=start_date,
                                    end_date=end_date,
                                    bands=bands,
                                    apply_fmask=apply_fmask,
                                    frames_per_second=speed,
                                    dimensions=dimensions,
                                    overlay_data=overlay_data,
                                    overlay_color=overlay_color,
                                    overlay_width=overlay_width,
                                    overlay_opacity=overlay_opacity,
                                    frequency=frequency,
                                    date_format=None,
                                    title=title,
                                    title_xy=("2%", "90%"),
                                    add_text=True,
                                    text_xy=("2%", "2%"),
                                    text_sequence=None,
                                    font_type=font_type,
                                    font_size=font_size,
                                    font_color=font_color,
                                    add_progress_bar=True,
                                    progress_bar_color=progress_bar_color,
                                    progress_bar_height=5,
                                    loop=0,
                                    mp4=mp4,
                                    fading=fading,
                                )
                            elif collection == "Sentinel-2 MSI Surface Reflectance":
                                out_gif = geemap.sentinel2_timelapse(
                                    roi=roi,
                                    out_gif=out_gif,
                                    start_year=start_year,
                                    end_year=end_year,
                                    start_date=start_date,
                                    end_date=end_date,
                                    bands=bands,
                                    apply_fmask=apply_fmask,
                                    frames_per_second=speed,
                                    dimensions=dimensions,
                                    overlay_data=overlay_data,
                                    overlay_color=overlay_color,
                                    overlay_width=overlay_width,
                                    overlay_opacity=overlay_opacity,
                                    frequency=frequency,
                                    date_format=None,
                                    title=title,
                                    title_xy=("2%", "90%"),
                                    add_text=True,
                                    text_xy=("2%", "2%"),
                                    text_sequence=None,
                                    font_type=font_type,
                                    font_size=font_size,
                                    font_color=font_color,
                                    add_progress_bar=True,
                                    progress_bar_color=progress_bar_color,
                                    progress_bar_height=5,
                                    loop=0,
                                    mp4=mp4,
                                    fading=fading,
                                )
                        except:
                            empty_text.error(
                                "An error occurred while computing the timelapse. Your probably requested too much data. Try reducing the ROI or timespan."
                            )
                            st.stop()

                        if out_gif is not None and os.path.exists(out_gif):

                            empty_text.text(
                                "Right click the GIF to save it to your computer👇"
                            )
                            empty_image.image(out_gif)

                            out_mp4 = out_gif.replace(".gif", ".mp4")
                            if mp4 and os.path.exists(out_mp4):
                                with empty_video:
                                    st.text(
                                        "Right click the MP4 to save it to your computer👇"
                                    )
                                    st.video(out_gif.replace(".gif", ".mp4"))

                        else:
                            empty_text.error(
                                "Something went wrong. You probably requested too much data. Try reducing the ROI or timespan."
                            )

        elif collection == "Geostationary Operational Environmental Satellites (GOES)":

            video_empty.video("https://youtu.be/16fA2QORG4A")

            with st.form("submit_goes_form"):

                roi = None
                if st.session_state.get("roi") is not None:
                    roi = st.session_state.get("roi")
                out_gif = geemap.temp_file_path(".gif")

                satellite = st.selectbox("Select a satellite:", ["GOES-17", "GOES-16"])
                earliest_date = datetime.date(2017, 7, 10)
                latest_date = datetime.date.today()

                if sample_roi == "Uploaded GeoJSON":
                    roi_start_date = today - datetime.timedelta(days=2)
                    roi_end_date = today - datetime.timedelta(days=1)
                    roi_start_time = datetime.time(14, 00)
                    roi_end_time = datetime.time(1, 00)
                else:
                    roi_start = goes_rois[sample_roi]["start_time"]
                    roi_end = goes_rois[sample_roi]["end_time"]
                    roi_start_date = datetime.datetime.strptime(
                        roi_start[:10], "%Y-%m-%d"
                    )
                    roi_end_date = datetime.datetime.strptime(roi_end[:10], "%Y-%m-%d")
                    roi_start_time = datetime.time(
                        int(roi_start[11:13]), int(roi_start[14:16])
                    )
                    roi_end_time = datetime.time(
                        int(roi_end[11:13]), int(roi_end[14:16])
                    )

                start_date = st.date_input("Select the start date:", roi_start_date)
                end_date = st.date_input("Select the end date:", roi_end_date)

                with st.expander("Customize timelapse"):

                    add_fire = st.checkbox("Add Fire/Hotspot Characterization", False)

                    scan_type = st.selectbox(
                        "Select a scan type:", ["Full Disk", "CONUS", "Mesoscale"]
                    )

                    start_time = st.time_input(
                        "Select the start time of the start date:", roi_start_time
                    )

                    end_time = st.time_input(
                        "Select the end time of the end date:", roi_end_time
                    )

                    start = (
                        start_date.strftime("%Y-%m-%d")
                        + "T"
                        + start_time.strftime("%H:%M:%S")
                    )
                    end = (
                        end_date.strftime("%Y-%m-%d")
                        + "T"
                        + end_time.strftime("%H:%M:%S")
                    )

                    speed = st.slider("Frames per second:", 1, 30, 5)
                    add_progress_bar = st.checkbox("Add a progress bar", True)
                    progress_bar_color = st.color_picker(
                        "Progress bar color:", "#0000ff"
                    )
                    font_size = st.slider("Font size:", 10, 50, 20)
                    font_color = st.color_picker("Font color:", "#ffffff")
                    fading = st.slider(
                        "Fading duration (seconds) for each frame:", 0.0, 3.0, 0.0
                    )
                    mp4 = st.checkbox("Save timelapse as MP4", True)

                empty_text = st.empty()
                empty_image = st.empty()
                empty_video = st.container()
                empty_fire_text = st.empty()
                empty_fire_image = st.empty()

                submitted = st.form_submit_button("Submit")
                if submitted:
                    if sample_roi == "Uploaded GeoJSON" and data is None:
                        empty_text.warning(
                            "Steps to create a timelapse: Draw a rectangle on the map -> Export it as a GeoJSON -> Upload it back to the app -> Click the Submit button. Alternatively, you can select a sample ROI from the dropdown list."
                        )
                    else:
                        empty_text.text("Computing... Please wait...")

                        geemap.goes_timelapse(
                            out_gif,
                            start_date=start,
                            end_date=end,
                            data=satellite,
                            scan=scan_type.replace(" ", "_").lower(),
                            region=roi,
                            dimensions=768,
                            framesPerSecond=speed,
                            date_format="YYYY-MM-dd HH:mm",
                            xy=("3%", "3%"),
                            text_sequence=None,
                            font_type="arial.ttf",
                            font_size=font_size,
                            font_color=font_color,
                            add_progress_bar=add_progress_bar,
                            progress_bar_color=progress_bar_color,
                            progress_bar_height=5,
                            loop=0,
                            overlay_data=overlay_data,
                            overlay_color=overlay_color,
                            overlay_width=overlay_width,
                            overlay_opacity=overlay_opacity,
                            mp4=mp4,
                            fading=fading,
                        )

                        if out_gif is not None and os.path.exists(out_gif):
                            empty_text.text(
                                "Right click the GIF to save it to your computer👇"
                            )
                            empty_image.image(out_gif)

                            out_mp4 = out_gif.replace(".gif", ".mp4")
                            if mp4 and os.path.exists(out_mp4):
                                with empty_video:
                                    st.text(
                                        "Right click the MP4 to save it to your computer👇"
                                    )
                                    st.video(out_gif.replace(".gif", ".mp4"))

                            if add_fire:
                                out_fire_gif = geemap.temp_file_path(".gif")
                                empty_fire_text.text(
                                    "Delineating Fire Hotspot... Please wait..."
                                )
                                geemap.goes_fire_timelapse(
                                    out_fire_gif,
                                    start_date=start,
                                    end_date=end,
                                    data=satellite,
                                    scan=scan_type.replace(" ", "_").lower(),
                                    region=roi,
                                    dimensions=768,
                                    framesPerSecond=speed,
                                    date_format="YYYY-MM-dd HH:mm",
                                    xy=("3%", "3%"),
                                    text_sequence=None,
                                    font_type="arial.ttf",
                                    font_size=font_size,
                                    font_color=font_color,
                                    add_progress_bar=add_progress_bar,
                                    progress_bar_color=progress_bar_color,
                                    progress_bar_height=5,
                                    loop=0,
                                )
                                if os.path.exists(out_fire_gif):
                                    empty_fire_image.image(out_fire_gif)
                        else:
                            empty_text.text(
                                "Something went wrong, either the ROI is too big or there are no data available for the specified date range. Please try a smaller ROI or different date range."
                            )

        elif collection == "MODIS Vegetation Indices (NDVI/EVI) 16-Day Global 1km":

            video_empty.video("https://youtu.be/16fA2QORG4A")

            satellite = st.selectbox("Select a satellite:", ["Terra", "Aqua"])
            band = st.selectbox("Select a band:", ["NDVI", "EVI"])

            with st.form("submit_modis_form"):

                roi = None
                if st.session_state.get("roi") is not None:
                    roi = st.session_state.get("roi")
                out_gif = geemap.temp_file_path(".gif")

                with st.expander("Customize timelapse"):

                    start = st.date_input(
                        "Select a start date:", datetime.date(2000, 2, 8)
                    )
                    end = st.date_input("Select an end date:", datetime.date.today())

                    start_date = start.strftime("%Y-%m-%d")
                    end_date = end.strftime("%Y-%m-%d")

                    speed = st.slider("Frames per second:", 1, 30, 5)
                    add_progress_bar = st.checkbox("Add a progress bar", True)
                    progress_bar_color = st.color_picker(
                        "Progress bar color:", "#0000ff"
                    )
                    font_size = st.slider("Font size:", 10, 50, 20)
                    font_color = st.color_picker("Font color:", "#ffffff")

                    font_type = st.selectbox(
                        "Select the font type for the title:",
                        ["arial.ttf", "alibaba.otf"],
                        index=0,
                    )
                    fading = st.slider(
                        "Fading duration (seconds) for each frame:", 0.0, 3.0, 0.0
                    )
                    mp4 = st.checkbox("Save timelapse as MP4", True)

                empty_text = st.empty()
                empty_image = st.empty()
                empty_video = st.container()

                submitted = st.form_submit_button("Submit")
                if submitted:
                    if sample_roi == "Uploaded GeoJSON" and data is None:
                        empty_text.warning(
                            "Steps to create a timelapse: Draw a rectangle on the map -> Export it as a GeoJSON -> Upload it back to the app -> Click the Submit button. Alternatively, you can select a sample ROI from the dropdown list."
                        )
                    else:

                        empty_text.text("Computing... Please wait...")

                        geemap.modis_ndvi_timelapse(
                            out_gif,
                            satellite,
                            band,
                            start_date,
                            end_date,
                            roi,
                            768,
                            speed,
                            overlay_data=overlay_data,
                            overlay_color=overlay_color,
                            overlay_width=overlay_width,
                            overlay_opacity=overlay_opacity,
                            mp4=mp4,
                            fading=fading,
                        )

                        geemap.reduce_gif_size(out_gif)

                        empty_text.text(
                            "Right click the GIF to save it to your computer👇"
                        )
                        empty_image.image(out_gif)

                        out_mp4 = out_gif.replace(".gif", ".mp4")
                        if mp4 and os.path.exists(out_mp4):
                            with empty_video:
                                st.text(
                                    "Right click the MP4 to save it to your computer👇"
                                )
                                st.video(out_gif.replace(".gif", ".mp4"))

        elif collection == "Any Earth Engine ImageCollection":

            with st.form("submit_ts_form"):
                with st.expander("Customize timelapse"):

                    title = st.text_input(
                        "Enter a title to show on the timelapse: ", "Timelapse"
                    )
                    start_date = st.date_input(
                        "Select the start date:", datetime.date(2020, 1, 1)
                    )
                    end_date = st.date_input(
                        "Select the end date:", datetime.date.today()
                    )
                    frequency = st.selectbox(
                        "Select a temporal frequency:",
                        ["year", "quarter", "month", "day", "hour", "minute", "second"],
                        index=0,
                    )
                    reducer = st.selectbox(
                        "Select a reducer for aggregating data:",
                        ["median", "mean", "min", "max", "sum", "variance", "stdDev"],
                        index=0,
                    )
                    data_format = st.selectbox(
                        "Select a date format to show on the timelapse:",
                        [
                            "YYYY-MM-dd",
                            "YYYY",
                            "YYMM-MM",
                            "YYYY-MM-dd HH:mm",
                            "YYYY-MM-dd HH:mm:ss",
                            "HH:mm",
                            "HH:mm:ss",
                            "w",
                            "M",
                            "d",
                            "D",
                        ],
                        index=0,
                    )

                    speed = st.slider("Frames per second:", 1, 30, 5)
                    add_progress_bar = st.checkbox("Add a progress bar", True)
                    progress_bar_color = st.color_picker(
                        "Progress bar color:", "#0000ff"
                    )
                    font_size = st.slider("Font size:", 10, 50, 30)
                    font_color = st.color_picker("Font color:", "#ffffff")
                    font_type = st.selectbox(
                        "Select the font type for the title:",
                        ["arial.ttf", "alibaba.otf"],
                        index=0,
                    )
                    fading = st.slider(
                        "Fading duration (seconds) for each frame:", 0.0, 3.0, 0.0
                    )
                    mp4 = st.checkbox("Save timelapse as MP4", True)

                empty_text = st.empty()
                empty_image = st.empty()
                empty_video = st.container()
                empty_fire_image = st.empty()

                roi = None
                if st.session_state.get("roi") is not None:
                    roi = st.session_state.get("roi")
                out_gif = geemap.temp_file_path(".gif")

                submitted = st.form_submit_button("Submit")
                if submitted:

                    if sample_roi == "Uploaded GeoJSON" and data is None:
                        empty_text.warning(
                            "Steps to create a timelapse: Draw a rectangle on the map -> Export it as a GeoJSON -> Upload it back to the app -> Click the Submit button. Alternatively, you can select a sample ROI from the dropdown list."
                        )
                    else:

                        empty_text.text("Computing... Please wait...")
                        try:
                            geemap.create_timelapse(
                                st.session_state.get("ee_asset_id"),
                                start_date=start_date.strftime("%Y-%m-%d"),
                                end_date=end_date.strftime("%Y-%m-%d"),
                                region=roi,
                                frequency=frequency,
                                reducer=reducer,
                                date_format=data_format,
                                out_gif=out_gif,
                                bands=st.session_state.get("bands"),
                                palette=st.session_state.get("palette"),
                                vis_params=st.session_state.get("vis_params"),
                                dimensions=768,
                                frames_per_second=speed,
                                crs="EPSG:3857",
                                overlay_data=overlay_data,
                                overlay_color=overlay_color,
                                overlay_width=overlay_width,
                                overlay_opacity=overlay_opacity,
                                title=title,
                                title_xy=("2%", "90%"),
                                add_text=True,
                                text_xy=("2%", "2%"),
                                text_sequence=None,
                                font_type=font_type,
                                font_size=font_size,
                                font_color=font_color,
                                add_progress_bar=add_progress_bar,
                                progress_bar_color=progress_bar_color,
                                progress_bar_height=5,
                                loop=0,
                                mp4=mp4,
                                fading=fading,
                            )
                        except:
                            empty_text.error(
                                "An error occurred while computing the timelapse. You probably requested too much data. Try reducing the ROI or timespan."
                            )

                        empty_text.text(
                            "Right click the GIF to save it to your computer👇"
                        )
                        empty_image.image(out_gif)

                        out_mp4 = out_gif.replace(".gif", ".mp4")
                        if mp4 and os.path.exists(out_mp4):
                            with empty_video:
                                st.text(
                                    "Right click the MP4 to save it to your computer👇"
                                )
                                st.video(out_gif.replace(".gif", ".mp4"))

        elif collection in [
            "MODIS Gap filled Land Surface Temperature Daily",
            "MODIS Ocean Color SMI",
        ]:

            with st.form("submit_ts_form"):
                with st.expander("Customize timelapse"):

                    title = st.text_input(
                        "Enter a title to show on the timelapse: ",
                        "Surface Temperature",
                    )
                    start_date = st.date_input(
                        "Select the start date:", datetime.date(2018, 1, 1)
                    )
                    end_date = st.date_input(
                        "Select the end date:", datetime.date(2020, 12, 31)
                    )
                    frequency = st.selectbox(
                        "Select a temporal frequency:",
                        ["year", "quarter", "month", "week", "day"],
                        index=2,
                    )
                    reducer = st.selectbox(
                        "Select a reducer for aggregating data:",
                        ["median", "mean", "min", "max", "sum", "variance", "stdDev"],
                        index=0,
                    )

                    vis_params = st.text_area(
                        "Enter visualization parameters",
                        "",
                        help="Enter a string in the format of a dictionary, such as '{'min': 23, 'max': 32}'",
                    )

                    speed = st.slider("Frames per second:", 1, 30, 5)
                    add_progress_bar = st.checkbox("Add a progress bar", True)
                    progress_bar_color = st.color_picker(
                        "Progress bar color:", "#0000ff"
                    )
                    font_size = st.slider("Font size:", 10, 50, 30)
                    font_color = st.color_picker("Font color:", "#ffffff")
                    font_type = st.selectbox(
                        "Select the font type for the title:",
                        ["arial.ttf", "alibaba.otf"],
                        index=0,
                    )
                    add_colorbar = st.checkbox("Add a colorbar", True)
                    colorbar_label = st.text_input(
                        "Enter the colorbar label:", "Surface Temperature (°C)"
                    )
                    fading = st.slider(
                        "Fading duration (seconds) for each frame:", 0.0, 3.0, 0.0
                    )
                    mp4 = st.checkbox("Save timelapse as MP4", True)

                empty_text = st.empty()
                empty_image = st.empty()
                empty_video = st.container()

                roi = None
                if st.session_state.get("roi") is not None:
                    roi = st.session_state.get("roi")
                out_gif = geemap.temp_file_path(".gif")

                submitted = st.form_submit_button("Submit")
                if submitted:

                    if sample_roi == "Uploaded GeoJSON" and data is None:
                        empty_text.warning(
                            "Steps to create a timelapse: Draw a rectangle on the map -> Export it as a GeoJSON -> Upload it back to the app -> Click the Submit button. Alternatively, you can select a sample ROI from the dropdown list."
                        )
                    else:

                        empty_text.text("Computing... Please wait...")
                        try:
                            if (
                                collection
                                == "MODIS Gap filled Land Surface Temperature Daily"
                            ):
                                out_gif = geemap.create_timelapse(
                                    st.session_state.get("ee_asset_id"),
                                    start_date=start_date.strftime("%Y-%m-%d"),
                                    end_date=end_date.strftime("%Y-%m-%d"),
                                    region=roi,
                                    bands=None,
                                    frequency=frequency,
                                    reducer=reducer,
                                    date_format=None,
                                    out_gif=out_gif,
                                    palette=st.session_state.get("palette"),
                                    vis_params=None,
                                    dimensions=768,
                                    frames_per_second=speed,
                                    crs="EPSG:3857",
                                    overlay_data=overlay_data,
                                    overlay_color=overlay_color,
                                    overlay_width=overlay_width,
                                    overlay_opacity=overlay_opacity,
                                    title=title,
                                    title_xy=("2%", "90%"),
                                    add_text=True,
                                    text_xy=("2%", "2%"),
                                    text_sequence=None,
                                    font_type=font_type,
                                    font_size=font_size,
                                    font_color=font_color,
                                    add_progress_bar=add_progress_bar,
                                    progress_bar_color=progress_bar_color,
                                    progress_bar_height=5,
                                    add_colorbar=add_colorbar,
                                    colorbar_label=colorbar_label,
                                    loop=0,
                                    mp4=mp4,
                                    fading=fading,
                                )
                            elif collection == "MODIS Ocean Color SMI":
                                if vis_params.startswith("{") and vis_params.endswith(
                                    "}"
                                ):
                                    vis_params = eval(vis_params)
                                else:
                                    vis_params = None
                                out_gif = geemap.modis_ocean_color_timelapse(
                                    st.session_state.get("ee_asset_id"),
                                    start_date=start_date.strftime("%Y-%m-%d"),
                                    end_date=end_date.strftime("%Y-%m-%d"),
                                    region=roi,
                                    bands=st.session_state["band"],
                                    frequency=frequency,
                                    reducer=reducer,
                                    date_format=None,
                                    out_gif=out_gif,
                                    palette=st.session_state.get("palette"),
                                    vis_params=vis_params,
                                    dimensions=768,
                                    frames_per_second=speed,
                                    crs="EPSG:3857",
                                    overlay_data=overlay_data,
                                    overlay_color=overlay_color,
                                    overlay_width=overlay_width,
                                    overlay_opacity=overlay_opacity,
                                    title=title,
                                    title_xy=("2%", "90%"),
                                    add_text=True,
                                    text_xy=("2%", "2%"),
                                    text_sequence=None,
                                    font_type=font_type,
                                    font_size=font_size,
                                    font_color=font_color,
                                    add_progress_bar=add_progress_bar,
                                    progress_bar_color=progress_bar_color,
                                    progress_bar_height=5,
                                    add_colorbar=add_colorbar,
                                    colorbar_label=colorbar_label,
                                    loop=0,
                                    mp4=mp4,
                                    fading=fading,
                                )
                        except:
                            empty_text.error(
                                "Something went wrong. You probably requested too much data. Try reducing the ROI or timespan."
                            )

                        if out_gif is not None and os.path.exists(out_gif):

                            geemap.reduce_gif_size(out_gif)

                            empty_text.text(
                                "Right click the GIF to save it to your computer👇"
                            )
                            empty_image.image(out_gif)

                            out_mp4 = out_gif.replace(".gif", ".mp4")
                            if mp4 and os.path.exists(out_mp4):
                                with empty_video:
                                    st.text(
                                        "Right click the MP4 to save it to your computer👇"
                                    )
                                    st.video(out_gif.replace(".gif", ".mp4"))

                        else:
                            st.error(
                                "Something went wrong. You probably requested too much data. Try reducing the ROI or timespan."
                            )

        elif collection == "USDA National Agriculture Imagery Program (NAIP)":

            with st.form("submit_naip_form"):
                with st.expander("Customize timelapse"):

                    title = st.text_input(
                        "Enter a title to show on the timelapse: ", "NAIP Timelapse"
                    )

                    years = st.slider(
                        "Start and end year:",
                        2003,
                        today.year,
                        (2003, today.year),
                    )

                    bands = st.selectbox(
                        "Select a band combination:", ["N/R/G", "R/G/B"], index=0
                    )

                    speed = st.slider("Frames per second:", 1, 30, 3)
                    add_progress_bar = st.checkbox("Add a progress bar", True)
                    progress_bar_color = st.color_picker(
                        "Progress bar color:", "#0000ff"
                    )
                    font_size = st.slider("Font size:", 10, 50, 30)
                    font_color = st.color_picker("Font color:", "#ffffff")
                    font_type = st.selectbox(
                        "Select the font type for the title:",
                        ["arial.ttf", "alibaba.otf"],
                        index=0,
                    )
                    fading = st.slider(
                        "Fading duration (seconds) for each frame:", 0.0, 3.0, 0.0
                    )
                    mp4 = st.checkbox("Save timelapse as MP4", True)

                empty_text = st.empty()
                empty_image = st.empty()
                empty_video = st.container()
                empty_fire_image = st.empty()

                roi = None
                if st.session_state.get("roi") is not None:
                    roi = st.session_state.get("roi")
                out_gif = geemap.temp_file_path(".gif")

                submitted = st.form_submit_button("Submit")
                if submitted:

                    if sample_roi == "Uploaded GeoJSON" and data is None:
                        empty_text.warning(
                            "Steps to create a timelapse: Draw a rectangle on the map -> Export it as a GeoJSON -> Upload it back to the app -> Click the Submit button. Alternatively, you can select a sample ROI from the dropdown list."
                        )
                    else:

                        empty_text.text("Computing... Please wait...")
                        try:
                            geemap.naip_timelapse(
                                roi,
                                years[0],
                                years[1],
                                out_gif,
                                bands=bands.split("/"),
                                palette=st.session_state.get("palette"),
                                vis_params=None,
                                dimensions=768,
                                frames_per_second=speed,
                                crs="EPSG:3857",
                                overlay_data=overlay_data,
                                overlay_color=overlay_color,
                                overlay_width=overlay_width,
                                overlay_opacity=overlay_opacity,
                                title=title,
                                title_xy=("2%", "90%"),
                                add_text=True,
                                text_xy=("2%", "2%"),
                                text_sequence=None,
                                font_type=font_type,
                                font_size=font_size,
                                font_color=font_color,
                                add_progress_bar=add_progress_bar,
                                progress_bar_color=progress_bar_color,
                                progress_bar_height=5,
                                loop=0,
                                mp4=mp4,
                                fading=fading,
                            )
                        except:
                            empty_text.error(
                                "Something went wrong. You either requested too much data or the ROI is outside the U.S."
                            )

                        if out_gif is not None and os.path.exists(out_gif):

                            empty_text.text(
                                "Right click the GIF to save it to your computer👇"
                            )
                            empty_image.image(out_gif)

                            out_mp4 = out_gif.replace(".gif", ".mp4")
                            if mp4 and os.path.exists(out_mp4):
                                with empty_video:
                                    st.text(
                                        "Right click the MP4 to save it to your computer👇"
                                    )
                                    st.video(out_gif.replace(".gif", ".mp4"))

                        else:
                            st.error(
                                "Something went wrong. You either requested too much data or the ROI is outside the U.S."
                            )


app()

################################################ to thko mou #################################################
# #!/usr/bin/env python
# # coding: utf-8


# # importing general purpose libraries
# import numpy as np
# import datetime
# import pandas as pd
# import matplotlib.pyplot as plt
# import requests
# import json



# # importing main geo libraries
# import rasterio
# import geopandas as gpd
# from pprint import pprint
# from rasterio.features import Window
# from rasterio.windows import bounds
# from shapely.geometry import MultiPolygon, box

# from PIL import Image
# from rasterio.features import Window
# from subprocess import call


# # importing plotting related libraries


# from IPython import display

# # reminder that if you are installing libraries in a Google Colab instance you will be prompted to restart your kernal
# import seaborn as sns
# import statsmodels.api as sm
# from scipy import stats
# import plotly.offline as py
# import plotly.graph_objs as go

# from ipyleaflet import GeoJSON

# # importing our god and savior geemap
# from geemap import geojson_to_ee, ee_to_geojson

# #Map = geemap.Map()
# #ee_data = geojson_to_ee('./data/planet_22.6586,39.256_23.2218,39.4689.geojson')
# #Map.addLayer(ee_data, {}, "Volos")



# # geemap.ee_initialize()
# # Map = geemap.Map()
# # Map.add_basemap("ESA WorldCover 2020 S2 FCC")
# # Map.add_basemap("ESA WorldCover 2020 S2 TCC")
# # Map.add_basemap("HYBRID")

# # esa = ee.ImageCollection("ESA/WorldCover/v100").first()
# # esa_vis = {"bands": ["Map"]}


# # esri = ee.ImageCollection(
# #     "projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m"
# # ).mosaic()
# # esri_vis = {
# #     "min": 1,
# #     "max": 10,
# #     "palette": [
# #         "#1A5BAB",
# #         "#358221",
# #         "#A7D282",
# #         "#87D19E",
# #         "#FFDB5C",
# #         "#EECFA8",
# #         "#ED022A",
# #         "#EDE9E4",
# #         "#F2FAFF",
# #         "#C8C8C8",
# #     ],
# # }


# # ### Specify some areas of interest manually
# # 
# # In the near future I'll create a function that uses the greece geopackage so that the user can test with that as well.
# #

# # Create Feature Collections for GEE for the abandoned buildings case study.


# # In[5]:


# #this could also be done with a function, but I should provide a list with available names
# def uploaded_file_to_gdf(data):
#     import tempfile
#     import os
#     import uuid

#     _, file_extension = os.path.splitext(data.name)
#     file_id = str(uuid.uuid4())
#     file_path = os.path.join(tempfile.gettempdir(), f"{file_id}{file_extension}")

#     with open(file_path, "wb") as file:
#         file.write(data.getbuffer())

#     if file_path.lower().endswith(".kml"):
#         gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"
#         gdf = gpd.read_file(file_path, driver="KML")
#     else:
#         gdf = gpd.read_file(file_path)

#     return gdf

# #greece_gdf = gpd.read_file("./data/kontur_boundaries_GR_20220407.gpkg") #read greece geopackage
# #greece_fc = geemap.geopandas_to_ee(greece_gdf)

# # select shapefile only for volos and make feature collection
# #volos_gdf = greece_gdf[greece_gdf['name_en']=='Volos Municipality'] 
# #volos_fc = geemap.geopandas_to_ee(volos_gdf) 

# # select shapefles for Trikala Municipality and Trikala Regional Unit shapefile, then
# # make feature collection for trikala municipality and for trikala regional unit
# #trikala_mun_gdf = greece_gdf[greece_gdf['name_en']=='Trikala Municipality'] 
# #trikala_regunit_gdf = greece_gdf[greece_gdf['name_en']=='Trikala Regional Unit']

# #trikala_mun_fc = geemap.geopandas_to_ee(trikala_mun_gdf) 
# #trikala_regun_fc = geemap.geopandas_to_ee(trikala_regunit_gdf) #


# # In[1]:


# greek_cities = pd.read_csv("./data/csvs/greek_cities.csv")
# greek_cities


# # In[27]:


# greek_cities = pd.read_csv('./data/csvs/greek_cities.csv')
# greek_cities


# # In[29]:


# greek_cities_dropped = greek_cities.dropna()
# greek_cities_dropped.to_csv('./data/csvs/greek_cities.csv')


# # In[31]:


# #esa = ee.ImageCollection("ESA/WorldCover/v100").first()
# #esa

# #poleis = gpd.read_file("./data/poleis/poleis.shp")
# #poleis = poleis.drop('ONOMA',axis=1)
# #poleis.to_csv('./data/greek_cities.csv',index=False)
# #poleis.to_file('./data/greek_cities.geojson',index=False)
# #poleispoleis['longitude'] = poleis.geometry.x
# #poleis['latitude'] = poleis.geometry.y
# #poleis
# # In[9]:


# trikala_regunit_gdf.to_file("trikala_reg_uni.geojson", driver='GeoJSON')
# trikala_mun_gdf.to_file("trikala_municipality.geojson", driver='GeoJSON')
# volos_gdf.to_file("volos_municipality.geojson", driver='GeoJSON')


# # In[8]:


# trikala_mun_gdf


# # In[7]:


# volos_gdf


# # In[6]:


# greece_gdf


# # ### User Input Fuctions
# # 
# # User specifies desired date and area of interest

# # In[5]:


# # See google earth datasets for data availability over a particular datetime

# #Latest Sentinel-2: 2017-03-28T00:00:00Z - 2022-06-10T00:00:00
# #latest Viirs DNB Monthly : 2014-01-01T00:00:00Z - 2022-05-01T00:00:00


# # In[46]:


# #function that takes desired timeframe through user input ini YY-MM-DD format\n",
# def set_dates():
#     startDate = input('Enter you desired starting date (YYYYMMDD): ')
#     endDate = input('Enter you desired ending date (YYYYMMDD): ')
#     return startDate,endDate

# startDate,endDate= set_dates()
# #('2015-01-01','2022-01-01')


# # In[ ]:


# #2021-01-01 2022-01-01


# # In[9]:


# ### Data, preprocessing and visualization


# # In[9]:


# # get our Magnisia boundary - there's a problem with the coastline
# magnisia = ee.FeatureCollection("FAO/GAUL/2015/level2").filter(ee.Filter.eq('ADM2_NAME','Magnisias')).geometry()


# # In[10]:


# trikala = ee.FeatureCollection("FAO/GAUL/2015/level2").filter(ee.Filter.eq('ADM2_NAME','Trikkaion')).geometry()


# # In[11]:


# # Get data from GGE over the specified location and timeframe

# # try with a rough outline of volos municipality

# volos_rough = ee.Geometry.Polygon([
#           [
#             22.96614646911621,
#             39.35095850174936
#           ],
#           [
#             22.996315956115723,
#             39.373454601030474
#           ],
#           [
#             22.971510887145996,
#             39.391499329244546
#           ],
#           [
#             22.951598167419434,
#             39.38901182227906
#           ],
#           [
#             22.94391632080078,
#             39.41219194887819
#           ],
#           [
#             22.92245864868164,
#             39.41232457407302
#           ],
#           [
#             22.914047241210938,
#             39.39388725250263
#           ],
#           [
#             22.916278839111325,
#             39.38738660316804
#           ],
#           [
#             22.903404235839844,
#             39.37425079034718
#           ],
#           [
#             22.893447875976562,
#             39.359519818280745
#           ],
#           [
#             22.925891876220703,
#             39.35155583694641
#           ],
#           [
#             22.932758331298828,
#             39.35474153842095
#           ],
#           [
#             22.96794891357422,
#             39.35089213085671
#           ]
#         ])
# # In[20]:


# import time
# from datetime import timedelta

# #magnisia
# #"COPERNICUS/S2_SR"
# #['EVI','NDVI','NDBI','IBI','UI','BLFEI']


# # In[29]:


# # Ask the user to define the satellite/image_collection they want to get data for
# # Ask him to also define the indices they want to check
# gee_name = input()
# indices = input()


# # In[34]:


# type(indices)


# # In[47]:


# import eemont #improved iteration of ee api

# def select_satellite(gee_name,bounds,indices):
#     #data from sentinel-2 surface reflectance

#     satellite = (ee.ImageCollection(gee_name)
#         .filterBounds(bounds)
#         .filterDate(startDate,endDate)
#         .maskClouds()
#         .scaleAndOffset()
#         .spectralIndices(['EVI','NDVI','NDBI','IBI','UI','BLFEI'])) 
#     print('satellite data loaded')
#     return satellite
# #select some bands
# #N = s2.select('B8')
# #R = s2.select('B4')
# #B = s2.select('B2')
# #G = s2.select('B3')

# s2 = select_satellite(gee_name,magnisia,indices)


# # In[44]:


# #generate time series over aoi, get spectral indices(awsome index)
# def generate_time_series(satellite):
#     time_series  = satellite.getTimeSeriesByRegion(ee.Reducer.mean(),
#                               geometry = volos_fc,
#                               bands = ['NDVI','NDBI','IBI','UI'],
#                               scale = 10,
#                               bestEffort = True,
#                               maxPixels = 1e13,
#                               dateFormat = 'YYYYMMdd',
#                               tileScale = 2)
#     print('start')
#     start_time = time.monotonic()

#     #use geemap to generate a pandas dataframe from the time series(contains the ts for the selected indices)
#     satellite_df= geemap.ee_to_pandas(time_series)
#     end_time = time.monotonic()
#     print(timedelta(seconds=end_time - start_time))
    
#     satellite_df[satellite_df == -9999] = np.nan # we do that to generate nan values when we don't have data
#     satellite_df['date'] = pd.to_datetime(satellite_df['date'],infer_datetime_format = True)
    
#     return satellite_df


# # In[48]:


# s2_df_till_19= generate_time_series(s2)


# # In[61]:


# startDate,endDate= set_dates()
# s2 = select_satellite(gee_name,magnisia,indices)
# s2_df_till_2021 = generate_time_series(s2)


# # In[62]:


# s2_df_till_2021 = s2_df_till_now


# # In[63]:


# startDate,endDate= set_dates()
# s2 = select_satellite(gee_name,magnisia,indices)
# s2_df_till_now = generate_time_series(s2)


# # In[68]:


# #len(s2_df_till_19) #597
# #len(s2_df_till_2021) #870
# #len(s2_df_till_now) #582


# # In[72]:


# s2_df_till_2021


# # In[76]:


# s2_df = s2_df_till_19.append(s2_df_till_2021,ignore_index=True)
# s2_df = s2_df.append(s2_df_till_now,ignore_index=True)


# # In[ ]:


# # export to csv


# # In[110]:


# # preview the sentinel-2 time series dataframe
# s2_df


# # In[ ]:





# # In[79]:


# #get times series of average radiance from viirs dnb monthly composites
# startDate,endDate= set_dates()

# viirs = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG").filterDate(startDate,endDate).select('avg_rad')

# viirs_ts = viirs.getTimeSeriesByRegion(ee.Reducer.mean(),
#                               geometry = volos_fc,
#                               scale = 10,
#                               bestEffort = True,
#                               maxPixels = 1e9,
#                               dateFormat = 'YYYYMMdd',
#                               tileScale = 2)

# viirs_df = geemap.ee_to_pandas(viirs_ts)
# viirs_df['date'] = pd.to_datetime(viirs_df['date'],infer_datetime_format = True)


# # In[80]:


# viirs_df


# # In[ ]:





# # In[81]:


# #enter integet for desired image number
# image_no = int(input())


# # In[16]:


# type(image_no)


# # In[82]:


# #function that takes as input the desired collections and returns the image we want
# def make_list_of_images(sentinel_collection,viirs_collection,image_no):
#     listOfS2Images = sentinel_collection.toList(sentinel_collection.size())
#     s2img = ee.Image(listOfS2Images.get(image_no))
#     listOfViirsImages= viirs_collection.toList(viirs_collection.size())
#     viirs_img = ee.Image(listOfViirsImages.get(image_no))
#     return s2img,viirs_img
# s2img,viirs_img = make_list_of_images(s2,viirs,image_no)


# # In[39]:


# # We proceed to visuzlize our aoi on a Map
# # We use the geemap tool, since it integrates with gee and offers some cool features, such as timelapse
# # and even geoprocessing tools


# # In[83]:



# # initialize our map
# Map = geemap.Map()
# Map.centerObject(volos_fc, 7)
# Map.addLayer(s2img.clip(magnisia), rgbViz, "S2")
# Map.addLayer(viirs_img.clip(magnisia), {}, "Viirs")
# Map.addLayerControl()
# Map


# # ### Data Preprocessing
# # 
# # In this part of the notebook, I ll do some basic preprocessing in order to better visualize the data. Some extra preprocessing may be added in the future.
# # 
# # Implemented :
# # 
# #     - Fill each column with the mean values
# #     
# # Will be added :
# #     
# #     - Fill with interpolation
# #     - Harmonizing
# #      
# # 

# # In[99]:


# # This should be turned into a function, in which you can specify the fill method(mean,mode,median)


# # In[84]:


# #filled_sentinel = pd.DataFrame()
# #filled_sentinel['date'] = s2_df['date']


# # In[108]:





# # In[111]:


# def fill_s2_with_mean(sentinel_dataset):
# #filled_sentinel['EVI'] = s2_df['EVI'].fillna(s2_df['EVI'].mean())
#     sentinel_dataset['NDVI'] = sentinel_dataset['NDVI'].fillna(sentinel_dataset['NDVI'].mean())
#     sentinel_dataset['IBI'] = sentinel_dataset['IBI'].fillna(sentinel_dataset['IBI'].mean())
#     sentinel_dataset['NDBI'] = sentinel_dataset['NDBI'].fillna(sentinel_dataset['NDBI'].mean())
# #filled_sentinel['BLFEI'] = s2_df['BLFEI'].fillna(s2_df['BLFEI'].mean())
#     sentinel_dataset['UI'] = sentinel_dataset['UI'].fillna(sentinel_dataset['UI'].mean())
    
#     del sentinel_dataset['reducer']
#     return sentinel_dataset
# filled_s2 = fill_s2_with_mean(s2_df)


# # In[112]:


# filled_s2 # to evi exei 100% outlier, genika kalo tha htan na vrw tous outliers prin kanw kapoio fillna me mean giati
#                 # einai euais8hto


# # In[50]:


# # Save dataframes to csv in order to perform EDA in other notebooks


# # In[113]:


# filled_s2.to_csv('./data/csvs/filled_sentinel.csv',index=False)
# viirs_df.to_csv('./data/csvs/viirs.csv',index=False)


# # In[49]:




# # Function to fill each column with mean 
# #s2_df.columns
# def fill_nan(data):
#         for i in data.columns:
#             filled[i] = data[i].fillna(data[i].mean(),inplace=True)
#             return filled
# mean_filled = fill_nan(s2_df)
# mean_filled.isnull().sum()
# # # Data Visualization

# # https://udst.github.io/urbansim/examples.html

# # In[ ]:





# # ### Abandoned Buildings Time Series Clustering and Classification

# # #### Time Series Clustering : Computed in Time_Series_Clustering.ipynb

# # In[ ]:





# # In[ ]:





# # #### Classification will be used after computing the chicago and philly datasets since we should know the label before running the algorithms
# # 
# # Define our dependent and independent variables
# X=test[['EVI','NDVI','NDBI','UI','BLFEI']]
# #y=test['label']from sklearn.model_selection import train_test_split
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.metrics import accuracy_score

# X_train,x_test,Y_train,y_test = train_test_split(X,y, test_size=0.3, random_state=1)

# classifier = RandomForestClassifier(n_estimators=100)

# classifier.fit(X_train, Y_train)
# y_pred = classifier.predict(x_test)
# accuracy_score(y_test, y_pred)from sklearn.model_selection import train_test_split
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.metrics import accuracy_score
# # Define our dependent and independent variables
# X=test[['EVI','NDVI','NDBI','UI','BLFEI']]
# #y=test['label']

# X_train,x_test,Y_train,y_test = train_test_split(X,y, test_size=0.3, random_state=1)

# classifier = RandomForestClassifier(n_estimators=100)

# classifier.fit(X_train, Y_train)
# y_pred = classifier.predict(x_test)
# accuracy_score(y_test, y_pred)

# from sktime.classification.hybrid import HIVECOTEV2

# hc2 = HIVECOTEV2(time_limit_in_minutes=1)
# hc2.fit(X_train, Y_train)
# y_pred = hc2.predict(x_test)
# accuracy_score(y_test, y_pred)

# from sktime.classification.kernel_based import RocketClassifier

# rocket = RocketClassifier()
# rocket.fit(X_train, Y_train)
# y_pred = rocket.predict(x_test)
# accuracy_score(y_test, y_pred)from sktime.classification.kernel_based import RocketClassifier

# rocket = RocketClassifier()
# rocket.fit(X_train, Y_train)
# y_pred = rocket.predict(x_test)
# accuracy_score(y_test, y_pred)
# # In[ ]:





# # In[ ]:





# # In[220]:





# # In[93]:





# # In[64]:


# #After constructing the time series We will combine the derived dataframes into one


# # In[ ]:


# #Firstly let's explore them


# # In[65]:


# s2_df.info()


# # In[66]:


# viirs_df.info()


# # In[ ]:


# #We can see that they have an entry difference, which is logical since the one consists of acquired every 2-3 days(s2)
# #while the other consists of monthly composites


# # In[ ]:


# #Methodology for combining
# #Create a column with the month, this will act as the criterion for joining the dataframes
# #Join the dataframes
# #drop the month column

# #The current implementaion uses nested loops which are inefficient. There's probably a better way to do it.


# # In[57]:


# #Create a column with the month, this will act as the criterion for joining the dataframes
# def print_lens(bigger_df,smaller_df):
#     print('Length sentinel2 dataframe: ', len(bigger_df))
#     print('Length viirs dataframe: ', len(smaller_df))


# # In[62]:


# def create_month(bigger_df,smaller_df):
#     bigger_df_month = bigger_df

#     bigger_df_month['month'] = bigger_df_month['date'].dt.month # datetime library

#     smaller_df_month = smaller_df
#     smaller_df_month['month'] = smaller_df_month['date'].dt.month
#     return bigger_df_month,smaller_df_month
# #merged = s2_df.merge(viirs_df,)
# bigger_df_month,smaller_df_month = create_month(s2_df,viirs_df)
# print_lens(bigger_df_month,smaller_df_month)


# # # TILL HERE WAS THE PROCESS OF COMBINING THE DFS - UNSUCCESSFUL\
# # 
# # ## I 'll try in combine_Dataframe.ipynb

# # In[12]:


# #Below I used a different S2 image(median) for better visualization


# # get our Nepal boundary
# aoi = ee.FeatureCollection("FAO/GAUL/2015/level1").filter(ee.Filter.eq('ADM1_NAME','Thessalia')).geometry()

# # Sentinel-2 image filtered on 2019 and on Nepal
# se2 = ee.ImageCollection('COPERNICUS/S2').filterDate("2015-01-01","2022-01-01").filterBounds(aoi).median().divide(10000)

# rgb = ['B4','B3','B2']

# # set some thresholds
# rgbViz = {"min":0.0, "max":0.3,"bands":rgb}


# # initialize our map
# map1 = geemap.Map()
# map1.centerObject(aoi, 7)
# map1.addLayer(se2.clip(aoi), rgbViz, "S2")

# map1.addLayerControl()
# map1
# nighttime = viirs.select('avg_rad')

# nighttimeVis = {min: 0.0, max: 60.0}

# Map.setCenter(fc, 8);
# Map.addLayer(nighttime, nighttimeVis, 'Nighttime')
# # In[ ]:





# # In[ ]:





# # In[ ]:





# # In[ ]:





# # In[ ]:





# # In[ ]:





# # In[ ]:





# # In[16]:


# # A sample of hand-labeled points of interest

# # This part of the project needs improvement


# # In[17]:


# # We use these hand-labeled pois in order to train a classifier for abandoned buildings.

# # With the current approach, we underfit our model and pretty much get garbage.


# # In[18]:


# #Suggested Improvements:
    
#     #Train the classifier on a different area (can't really find a dataset that contains both coordinates and tags or did I?)
#     #check provided data folder
    
#     #Use openstreetmaps for building boundary extraction so that We don't have to do it ourselves
#     #Drawback: don't know the building correspondance and I still have to hand-label the dataset


# # In[444]:


# #Found vacancy data from Philadelphia
# #Going to extract my indices from there
# #I ll also fusion some local hand-labeled ones


# # In[130]:


# ### EKTOS APO TO OIKONOMAKI TA ALLA EINAI ABANDONED

# kount_fil = ee.Geometry.Polygon([
#           [
#             22.952406182885166,
#             39.35917348693331
#           ],
#           [
#             22.952624447643757,
#             39.359061499184136
#           ],
#           [
#             22.952531576156613,
#             39.35895702896919
#           ],
#           [
#             22.952297888696194,
#             39.35905890687299
#           ],
#           [
#             22.952407523989677,
#             39.359176597701556
#           ]
#         ])
# kount_mavro = ee.Geometry.Polygon([
#           [
#             22.951523065567017,
#             39.35919215154071
#           ],
#           [
#             22.951737642288208,
#             39.35908016382146
#           ],
#           [
#             22.951886504888535,
#             39.3592429607245
#           ],
#           [
#             22.95165583491325,
#             39.35935598510286
#           ],
#           [
#             22.951521389186382,
#             39.35919085538758
#           ]
#         ])

# fil_28okt = ee.Geometry.Polygon( [
#           [
#             22.95275218784809,
#             39.35951204139807
#           ],
#           [
#             22.952881939709187,
#             39.35942908792906
#           ],
#           [
#             22.95277565717697,
#             39.35932072981181
#           ],
#           [
#             22.95261740684509,
#             39.35940160957075
#           ],
#           [
#             22.952740788459778,
#             39.359515670610094
#           ]
#         ])

# fill_28okt2 = ee.Geometry.Polygon([
#           [
#             22.95280247926712,
#             39.359597846288914
#           ],
#           [
#             22.95294027775526,
#             39.35953174283249
#           ],
#           [
#             22.9528571292758,
#             39.359441271726006
#           ],
#           [
#             22.95270960777998,
#             39.35952889130942
#           ],
#           [
#             22.952714301645756,
#             39.35956570187087
#           ],
#           [
#             22.952717654407024,
#             39.35957736718557
#           ],
#           [
#             22.952751852571964,
#             39.35956777570473
#           ],
#           [
#             22.952791415154934,
#             39.35959499476857
#           ],
#           [
#             22.95280247926712,
#             39.359595253997696
#           ],
#           [
#             22.952802814543247,
#             39.35960017935096
#           ],
#           [
#             22.95280449092388,
#             39.359598883205386
#           ]
#         ])

# # not abandoned
# fil_fer = ee.Geometry.Polygon([
#           [
#             22.95489829033613,
#             39.361775077721575
#           ],
#           [
#             22.954826205968857,
#             39.361703014235744
#           ],
#           [
#             22.954844646155834,
#             39.36168823861977
#           ],
#           [
#             22.95478966087103,
#             39.361634320555964
#           ],
#           [
#             22.95481715351343,
#             39.361614360492915
#           ],
#           [
#             22.954944893717766,
#             39.36154437061647
#           ],
#           [
#             22.955089397728443,
#             39.3616892755052
#           ],
#           [
#             22.954903990030285,
#             39.361783632015296
#           ],
#           [
#             22.954898625612255,
#             39.36177715148985
#           ]
#         ])

# fil_fer_apenanti = ee.Geometry.Polygon([
#           [
#             22.955063581466675,
#             39.362018745072554
#           ],
#           [
#             22.955232560634613,
#             39.361943052752395
#           ],
#           [
#             22.95509308576584,
#             39.36182692190997
#           ],
#           [
#             22.95496568083763,
#             39.36189742994447
#           ],
#           [
#             22.955056875944138,
#             39.36201148690843
#           ]
#         ])
# #not abandoned
# konst_gamv = ee.Geometry.Polygon( [
#           [
#             22.95320212841034,
#             39.36192127823414
#           ],
#           [
#             22.953552156686783,
#             39.36170871710425
#           ],
#           [
#             22.95335903763771,
#             39.36154488906026
#           ],
#           [
#             22.95302912592888,
#             39.361739823651455
#           ],
#           [
#             22.953198105096817,
#             39.36191816758813
#           ]
#         ])

# poi_oikonomaki= ee.Geometry.Polygon([[[
#               22.949098348617554,39.35979978548018],
#             [22.951193153858185,39.35979978548018 ],
#             [22.951193153858185,39.36196275350115],
#             [22.949098348617554,39.36196275350115],
#             [22.949098348617554,39.35979978548018]]])

# f1 = ee.Feature(konst_gamv,{'ID':'1_0','Class':'Not Abandoned','ClassPallete':'006633'})
# f2 = ee.Feature(fil_fer_apenanti,{'ID':'2_0','Class':'Not Abandoned','ClassPallete':'006633'})
# f3 = ee.Feature(fil_fer,{'ID':'3_0','Class':'Not Abandoned','ClassPallete':'006633'})
# f4 = ee.Feature(fill_28okt2,{'ID':'4_0','Class':'Abandoned','ClassPallete':'E5FFCC'})
# f5 = ee.Feature(fil_28okt,{'ID':'5_0','Class':'Abandoned','ClassPallete':'E5FFCC'})
# f6 = ee.Feature(kount_mavro,{'ID':'6_0','Class':'Abandoned','ClassPallete':'E5FFCC'})
# f7 = ee.Feature(poi_oikonomaki,{'ID':'7_0','Class':'Not Abandoned','ClassPallete':'006633'})
# f8 = ee.Feature(kount_fil,{'ID':'8_0','Class':'Abandoned','ClassPallete':'E5FFCC'})

# #f2 = ee.Feature(ee.Geometry.Point([22.947140336036682,39.36547976654773]).buffer(50),{'ID':'B'})
# abandoned_volos = ee.FeatureCollection([f4,f5,f6,f8])
# not_abandoned_volos =  ee.FeatureCollection([f1,f2,f3,f7])
# # In[446]:


# #Greece boundaries taken from world bank data portal

# countries_gdf = gpd.read_file("./data/kontur_boundaries_GR_20220407.gpkg")
# volos_gdf = countries_gdf[countries_gdf['name_en']=='Volos Municipality']
# countries_fc = geemap.geopandas_to_ee(countries_gdf)

# # https://geemap.org/notebooks/geopandas/#convert-eefeaturecollection-to-pandas-dataframe
# # 
# # Poly asteio pou den eixa dei auto kai efaga 2 wres na kanw to geopandas se feature collection
# en_names = countries_gdf['name_en'].unique()#use in order to list available english names from the geopackage of greece
# for i in en_names:
#     print(i)volos_gdf = countries_gdf[countries_gdf['name_en']=='Volos Municipality']
# countries_fc = geemap.geopandas_to_ee(countries_gdf)

# # In[ ]:




# #An valoume to gdf gia olhh thn ellada exei terastio payload gia to gee opote de trexei
# volos_municipality = geemap.geopandas_to_ee(volos_gdf)
# Map = geemap.Map()
# Map.addLayer(volos_municipality, {}, "Volos Municipality")
# Map.centerObject(volos_municipality, 9)
# Map
# # ### Load Vacant points, land and buildings geojson from Philadelphia

# # In[116]:


# # Load chicago service calls and then take the abandoned buildings reports from that
# chicago_service = pd.read_csv("./data/311_Service_Requests.csv")
# chicago_service

# chicago_service.SR_TYPE.unique()
# #Vacant/Abandoned Building Complaint # abandoned
# #Clean Vacant Lot Request # abandoned
# #Shared Housing/Vacation Rental Complaint' # not_abandoned
# #Building Violation' #not_abandoned
# #Water Quality Concern'
# # In[117]:


# chicago_pois = chicago_service.loc[chicago_service['SR_TYPE'].isin(['Vacant/Abandoned Building Complaint','Clean Vacant Lot Request',
#                                                              'Shared Housing/Vacation Rental Complaint','Building Violation',
#                                                               'Water Quality Concern'])]
# chicago_pois 


# # In[118]:


# chicago_pois = chicago_pois.rename(columns = {'LATITUDE':'Latitude', 'LONGITUDE':'Longitude'})
# chicago_pois


# # In[119]:


# # Let's assume that shared housing,water quality and building violation correlated  to not abandoned buildings
# chicago_abandoned = chicago_pois.loc[chicago_pois['SR_TYPE'].isin(['Vacant/Abandoned Building Complaint',
#                                                                    'Clean Vacant Lot Request'])]
# chicago_abandoned = chicago_abandoned.dropna()
# chicago_abandoned = chicago_abandoned.reset_index()
# #chicago_abandoned = chicago_abandoned.drop(chicago_abandoned.index)
# chicago_abandoned = chicago_abandoned.set_index(chicago_abandoned.index)
# # Let's assume that shared housing,water quality and building violation correlated  to not abandoned buildings
# chicago_not_abandoned = chicago_pois.loc[chicago_pois['SR_TYPE'].isin(['Shared Housing/Vacation Rental Complaint','Building Violation',
#                                                        'Water Quality Concern'])]

# chicago_not_abandoned = chicago_not_abandoned.dropna()
# chicago_not_abandoned = chicago_not_abandoned.reset_index() 
# #chicago_not_abandoned = chicago_not_abandoned.drop(chicago_not_abandoned.index)
# chicago_not_abandoned = chicago_not_abandoned.set_index(chicago_not_abandoned.index)


# # In[123]:


# # Create list of ee.Points from dataset's coordinates
# def make_point_list(data):
#     point = list()
#     feature = list()
#     for i in range(len(data)):
#         point.append(ee.Geometry.Point(data.Latitude.loc[i],data.Longitude.loc[i]))
#         feature.append(ee.Feature(point[i]))
#     feature_collection = ee.FeatureCollection(feature) # feature collection of VacantSpace_uk.xls
#     return feature_collection
# chicago_abandoned_fc = make_point_list(chicago_abandoned)
# chicago_not_abandoned_fc = make_point_list(chicago_not_abandoned)


# # In[137]:


# #https://overpass-turbo.eu/# trurbo source
# #https://wiki.openstreetmap.org/wiki/Map_features


# # In[129]:


# turbo_volos_bldgs = gpd.read_file('./data/turbo_volos_bldgs.geojson') #read volos_bldgs_geojson
# turbo_volos_bldgs_fc = geemap.geopandas_to_ee(turbo_volos_bldgs)


# # In[ ]:


# startDate,endDate= set_dates()
# s2 = select_satellite(gee_name,magnisia,indices)
# s2_df_till_now = generate_time_series(s2)


# # In[132]:


# #import eemont #improved iteration of ee api
# startDate,endDate= set_dates()

# # construct a feature collection using two topologies with a radius of 50meters each, they probably overlap
# # this was improved later, where I added hand-labeled locations(abandoned/not abandoned buildings)
# #f1 = ee.Feature(ee.Geometry.Point([22.951893210411072,39.35932487749404]).buffer(50),{'ID':'A'})
# #f2 = ee.Feature(ee.Geometry.Point([22.947140336036682,39.36547976654773]).buffer(50),{'ID':'B'})
# #fc = ee.FeatureCollection([volos_rough])

# #data from sentinel-2 surface reflectance

# turbo_volos = (ee.ImageCollection("COPERNICUS/S2_SR")
#     .filterBounds(turbo_volos_bldgs_fc)
#     .filterDate(startDate,endDate)
#     .maskClouds()
#     .scaleAndOffset()
#     .spectralIndices(['EVI','NDVI','NDBI','IBI','UI','BLFEI'])) 

# #select some bands
# #N = s2.select('B8')
# #R = s2.select('B4')
# #B = s2.select('B2')
# #G = s2.select('B3')
# print('done')
# #generate time series over aoi, get spectral indices(awsome index)

# turbo_volos_ts = turbo_volos.getTimeSeriesByRegion(ee.Reducer.mean(),
#                               geometry = turbo_volos_bldgs_fc,
#                               bands = ['NDVI','NDBI','IBI','UI'],
#                               scale = 10,
#                               bestEffort = True,
#                               maxPixels = 1e13,
#                               dateFormat = 'YYYYMMdd',
#                               tileScale = 2)
# start_time = time.monotonic()

# #use geemap to generate a pandas dataframe from the time series(contains the ts for the selected indices)
# turbo_volos_df= geemap.ee_to_pandas(turbo_volos_ts)
# end_time = time.monotonic()
# print(timedelta(seconds=end_time - start_time))
# turbo_volos_df[turbo_volos_df == -9999] = np.nan # we do that to generate nan values when we don't have data
# turbo_volos_df['date'] = pd.to_datetime(turbo_volos_df['date'],infer_datetime_format = True)


# # In[133]:


# filled_turbo = fill_s2_with_mean(turbo_volos_df)


# # In[134]:


# filled_turbo


# # In[139]:


# turbo_volos_df.to_csv('./data/csvs/turbo_volos_df.csv',index=False)


# # In[178]:


# viirs_turbo_df= make_viirs(turbo_volos_bldgs_fc)


# # In[179]:


# viirs_turbo_df.to_csv('./data/csvs/viirs_turbo_df.csv',index=False)


# # In[140]:


# f1 = ee.Feature(konst_gamv) #,{'ID':'1_0','Class':'Not Abandoned','ClassPallete':'006633'}
# f2 = ee.Feature(fil_fer_apenanti) # ,{'ID':'2_0','Class':'Not Abandoned','ClassPallete':'006633'}
# f3 = ee.Feature(fil_fer) # ,{'ID':'3_0','Class':'Not Abandoned','ClassPallete':'006633'}
# f4 = ee.Feature(fill_28okt2) # ,{'ID':'4_0','Class':'Abandoned','ClassPallete':'E5FFCC'}
# f5 = ee.Feature(fil_28okt) # ,{'ID':'5_0','Class':'Abandoned','ClassPallete':'E5FFCC'}
# f6 = ee.Feature(kount_mavro) # ,{'ID':'6_0','Class':'Abandoned','ClassPallete':'E5FFCC'}
# f7 = ee.Feature(poi_oikonomaki) # ,{'ID':'7_0','Class':'Not Abandoned','ClassPallete':'006633'}
# f8 = ee.Feature(kount_fil) # ,{'ID':'8_0','Class':'Abandoned','ClassPallete':'E5FFCC'}

# #f2 = ee.Feature(ee.Geometry.Point([22.947140336036682,39.36547976654773]).buffer(50),{'ID':'B'})
# abandoned_volos = ee.FeatureCollection([f4,f5,f6,f8])
# not_abandoned_volos =  ee.FeatureCollection([f1,f2,f3,f7])


# # In[ ]:





# # In[124]:


# vacant_uk = pd.read_excel("./data/VacantSpace_uk.xls")
# vacant_uk


# # In[141]:


# # Create list of ee.Points from dataset's coordinates

# vacant_uk_fc = make_point_list(vacant_uk) # feature collection of VacantSpace_uk.xls


# # In[142]:


# # Combine vacant/abandoned collections

# abandoned_collection = ee.FeatureCollection([chicago_abandoned_fc,vacant_uk_fc,abandoned_volos])
# not_abandoned_collection = ee.FeatureCollection([chicago_not_abandoned_fc,not_abandoned_volos])


# # In[144]:


# # source: opendatatphily
# # https://www.opendataphilly.org/dataset/vacant-property-indicators
# vacant_philly_points = gpd.read_file("./data/Vacant_Indicators_Points.geojson") 


# # In[ ]:





# # In[145]:


# vacant_philly_land = gpd.read_file("./data/Vacant_Indicators_Land.geojson")


# # In[146]:


# vacant_philly_bldgs = gpd.read_file("./data/Vacant_Indicators_Bldg.geojson")

# # Irrelevant for Volos, only includes one industrial area
# hotosm = gpd.read_file("./data/hotosm_grc_buildings.gpkg")
# hotosm#I ll filter the multipolygons since they seem to make gee implementation impossible
# vacant_bld_pol = vacant_philly_bldgs[vacant_philly_bldgs.geometry.type!="MULTIPOLYGON"]

# # In[147]:


# # drop the columns that we don't need to reduce computing time
# vacant_buildings_ph =  vacant_philly_bldgs.drop(columns=['OBJECTID','ADDRESS','OWNER1','OWNER2','BLDG_DESC','OPA_ID',
#                                                  'LNIADDRESSKEY','COUNCILDISTRICT','ZONINGBASEDISTRICT',
#                                                'ZIPCODE','BUILD_RANK','Shape__Area','Shape__Length'])
# vacant_buildings_ph

# # turn geopandas to ee feature collection
# vacant_philly_buildings_fc = geemap.geopandas_to_ee(vacant_philly_bldgs)
# # In[149]:


# vacant_philly_buildings_ph_fc = geemap.geopandas_to_ee(vacant_buildings_ph) # let;s take only hhhe first 100


# # In[150]:


# vacant_philly_buildings_ph_fc.size().getInfo()


# # In[154]:


# turbo_volos_bldgs_fc.size().getInfo()


# # In[159]:


# # Combine vacant/abandoned collections

# abandoned_collection = ee.FeatureCollection([chicago_abandoned_fc,vacant_uk_fc,abandoned_volos]).flatten()
# not_abandoned_collection = ee.FeatureCollection([chicago_not_abandoned_fc,not_abandoned_volos]).flatten()

# # FEATURE COLLECTION THAT COMBINES ALL PREVIOUS ONES
# final_fc = ee.FeatureCollection([vacant_philly_buildings_ph_fc,abandoned_collection,not_abandoned_collection,turbo_volos_bldgs_fc]).flatten()
# # In[156]:


# final_fc.flatten()


# # In[198]:


# #Get Time Series and export to csv
# # Tha ginei function pou tha pairnei to geometry

# import eemont #improved iteration of ee api

# def select_satellite(gee_name,bounds,indices):
#     #data from sentinel-2 surface reflectance

#     satellite = (ee.ImageCollection(gee_name)
#         .filterBounds(bounds)
#         .filterDate(startDate,endDate)
#         .maskClouds()
#         .scaleAndOffset()
#         .spectralIndices(['EVI','NDVI','NDBI','IBI','UI','BLFEI'])) 
#     print('satellite data loaded')
#     return satellite
# #select some bands
# #N = s2.select('B8')
# #R = s2.select('B4')
# #B = s2.select('B2')
# #G = s2.select('B3')

# s2 = select_satellite(gee_name,magnisia,indices)
# # In[161]:


# #generate time series over aoi, get spectral indices(awsome index) #  fixed
# def generate_time_series(satellite,geometry):
#     time_series  = satellite.getTimeSeriesByRegion(ee.Reducer.mean(),
#                               geometry = geometry,
#                               bands = ['NDVI','NDBI','IBI','UI'],
#                               scale = 10,
#                               bestEffort = True,
#                               maxPixels = 1e13,
#                               dateFormat = 'YYYYMMdd',
#                               tileScale = 2)
#     print('start')
#     start_time = time.monotonic()

#     #use geemap to generate a pandas dataframe from the time series(contains the ts for the selected indices)
#     satellite_df= geemap.ee_to_pandas(time_series)
#     end_time = time.monotonic()
#     print(timedelta(seconds=end_time - start_time))
    
#     satellite_df[satellite_df == -9999] = np.nan # we do that to generate nan values when we don't have data
#     satellite_df['date'] = pd.to_datetime(satellite_df['date'],infer_datetime_format = True)
    
#     return satellite_df


# # In[162]:


# startDate,endDate= set_dates()
# abandoned_s2 =select_satellite(gee_name,abandoned_collection,indices)
# not_abandoned_s2 = select_satellite(gee_name,not_abandoned_collection,indices)
# abadnoned_s2_df = generate_time_series(abandoned_s2,abandoned_collection)
# not_abadnoned_s2_df = generate_time_series(not_abandoned_s2,not_abandoned_collection)


# # In[ ]:





# # In[176]:


# abadnoned_s2_filled= fill_s2_with_mean(abadnoned_s2_df)
# not_abadnoned_s2_filled=fill_s2_with_mean(not_abadnoned_s2_df)


# # In[177]:


# abadnoned_s2_filled.to_csv('./data/csvs/abandoned_s2.csv',index=False)
# not_abadnoned_s2_filled.to_csv('./data/csvs/not_abandoned_s2.csv',index=False)


# # In[169]:


# # test oik
# #get times series of average radiance from viirs dnb monthly composites 
# def make_viirs(geometry):
#     viirs_class = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG").filterDate(startDate,endDate).select('avg_rad')

#     viirs_ts= viirs_class.getTimeSeriesByRegion(ee.Reducer.mean(),
#                               geometry = geometry,
#                               scale = 750,
#                               bestEffort = True,
#                               maxPixels = 1e9,
#                               dateFormat = 'YYYYMMdd',
#                               tileScale = 2)
#     print('done')
#     start_time = time.monotonic()
    
#     viirs_df = geemap.ee_to_pandas(viirs_ts)
#     end_time = time.monotonic()
#     print(timedelta(seconds=end_time - start_time))
#     viirs_df['date'] = pd.to_datetime(viirs_df['date'],infer_datetime_format = True)
#     return(viirs_df)


# # In[171]:


# startDate,endDate= set_dates() #2017/2020

# viirs_abandoned = make_viirs(abandoned_collection)
# viirs_not_abandoned = make_viirs(not_abandoned_collection)


# # In[173]:


# viirs_abandoned.to_csv('./data/csvs/viirs_abandoned.csv',index=False)
# viirs_not_abandoned.to_csv('./data/csvs/viirs_not_abandoned.csv',index=False)


# # In[174]:


# #classifier


# # In[180]:


# startDate,endDate= set_dates()
# s2_oikonomaki =select_satellite(gee_name,poi_oikonomaki,indices)
# s2_oikonomaki_df = generate_time_series(abandoned_s2,poi_oikonomaki)
# viirs_oikonomaki = make_viirs(poi_oikonomaki)
# s2_oikonomaki_df=fill_s2_with_mean(s2_oikonomaki_df)


# # In[181]:


# s2_oikonomaki_df.to_csv('./data/csvs/oik.csv',index=False)
# viirs_not_abandoned.to_csv('./data/csvs/viirs_oik.csv',index=False)


# # In[ ]:





# # In[ ]:





# # In[163]:


# #ignore the rest for now


# # In[ ]:


# #import eemont #improved iteration of ee api
# startDate,endDate= set_dates()

# # construct a feature collection using two topologies with a radius of 50meters each, they probably overlap
# # this was improved later, where I added hand-labeled locations(abandoned/not abandoned buildings)
# #f1 = ee.Feature(ee.Geometry.Point([22.951893210411072,39.35932487749404]).buffer(50),{'ID':'A'})
# #f2 = ee.Feature(ee.Geometry.Point([22.947140336036682,39.36547976654773]).buffer(50),{'ID':'B'})
# #fc = ee.FeatureCollection([volos_rough])

# #data from sentinel-2 surface reflectance

# s2_Class= (ee.ImageCollection("COPERNICUS/S2_SR")
#    .filterBounds(final_fc)
#    .filterDate(startDate,endDate)
#    .maskClouds()
#    .scaleAndOffset()
#    .spectralIndices(['EVI','NDVI','NDBI','UI','BLFEI','IBI']))
# print('done')
# #select some bands
# #N = s2.select('B8')
# #R = s2.select('B4')
# #B = s2.select('B2')
# #G = s2.select('B3')

# #generate time series over poi, get spectral indices(awsome index) 
# s2ts_class = s2_Class.getTimeSeriesByRegion(ee.Reducer.mean(),
#                               geometry = final_fc ,
#                               bands = ['NDVI','NDBI','UI','IBI'],
#                               scale = 10,
#                               bestEffort = True,
#                               maxPixels = 1e13,
#                               dateFormat = 'YYYYMMdd',
#                               tileScale = 2)
# start_time = time.monotonic()

# #use geemap to generate a pandas dataframe from the time series(contains the ts for the selected indices)
# s2df_class_till= geemap.ee_to_pandas(s2ts_class)
# end_time = time.monotonic()
# print(timedelta(seconds=end_time - start_time))
# s2df_class_till[s2df_class == -9999] = np.nan # we do that to generate nan values when we don't have data
# s2df_class_till['date'] = pd.to_datetime(s2df_class_till['date'],infer_datetime_format = True)


# # In[213]:


# import eemont #improved iteration of ee api

# # construct a feature collection using two topologies with a radius of 50meters each, they probably overlap
# # this was improved later, where I added hand-labeled locations(abandoned/not abandoned buildings)
# #f1 = ee.Feature(ee.Geometry.Point([22.951893210411072,39.35932487749404]).buffer(50),{'ID':'A'})
# #f2 = ee.Feature(ee.Geometry.Point([22.947140336036682,39.36547976654773]).buffer(50),{'ID':'B'})
# #fc = ee.FeatureCollection([volos_rough])

# #data from sentinel-2 surface reflectance

# s2_uk_Class= (ee.ImageCollection("COPERNICUS/S2_SR")
#    .filterBounds(vacant_uk_fc)
#    .filterDate(startDate,endDate)
#    .maskClouds()
#    #.scaleAndOffset()
#    .spectralIndices(['EVI','NDVI','NDBI','UI','BLFEI','IBI']))

# #select some bands
# #N = s2.select('B8')
# #R = s2.select('B4')
# #B = s2.select('B2')
# #G = s2.select('B3')

# #generate time series over poi, get spectral indices(awsome index) 
# s2ts_uk_class = s2_uk_Class.getTimeSeriesByRegion(ee.Reducer.mean(),
#                               geometry = vacant_uk_fc ,
#                               bands = ['NDVI','NDBI','UI','IBI'],
#                               scale = 10,
#                               bestEffort = True,
#                               maxPixels = 1e13,
#                               dateFormat = 'YYYYMMdd',
#                               tileScale = 2)
# start_time = time.monotonic()

# #use geemap to generate a pandas dataframe from the time series(contains the ts for the selected indices)
# s2df_uk_class= geemap.ee_to_pandas(s2ts_uk_class)
# end_time = time.monotonic()
# print(timedelta(seconds=end_time - start_time))
# s2df_uk_class[s2df_uk_class == -9999] = np.nan # we do that to generate nan values when we don't have data
# s2df_uk_class['date'] = pd.to_datetime(s2df_uk_class['date'],infer_datetime_format = True)


# # In[220]:


# # for now this fc is limited to 100 entries
# vacant_philly_buildings_ph_fc.size().getInfo()


# # In[216]:




# # construct a feature collection using two topologies with a radius of 50meters each, they probably overlap
# # this was improved later, where I added hand-labeled locations(abandoned/not abandoned buildings)
# #f1 = ee.Feature(ee.Geometry.Point([22.951893210411072,39.35932487749404]).buffer(50),{'ID':'A'})
# #f2 = ee.Feature(ee.Geometry.Point([22.947140336036682,39.36547976654773]).buffer(50),{'ID':'B'})
# #fc = ee.FeatureCollection([volos_rough])

# #data from sentinel-2 surface reflectance

# s2_philly_bldgs_Class= (ee.ImageCollection("COPERNICUS/S2_SR")
#    .filterBounds(vacant_philly_buildings_ph_fc)
#    .filterDate(startDate,endDate)
#    .maskClouds()
#    .scaleAndOffset()
#    .spectralIndices(['EVI','NDVI','NDBI','UI','BLFEI','IBI']))

# #select some bands
# #N = s2.select('B8')
# #R = s2.select('B4')
# #B = s2.select('B2')
# #G = s2.select('B3')

# #generate time series over poi, get spectral indices(awsome index) 
# s2ts_philly_bldgs_class = s2_philly_bldgs_Class.getTimeSeriesByRegion(ee.Reducer.mean(),
#                               geometry = vacant_philly_buildings_ph_fc ,
#                               bands = ['NDVI','NDBI','UI','IBI'],
#                               scale = 10,
#                               bestEffort = True,
#                               maxPixels = 1e13,
#                               dateFormat = 'YYYYMMdd',
#                               tileScale = 2)
# start_time = time.monotonic()

# #use geemap to generate a pandas dataframe from the time series(contains the ts for the selected indices)
# s2df_philly_bldgs_class= geemap.ee_to_pandas(s2ts_philly_bldgs_class)
# end_time = time.monotonic()
# print(timedelta(seconds=end_time - start_time))
# s2df_philly_bldgs_class[s2df_philly_bldgs_class == -9999] = np.nan # we do that to generate nan values when we don't have data
# s2df_philly_bldgs_class['date'] = pd.to_datetime(s2df_philly_bldgs_class['date'],infer_datetime_format = True)


# # In[234]:


# #not_abandoned_collection


# # construct a feature collection using two topologies with a radius of 50meters each, they probably overlap
# # this was improved later, where I added hand-labeled locations(abandoned/not abandoned buildings)
# #f1 = ee.Feature(ee.Geometry.Point([22.951893210411072,39.35932487749404]).buffer(50),{'ID':'A'})
# #f2 = ee.Feature(ee.Geometry.Point([22.947140336036682,39.36547976654773]).buffer(50),{'ID':'B'})
# #fc = ee.FeatureCollection([volos_rough])

# #data from sentinel-2 surface reflectance

# s2_philly_bldgs_Class= (ee.ImageCollection("COPERNICUS/S2_SR")
#    .filterBounds(not_abandoned_collection)
#    .filterDate(startDate,endDate)
#    .maskClouds()
#    .scaleAndOffset()
#    .spectralIndices(['EVI','NDVI','NDBI','UI','BLFEI','IBI']))

# #select some bands
# #N = s2.select('B8')
# #R = s2.select('B4')
# #B = s2.select('B2')
# #G = s2.select('B3')

# #generate time series over poi, get spectral indices(awsome index) 
# s2ts_not_abad = s2_philly_bldgs_Class.getTimeSeriesByRegion(ee.Reducer.mean(),
#                               geometry = not_abandoned_collection ,
#                               bands = ['NDVI','NDBI','UI','IBI'],
#                               scale = 10,
#                               bestEffort = True,
#                               maxPixels = 1e13,
#                               dateFormat = 'YYYYMMdd',
#                               tileScale = 2)
# start_time = time.monotonic()

# #use geemap to generate a pandas dataframe from the time series(contains the ts for the selected indices)
# s2df_not_abad= geemap.ee_to_pandas(s2ts_not_abad)
# end_time = time.monotonic()
# print(timedelta(seconds=end_time - start_time))
# s2df_not_abad[s2df_not_abad == -9999] = np.nan # we do that to generate nan values when we don't have data
# s2df_not_abad['date'] = pd.to_datetime(s2df_not_abad['date'],infer_datetime_format = True)


# # In[192]:


# filled_sentinel_class= pd.DataFrame()
# filled_sentinel_class['date'] = s2df_class['date']
# #filled_sentinel['EVI'] = s2_df['EVI'].fillna(s2_df['EVI'].mean())
# filled_sentinel_class['NDVI'] = s2df_class['NDVI'].fillna(s2df_class['NDVI'].mean())
# filled_sentinel_class['IBI'] = s2df_class['IBI'].fillna(s2df_class['IBI'].mean())
# filled_sentinel_class['NDBI'] = s2df_class['NDBI'].fillna(s2df_class['NDBI'].mean())
# #filled_sentinel['BLFEI'] = s2_df['BLFEI'].fillna(s2_df['BLFEI'].mean())
# filled_sentinel_class['UI'] = s2df_class['UI'].fillna(s2df_class['UI'].mean())


# # In[225]:


# filled_sentinel_class.to_csv('./data/csvs/filled_sentinel_final_class.csv',index=False)


# # In[214]:


# filled_sentinel_uk_class= pd.DataFrame()
# filled_sentinel_uk_class['date'] = s2df_uk_class['date']
# #filled_sentinel['EVI'] = s2_df['EVI'].fillna(s2_df['EVI'].mean())
# filled_sentinel_uk_class['NDVI'] = s2df_uk_class['NDVI'].fillna(s2df_uk_class['NDVI'].mean())
# filled_sentinel_uk_class['IBI'] = s2df_uk_class['IBI'].fillna(s2df_class['IBI'].mean())
# filled_sentinel_uk_class['NDBI'] = s2df_uk_class['NDBI'].fillna(s2df_uk_class['NDBI'].mean())
# #filled_sentinel['BLFEI'] = s2_df['BLFEI'].fillna(s2_df['BLFEI'].mean())
# filled_sentinel_uk_class['UI'] = s2df_uk_class['UI'].fillna(s2df_uk_class['UI'].mean())


# # In[224]:


# filled_sentinel_uk_class.to_csv('./data/csvs/filled_sentinel_uk_class.csv',index=False)


# # In[221]:


# # fillna with me s2df_philly_bldgs_class
# filled_sentinel_philly_bldgs_class= pd.DataFrame()
# filled_sentinel_philly_bldgs_class['date'] = s2df_philly_bldgs_class['date']
# #filled_sentinel['EVI'] = s2_df['EVI'].fillna(s2_df['EVI'].mean())
# filled_sentinel_philly_bldgs_class['NDVI'] = s2df_philly_bldgs_class['NDVI'].fillna(s2df_philly_bldgs_class['NDVI'].mean())
# filled_sentinel_philly_bldgs_class['IBI'] = s2df_philly_bldgs_class['IBI'].fillna(s2df_philly_bldgs_class['IBI'].mean())
# filled_sentinel_philly_bldgs_class['NDBI'] = s2df_philly_bldgs_class['NDBI'].fillna(s2df_philly_bldgs_class['NDBI'].mean())
# #filled_sentinel['BLFEI'] = s2_df['BLFEI'].fillna(s2_df['BLFEI'].mean())
# filled_sentinel_philly_bldgs_class['UI'] = s2df_philly_bldgs_class['UI'].fillna(s2df_philly_bldgs_class['UI'].mean())


# # In[223]:


# filled_sentinel_philly_bldgs_class.to_csv('./data/csvs/filled_sentinel_philly_bldgs_class.csv',index=False)


# # In[233]:


# not_abandoned_collection.size().getInfo()


# # In[235]:


# filled_s2_not_abad= pd.DataFrame()
# filled_s2_not_abad['date'] = s2df_not_abad['date']
# #filled_sentinel['EVI'] = s2_df['EVI'].fillna(s2_df['EVI'].mean())
# filled_s2_not_abad['NDVI'] = s2df_not_abad['NDVI'].fillna(s2df_not_abad['NDVI'].mean())
# filled_s2_not_abad['IBI'] = s2df_not_abad['IBI'].fillna(s2df_not_abad['IBI'].mean())
# filled_s2_not_abad['NDBI'] = s2df_not_abad['NDBI'].fillna(s2df_not_abad['NDBI'].mean())
# #filled_sentinel['BLFEI'] = s2_df['BLFEI'].fillna(s2_df['BLFEI'].mean())
# filled_s2_not_abad['UI'] = s2df_not_abad['UI'].fillna(s2df_not_abad['UI'].mean())


# # In[236]:


# filled_s2_not_abad.to_csv('./data/csvs/filled_s2_not_abad.csv',index=False)


# # In[239]:


# #get times series of average radiance from viirs dnb monthly composites 
# viirs_class = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG").filterDate(startDate,endDate).select('avg_rad')

# viirsts_not_abandoned_class = viirs_class.getTimeSeriesByRegion(ee.Reducer.mean(),
#                               geometry = not_abandoned_collection,
#                               scale = 30,
#                               bestEffort = True,
#                               maxPixels = 2e9,
#                               dateFormat = 'YYYYMMdd',
#                               tileScale = 2)
# start_time = time.monotonic()

# viirsdf_not_abandoned_class = geemap.ee_to_pandas(viirsts_not_abandoned_class)
# end_time = time.monotonic()
# print(timedelta(seconds=end_time - start_time))
# viirsdf_not_abandoned_class['date'] = pd.to_datetime(viirsdf_not_abandoned_class['date'],infer_datetime_format = True)


# # In[240]:


# viirsdf_not_abandoned_class.to_csv('./data/csvs/viirsdf_not_abandoned_class.csv',index=False)


# # In[241]:


# #run a test random poi

# # construct a feature collection using two topologies with a radius of 50meters each, they probably overlap
# # this was improved later, where I added hand-labeled locations(abandoned/not abandoned buildings)
# #f1 = ee.Feature(ee.Geometry.Point([22.951893210411072,39.35932487749404]).buffer(50),{'ID':'A'})
# #f2 = ee.Feature(ee.Geometry.Point([22.947140336036682,39.36547976654773]).buffer(50),{'ID':'B'})
# #fc = ee.FeatureCollection([volos_rough])

# #data from sentinel-2 surface reflectance

# s2_test_oik= (ee.ImageCollection("COPERNICUS/S2_SR")
#    .filterBounds(poi_oikonomaki)
#    .filterDate(startDate,endDate)
#    .maskClouds()
#    .scaleAndOffset()
#    .spectralIndices(['EVI','NDVI','NDBI','UI','BLFEI','IBI']))

# #select some bands
# #N = s2.select('B8')
# #R = s2.select('B4')
# #B = s2.select('B2')
# #G = s2.select('B3')

# #generate time series over poi, get spectral indices(awsome index) 
# s2ts_test_oik = s2_test_oik.getTimeSeriesByRegion(ee.Reducer.mean(),
#                               geometry = poi_oikonomaki ,
#                               bands = ['NDVI','NDBI','UI','IBI'],
#                               scale = 10,
#                               bestEffort = True,
#                               maxPixels = 1e13,
#                               dateFormat = 'YYYYMMdd',
#                               tileScale = 2)
# start_time = time.monotonic()

# #use geemap to generate a pandas dataframe from the time series(contains the ts for the selected indices)
# s2df_test_oik= geemap.ee_to_pandas(s2ts_test_oik)
# end_time = time.monotonic()
# print(timedelta(seconds=end_time - start_time))
# s2df_test_oik[s2df_test_oik == -9999] = np.nan # we do that to generate nan values when we don't have data
# s2df_test_oik['date'] = pd.to_datetime(s2df_test_oik['date'],infer_datetime_format = True)


# # In[242]:


# oik = pd.DataFrame()
# filled_s2_not_abad['date'] = s2df_test_oik['date']
# #filled_sentinel['EVI'] = s2_df['EVI'].fillna(s2_df['EVI'].mean())
# oik['NDVI'] = s2df_test_oik['NDVI'].fillna(s2df_test_oik['NDVI'].mean())
# oik['IBI'] = s2df_test_oik['IBI'].fillna(s2df_test_oik['IBI'].mean())
# oik['NDBI'] = s2df_test_oik['NDBI'].fillna(s2df_test_oik['NDBI'].mean())
# #filled_sentinel['BLFEI'] = s2_df['BLFEI'].fillna(s2_df['BLFEI'].mean())
# oik['UI'] = s2df_test_oik['UI'].fillna(s2df_test_oik['UI'].mean())


# # In[244]:


# # test oik
# #get times series of average radiance from viirs dnb monthly composites 
# viirs_class = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG").filterDate(startDate,endDate).select('avg_rad')

# viirs_oik = viirs_class.getTimeSeriesByRegion(ee.Reducer.mean(),
#                               geometry = poi_oikonomaki,
#                               scale = 30,
#                               bestEffort = True,
#                               maxPixels = 2e9,
#                               dateFormat = 'YYYYMMdd',
#                               tileScale = 2)
# start_time = time.monotonic()

# viirs_oik_df = geemap.ee_to_pandas(viirs_oik)
# end_time = time.monotonic()
# print(timedelta(seconds=end_time - start_time))
# viirs_oik_df['date'] = pd.to_datetime(viirs_oik_df['date'],infer_datetime_format = True)


# # In[243]:


# oik.to_csv('./data/csvs/oik.csv',index=False)


# # In[245]:


# viirs_oik_df.to_csv('./data/csvs/viirs_oik.csv',index=False)


# # In[26]:


# #vacant_bld_pol_fc = geemap.geopandas_to_ee(vacant_bld_pol)


# # In[358]:


# # The above are supposed to be vacant lots/land/buildings from the state of Philladelphia

# # We are going to create a feature collelction based on them for abandoned buildings


# vacant_bldg.geometry[:1000]polygonlist = list()
# for i in range(len(vacant_bldg)):
#     polygonlist.append(vacant_bldg['geometry'].loc[i])polygonlistf1 = ee.Feature(f,{'ID':'5_0','Class':'Abandoned','ClassPallete':'E5FFCC'})
# import geopandas as gpd
# import numpy as np
# from functools import reduce
# from geopandas import GeoDataFrame
# from shapely.geometry import Point,Polygon

# def make_points(gdf):
#     g = [i for i in gdf.geometry]
#     features=[]
#     for i in range(len(g)):
#         g = [i for i in gdf.geometry]
#         x,y = g[i].exterior.coords.xy
#         cords = np.dstack((x,y)).tolist()
#         double_list = reduce(lambda x,y: x+y, cords)
#         single_list = reduce(lambda x,y: x+y, double_list)

#         g=ee.Geometry.Polygon(single_list)
#         feature = ee.Feature(g)
#         features.append(feature)
#         #print("done")
#         ee_object = ee.FeatureCollection(features)
#     return ee_object
# #mycoordslist = [poly.exterior.coords for poly in list(geom)]
# points_features_collections = make_points(vacant_bldg[:1000])
# # In[441]:




# list(polygonlist[1].exterior.coords)f = ee.Geometry.Polygon(list(polygonlist[1].exterior.coords))
# f from shapely.geometry import mapping
# #sh_polygon = Polygon(((0,0), (1,1), (0,1)))
# mapping(vacant_bldg['geometry'].loc[1])for i in range(len(polygonlist)):
#     f[i] = ee.Geometry.Polygon(list(polygonlist[1].exterior.coords))geemap.js_snippet_to_py(
#     js, add_new_cell=True, import_ee=True, import_geemap=True, show_map=True
# )# plot the country on a map
# if poly.geom_type=='MultiPolygon':
#     # `poly` is a list of geometries
#     ax.add_geometries(poly, crs=ccrs.PlateCarree(), facecolor=rgba, edgecolor='none', zorder=1)
# elif poly.geom_type=='Polygon': 
#     # `poly` is a geometry
#     # Austria, Belgium
#     # Plot it `green` for checking purposes
#     ax.add_geometries([poly], crs=ccrs.PlateCarree(), facecolor="green", edgecolor='none', zorder=1)
# else:
#     pass  #do not plot the geometry#gdf = gdf[gdf.geom_type == 'MultiPolygon']



# for i in range(len(vacant_bldg[:1000])):
#     fc = ee.FeatureCollection(vacant_bldg.geometry.loc[i],{'Class':'Not Abandoned'})
# #f2 = ee.Feature(ee.Geometry.Point([22.947140336036682,39.36547976654773]).buffer(50),{'ID':'B'})
# #abandoned = ee.FeatureCollection([f4,f5,f6,f8])
# #not_abandoned =  ee.FeatureCollection([f1,f2,f3,f7])
# # In[28]:


# new = vacant_bld_pol_fc

# new.reduceColumns({
#     reducer:ee.Reducer.max(),
#     selectprs: ['geometry']
# })
# # In[42]:


# list_fc = ee.List(vacant_buildings_ph_fc)


# # In[54]:


# import eemont #improved iteration of ee api

# # construct a feature collection using two topologies with a radius of 50meters each, they probably overlap
# # this was improved later, where I added hand-labeled locations(abandoned/not abandoned buildings)
# #f1 = ee.Feature(ee.Geometry.Point([22.951893210411072,39.35932487749404]).buffer(50),{'ID':'A'})
# #f2 = ee.Feature(ee.Geometry.Point([22.947140336036682,39.36547976654773]).buffer(50),{'ID':'B'})
# #fc = ee.FeatureCollection([volos_rough])

# #data from sentinel-2 surface reflectance

# s2 = (ee.ImageCollection("COPERNICUS/S2_SR")
#    .filterBounds(vacant_buildings_ph_fc)
#    .filterDate(startDate,endDate)
#    .maskClouds()
#    #.scaleAndOffset()
#    .spectralIndices(['EVI','NDVI','NDBI','UI','BLFEI']))

# #select some bands
# #N = s2.select('B8')
# #R = s2.select('B4')
# #B = s2.select('B2')
# #G = s2.select('B3')

# #generate time series over poi, get spectral indices(awsome index) 
# s2_ts = s2.getTimeSeriesByRegion(ee.Reducer.mean(),
#                               geometry = vacant_buildings_ph_fc ,
#                               bands = ['EVI','NDVI','NDBI','UI','BLFEI'],
#                               scale = 10,
#                               bestEffort = True,
#                               maxPixels = 1e13,
#                               dateFormat = 'YYYYMMdd',
#                               tileScale = 2)

# #use geemap to generate a pandas dataframe from the time series(contains the ts for the selected indices)
# s2_df= geemap.ee_to_pandas(s2_ts)

# s2_df[s2_df == -9999] = np.nan # we do that to generate nan values when we don't have data
# s2_df['date'] = pd.to_datetime(s2_df['date'],infer_datetime_format = True)


# # In[55]:


# s2_df


# # In[ ]:


# #https://urbanspatial.github.io/PublicPolicyAnalytics/geospatial-risk-modeling-predictive-policing.html


# # In[ ]:





# # In[ ]:





# # In[ ]:





# # In[5]:


# Map1 = geemap.Map()
# Map1.add_basemap('HYBRID')
# dynamic_world_s2 = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
# # Set the region of interest by simply drawing a polygon on the map
# region = Map1.user_roi
# if region is None:
#     region = ee.Geometry.BBox(-89.7088, 42.9006, -89.0647, 43.2167)

# Map1.centerObject(region)

# # Set the date range
# start_date = '2021-01-01'
# end_date = '2022-01-01'

# # Create a Sentinel-2 image composite
# #image = geemap.dynamic_world_s2(region, start_date, end_date)
# #vis_params = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}
# #Map1.addLayer(image, vis_params, 'Sentinel-2 image')

# # Create Dynamic World land cover composite
# landcover = geemap.dynamic_world(region, start_date, end_date, return_type='hillshade')
# Map1.addLayer(landcover, {}, 'Land Cover')

# # Add legend to the map
# Map1.add_legend(title="Dynamic World Land Cover", builtin_legend='Dynamic_World')
# Map1


# # In[ ]:


















# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# import rasterio
# import geopandas as gpd
# import requests
# import json
# import datetime

# from pprint import pprint
# from rasterio.features import Window
# from rasterio.windows import bounds
# from shapely.geometry import MultiPolygon, box
# from PIL import Image
# from rasterio.features import Window
# from subprocess import call
# from IPython import display
# import seaborn as sns



# import statsmodels.api as sm
# from scipy import stats
# import plotly.offline as py
# import plotly.graph_objs as go

# from ipyleaflet import GeoJSON
# from geemap import geojson_to_ee, ee_to_geojson


# from sklearn.model_selection import train_test_split
# #from tslearn.clustering import TimeSeriesKMeans, KShape
# #from tslearn.datasets import CachedDatasets
# #from tslearn.preprocessing import TimeSeriesScalerMeanVariance, \
# #    TimeSeriesResampler


# import streamlit as st
# import leafmap.foliumap as leafmap

# st.set_page_config(layout="wide")

# st.sidebar.title("About")
# st.sidebar.info(
#     """
#     Web App URL: <https://geospatial.streamlitapp.com>
#     GitHub repository: <https://github.com/giswqs/streamlit-geospatial>
#     """
# )

# st.sidebar.title("Contact")
# st.sidebar.info(
#     """
#     Qiusheng Wu: <https://wetlands.io>
#     [GitHub](https://github.com/giswqs) | [Twitter](https://twitter.com/giswqs) | [YouTube](https://www.youtube.com/c/QiushengWu) | [LinkedIn](https://www.linkedin.com/in/qiushengwu)
#     """
# )

# st.title("Business Intelligence Toolkit")

# col1, col2 = st.columns([4, 1])

# turbo_volos_filled = pd.read_csv('./data/turbo_volos_df.csv')
# viirs_turbo =pd.read_csv('./data/viirs_turbo_df.csv')

# # Author: Romain Tavenard
# # License: BSD 3 clause










# #######################  LOAD DATA #################################














# ########################  CLUSTERING #############################
# def clustering():
#     seed = 0
#     numpy.random.seed(seed)
#     X_train, x_test = train_test_split(turbo_volos_filled.drop('date',axis=1),test_size=0.3,random_state=42)


#     #numpy.random.shuffle(X_train)
#     # Keep only 50 time series
#     X_train = TimeSeriesScalerMeanVariance().fit_transform(X_train[:50])
#     # Make time series shorter
#     X_train = TimeSeriesResampler(sz=40).fit_transform(X_train)
#     sz = X_train.shape[1]

#     # Euclidean k-means
#     print("Euclidean k-means")
#     km = TimeSeriesKMeans(n_clusters=3, verbose=True, random_state=seed)
#     y_pred = km.fit_predict(X_train)

#     plt.figure()
#     for yi in range(3):
#         plt.subplot(3, 3, yi + 1)
#         for xx in X_train[y_pred == yi]:
#             plt.plot(xx.ravel(), "k-", alpha=.2)
#         plt.plot(km.cluster_centers_[yi].ravel(), "r-")
#         plt.xlim(0, sz)
#         plt.ylim(-4, 4)
#         plt.text(0.55, 0.85,'Cluster %d' % (yi + 1),
#                  transform=plt.gca().transAxes)
#         if yi == 1:
#             plt.title("Euclidean $k$-means")

#     # DBA-k-means
#     print("DBA k-means")
#     dba_km = TimeSeriesKMeans(n_clusters=3,
#                               n_init=2,
#                               metric="dtw",
#                               verbose=True,
#                               max_iter_barycenter=10,
#                               random_state=seed)
#     y_pred = dba_km.fit_predict(X_train)

#     for yi in range(3):
#         plt.subplot(3, 3, 4 + yi)
#         for xx in X_train[y_pred == yi]:
#             plt.plot(xx.ravel(), "k-", alpha=.2)
#         plt.plot(dba_km.cluster_centers_[yi].ravel(), "r-")
#         plt.xlim(0, sz)
#         plt.ylim(-4, 4)
#         plt.text(0.55, 0.85,'Cluster %d' % (yi + 1),
#                  transform=plt.gca().transAxes)
#         if yi == 1:
#             plt.title("DBA $k$-means")

#     # Soft-DTW-k-means
#     print("Soft-DTW k-means")
#     sdtw_km = TimeSeriesKMeans(n_clusters=3,
#                                metric="softdtw",
#                                metric_params={"gamma": .01},
#                                verbose=True,
#                                random_state=seed)
#     y_pred = sdtw_km.fit_predict(X_train)

#     for yi in range(3):
#         plt.subplot(3, 3, 7 + yi)
#         for xx in X_train[y_pred == yi]:
#             plt.plot(xx.ravel(), "k-", alpha=.2)
#         plt.plot(sdtw_km.cluster_centers_[yi].ravel(), "r-")
#         plt.xlim(0, sz)
#         plt.ylim(-4, 4)
#         plt.text(0.55, 0.85,'Cluster %d' % (yi + 1),
#                  transform=plt.gca().transAxes)
#         if yi == 1:
#             plt.title("Soft-DTW $k$-means")

#     plt.tight_layout()
#     plt.show()


# def kshape():
# # Author: Romain Tavenard
# # License: BSD 3 clause



#     seed = 0
#     numpy.random.seed(seed)

#     # Keep first 3 classes and 50 first time series


#     numpy.random.shuffle(X_train)
#     # For this method to operate properly, prior scaling is required
#     X_train = TimeSeriesScalerMeanVariance().fit_transform(X_train)
#     sz = X_train.shape[1]

#     # kShape clustering
#     ks = KShape(n_clusters=2, verbose=True, random_state=seed)
#     y_pred = ks.fit_predict(X_train)

#     plt.figure()
#     for yi in range(2):
#         plt.subplot(3, 1, 1 + yi)
#         for xx in X_train[y_pred == yi]:
#             plt.plot(xx.ravel(), "k-", alpha=.2)
#         plt.plot(ks.cluster_centers_[yi].ravel(), "r-")
#         plt.xlim(0, sz)
#         plt.ylim(-4, 4)
#         plt.title("Cluster %d" % (yi + 1))

#     plt.tight_layout()
#     plt.show()