import streamlit as st
import leafmap.foliumap as leafmap

st.set_page_config(layout="wide")

markdown = """
Web App URL: <https://template.streamlitapp.com>
GitHub Repository: <https://github.com/giswqs/streamlit-multipage-template>
"""

st.sidebar.title("About")
st.sidebar.info(markdown)
logo = "https://i.imgur.com/UbOXYAU.png"
st.sidebar.image(logo)

st.title("Heatmap")

with st.expander("See source code"):
    with st.echo():
        #filepath = "https://raw.githubusercontent.com/giswqs/leafmap/master/examples/data/us_cities.csv"
        filepath = ":https://raw.githubusercontent.com/ckyriakos/thesis_front_end/master/data/greek_cities.csv" # EDW THA VALW TO CSV POU MAS ENDIAFEREI ONTWS
        m = leafmap.Map(center=[ 22.9507, -39.3666], zoom=4, tiles="stamentoner")
        m.add_heatmap(
            filepath,
            latitude="lat",
            longitude="lng",
            value="population",
            name="Heat map",
            radius=20,
        )
m.to_streamlit(height=700)
