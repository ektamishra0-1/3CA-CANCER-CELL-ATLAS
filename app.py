import streamlit as st
import pandas as pd
import networkx as nx
import pickle
from pyvis.network import Network
import streamlit.components.v1 as components



# PAGE CONFIG

st.set_page_config(
    page_title="3CA Data Explorer",
    page_icon="🧬",
    layout="wide"
)

st.title("🧬 3CA Cancer Cell Atlas Explorer")

st.caption(
    "Knowledge-graph powered discovery across "
    "single-cell cancer datasets"
)


# LOAD DATA


@st.cache_data
def load_samples():
    return pd.read_csv("unified_samples.csv")


@st.cache_data
def load_cell_links():
    return pd.read_csv("cell_type_links.csv")


@st.cache_resource
def load_graph():
    with open("knowledge_graph.pkl", "rb") as f:
        return pickle.load(f)


samples = load_samples()
cell_links = load_cell_links()
G = load_graph()


st.success(
    f"Knowledge graph loaded: "
    f"{G.number_of_nodes():,} nodes · "
    f"{G.number_of_edges():,} relationships"
)



# SIDEBAR SEARCH


st.sidebar.header("🔎 Search datasets")

text_search = st.sidebar.text_input(
    "Search datasets",
    placeholder="e.g. HNSCC, breast, tumor..."
)

regions = ["Any"] + sorted(
    samples["region"]
    .dropna()
    .unique()
    .tolist()
)

cell_types = ["Any"] + sorted(
    cell_links["cell_type_clean"]
    .dropna()
    .unique()
    .tolist()
)

conditions = ["Any"] + sorted(
    samples["condition"]
    .dropna()
    .unique()
    .tolist()
)

technologies = ["Any"] + sorted(
    samples["technology_clean"]
    .dropna()
    .unique()
    .tolist()
)

sites = ["Any"] + sorted(
    samples["site_clean"]
    .dropna()
    .unique()
    .tolist()
)


selected_region = st.sidebar.selectbox(
    "Region",
    regions,
    key="region_filter"
)

selected_cell = st.sidebar.selectbox(
    "Cell type",
    cell_types,
    key="cell_filter"
)

selected_condition = st.sidebar.selectbox(
    "Cancer / condition",
    conditions,
    key="condition_filter"
)

selected_technology = st.sidebar.selectbox(
    "Technology",
    technologies,
    key="technology_filter"
)

selected_site = st.sidebar.selectbox(
    "Site",
    sites,
    key="site_filter"
)


search_button = st.sidebar.button(
    "🔍 Search",
    type="primary"
)



# SEARCH FUNCTION


def search_datasets():

    result = samples.copy()

    
    # TEXT SEARCH
    

    if text_search.strip():

        query = text_search.strip().lower()

        searchable = (
            result
            .fillna("")
            .astype(str)
            .apply(lambda col: col.str.lower())
        )

        mask = searchable.apply(
            lambda row: row.str.contains(
                query,
                regex=False
            ).any(),
            axis=1
        )

        result = result[mask]

    
    # REGION
    

    if selected_region != "Any":

        result = result[
            result["region"] == selected_region
        ]

    
    # CONDITION
    

    if selected_condition != "Any":

        result = result[
            result["condition"] == selected_condition
        ]

    
    # TECHNOLOGY
    

    if selected_technology != "Any":

        result = result[
            result["technology_clean"] == selected_technology
        ]

    
    # SITE
    

    if selected_site != "Any":

        result = result[
            result["site_clean"] == selected_site
        ]

    
    # CELL TYPE
    

    if selected_cell != "Any":

        matching_samples = set(
            cell_links.loc[
                cell_links["cell_type_clean"] == selected_cell,
                "sample_id"
            ]
        )

        result = result[
            result["sample_id"].isin(
                matching_samples
            )
        ]

    return result



# DISCOVERY INSIGHTS


def show_discovery_insights(result, cell_links):

    st.subheader("🧠 Discovery Insights")

    if result.empty:

        st.info(
            "No matching datasets available for insight generation."
        )

        return

    # --------------------------------------------------------
    # BASIC COUNTS
    # --------------------------------------------------------

    study_count = result["study"].nunique()

    sample_count = len(result)

    condition_count = (
        result["condition"]
        .dropna()
        .nunique()
    )

    region_count = (
        result["region"]
        .dropna()
        .nunique()
    )

    technology_count = (
        result["technology_clean"]
        .dropna()
        .nunique()
    )

    # --------------------------------------------------------
    # MATCHING CELL TYPES
    # --------------------------------------------------------

    matching_ids = set(
        result["sample_id"]
    )

    matching_cells = cell_links[
        cell_links["sample_id"].isin(
            matching_ids
        )
    ]

    cell_type_count = (
        matching_cells["cell_type_clean"]
        .dropna()
        .nunique()
    )

    # --------------------------------------------------------
    # TOP METRICS
    # --------------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Studies",
            f"{study_count:,}"
        )

    with c2:

        st.metric(
            "Samples",
            f"{sample_count:,}"
        )

    with c3:

        st.metric(
            "Conditions",
            f"{condition_count:,}"
        )

    with c4:

        st.metric(
            "Cell types",
            f"{cell_type_count:,}"
        )

    # --------------------------------------------------------
    # TECHNOLOGIES
    # --------------------------------------------------------

    technologies = (
        result["technology_clean"]
        .dropna()
        .value_counts()
    )

    # --------------------------------------------------------
    # CONDITIONS
    # --------------------------------------------------------

    conditions = (
        result["condition"]
        .dropna()
        .value_counts()
    )

    # --------------------------------------------------------
    # REGIONS
    # --------------------------------------------------------

    regions = (
        result["region"]
        .dropna()
        .value_counts()
    )

    # --------------------------------------------------------
    # CELL TYPES
    # --------------------------------------------------------

    cell_types = (
        matching_cells["cell_type_clean"]
        .dropna()
        .value_counts()
    )

    # ========================================================
    # RELATIONSHIP TABLES
    # ========================================================

    col1, col2 = st.columns(2)

    # --------------------------------------------------------
    # TECHNOLOGY TABLE
    # --------------------------------------------------------

    with col1:

        st.markdown(
            "**🧪 Experimental technologies**"
        )

        if technologies.empty:

            st.write(
                "No technology metadata available."
            )

        else:

            technology_df = (
                technologies
                .rename("Samples")
                .reset_index()
                .rename(columns={"index": "Technology"})
            )

            st.dataframe(
                technology_df,
                use_container_width=True,
                hide_index=True
            )

    # --------------------------------------------------------
    # CONDITION TABLE
    # --------------------------------------------------------

    with col2:

        st.markdown(
            "**🧬 Cancer / condition distribution**"
        )

        if conditions.empty:

            st.write(
                "No condition metadata available."
            )

        else:

            condition_df = (
                conditions
                .rename("Samples")
                .reset_index()
                .rename(columns={"index": "Condition"})
                .head(15)
            )

            st.dataframe(
                condition_df,
                use_container_width=True,
                hide_index=True
            )

    # ========================================================
    # CELL TYPES
    # ========================================================

    st.markdown(
        "**🔬 Cell types represented in matching datasets**"
    )

    if cell_types.empty:

        st.write(
            "No cell-type relationships available."
        )

    else:

        cell_type_df = (
            cell_types
            .rename("Relationships")
            .reset_index()
            .rename(columns={"index": "Cell type"})
            .head(15)
        )

        st.dataframe(
            cell_type_df,
            use_container_width=True,
            hide_index=True
        )

    # ========================================================
    # REGIONAL DISTRIBUTION
    # ========================================================

    if not regions.empty:

        st.markdown(
            "**🌍 Regional distribution**"
        )

        region_df = (
            regions
            .rename("Samples")
            .reset_index()
            .rename(columns={"index": "Region"})
        )

        st.dataframe(
            region_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# GRAPH EXPLORER
# ============================================================

def show_sample_graph(
    G,
    selected_sample=None
):

    if selected_sample is None:

        st.warning(
            "Please select a sample."
        )

        return

    selected_sample = str(
        selected_sample
    )

    # --------------------------------------------------------
    # SAMPLE NODE
    # --------------------------------------------------------

    if selected_sample.startswith(
        "sample::"
    ):

        sample_node = selected_sample

    else:

        sample_node = (
            f"sample::{selected_sample}"
        )

    if sample_node not in G:

        st.warning(
            f"Sample not found in knowledge graph: "
            f"{selected_sample}"
        )

        return

    # --------------------------------------------------------
    # GET SAMPLE NEIGHBORS
    # --------------------------------------------------------

    neighbors = list(
        G.neighbors(
            sample_node
        )
    )

    # --------------------------------------------------------
    # CREATE NETWORK
    # --------------------------------------------------------

    net = Network(
        height="700px",
        width="100%",
        bgcolor="#0e1117",
        font_color="white",
        directed=False
    )

    # --------------------------------------------------------
    # PHYSICS
    # --------------------------------------------------------

    net.barnes_hut(
        gravity=-6500,
        central_gravity=0.25,
        spring_length=230,
        spring_strength=0.04,
        damping=0.09
    )

    # --------------------------------------------------------
    # NODE STYLES
    # --------------------------------------------------------

    styles = {

        "Sample": {
            "color": "#ff4b4b",
            "shape": "dot",
            "size": 42
        },

        "Cluster": {
            "color": "#ffffff",
            "shape": "hexagon",
            "size": 30
        },

        "Study": {
            "color": "#4dabf7",
            "shape": "box",
            "size": 22
        },

        "Region": {
            "color": "#51cf66",
            "shape": "box",
            "size": 22
        },

        "Condition": {
            "color": "#ffd43b",
            "shape": "ellipse",
            "size": 21
        },

        "Technology": {
            "color": "#cc5de8",
            "shape": "diamond",
            "size": 21
        },

        "Site": {
            "color": "#20c997",
            "shape": "ellipse",
            "size": 19
        },

        "Patient": {
            "color": "#ff922b",
            "shape": "dot",
            "size": 19
        },

        "CellType": {
            "color": "#74c0fc",
            "shape": "dot",
            "size": 15
        }
    }

    # --------------------------------------------------------
    # ADD SAMPLE
    # --------------------------------------------------------

    sample_name = G.nodes[
        sample_node
    ].get(
        "name",
        selected_sample
    )

    net.add_node(
        sample_node,
        label=sample_name,
        title=(
            "<b>Sample</b><br>"
            f"{sample_name}"
        ),
        color="#ff4b4b",
        shape="dot",
        size=45,
        font={
            "size": 21,
            "bold": True,
            "color": "white"
        }
    )

    # --------------------------------------------------------
    # SEMANTIC CLUSTERS
    # --------------------------------------------------------

    clusters = {

        "Study": [],

        "Biological Context": [],

        "Experimental Method": [],

        "Patient / Site": [],

        "Cell Types": []
    }

    # --------------------------------------------------------
    # CLASSIFY NEIGHBORS
    # --------------------------------------------------------

    for node in neighbors:

        node_data = G.nodes[node]

        node_type = node_data.get(
            "type",
            "Unknown"
        )

        if node_type == "Study":

            clusters[
                "Study"
            ].append(node)

        elif node_type in {
            "Region",
            "Condition"
        }:

            clusters[
                "Biological Context"
            ].append(node)

        elif node_type == "Technology":

            clusters[
                "Experimental Method"
            ].append(node)

        elif node_type in {
            "Patient",
            "Site"
        }:

            clusters[
                "Patient / Site"
            ].append(node)

        elif node_type == "CellType":

            clusters[
                "Cell Types"
            ].append(node)

    # --------------------------------------------------------
    # CLUSTER COLORS
    # --------------------------------------------------------

    cluster_colors = {

        "Study": "#4dabf7",

        "Biological Context": "#ffd43b",

        "Experimental Method": "#cc5de8",

        "Patient / Site": "#ff922b",

        "Cell Types": "#74c0fc"
    }

    # --------------------------------------------------------
    # CREATE CLUSTER NODES
    # --------------------------------------------------------

    cluster_nodes = {}

    for cluster_name, cluster_members in clusters.items():

        if not cluster_members:
            continue

        cluster_id = (
            f"cluster::{selected_sample}::"
            f"{cluster_name}"
        )

        cluster_nodes[
            cluster_name
        ] = cluster_id

        # ----------------------------------------------------
        # LABEL
        # ----------------------------------------------------

        if cluster_name == "Cell Types":

            label = (
                f"🧬 Cell Types\n"
                f"{len(cluster_members)}"
            )

        elif cluster_name == "Biological Context":

            label = (
                f"🧪 Biology\n"
                f"{len(cluster_members)}"
            )

        elif cluster_name == "Experimental Method":

            label = (
                f"⚙ Method\n"
                f"{len(cluster_members)}"
            )

        elif cluster_name == "Patient / Site":

            label = (
                f"👤 Patient / Site\n"
                f"{len(cluster_members)}"
            )

        else:

            label = (
                f"📚 Study\n"
                f"{len(cluster_members)}"
            )

        # ----------------------------------------------------
        # CLUSTER NODE
        # ----------------------------------------------------

        net.add_node(
            cluster_id,
            label=label,
            title=(
                f"<b>{cluster_name}</b><br>"
                f"{len(cluster_members)} "
                f"connected entities"
            ),
            color=cluster_colors[
                cluster_name
            ],
            shape="hexagon",
            size=30,
            font={
                "size": 15,
                "bold": True,
                "color": "white"
            }
        )

        # ----------------------------------------------------
        # SAMPLE → CLUSTER
        # ----------------------------------------------------

        net.add_edge(
            sample_node,
            cluster_id,
            label=cluster_name,
            title=(
                f"Sample → {cluster_name}"
            ),
            width=3,
            color="#868e96",
            font={
                "size": 11,
                "color": "#ced4da"
            }
        )

    # --------------------------------------------------------
    # ADD CLUSTER MEMBERS
    # --------------------------------------------------------

    for cluster_name, cluster_members in clusters.items():

        if cluster_name not in cluster_nodes:
            continue

        cluster_id = cluster_nodes[
            cluster_name
        ]

        for node in cluster_members:

            data = G.nodes[node]

            node_type = data.get(
                "type",
                "Unknown"
            )

            name = data.get(
                "name",
                node
            )

            style = styles.get(
                node_type,
                {
                    "color": "#adb5bd",
                    "shape": "dot",
                    "size": 15
                }
            )

            # ------------------------------------------------
            # ENTITY NODE
            # ------------------------------------------------

            net.add_node(
                node,
                label=name,
                title=(
                    f"<b>{node_type}</b><br>"
                    f"{name}"
                ),
                color=style["color"],
                shape=style["shape"],
                size=style["size"],
                font={
                    "size": 12,
                    "color": "white"
                }
            )

            # ------------------------------------------------
            # CLUSTER → ENTITY
            # ------------------------------------------------

            net.add_edge(
                cluster_id,
                node,
                label="",
                title=(
                    f"{cluster_name}: {name}"
                ),
                width=1.2,
                color="#495057"
            )

    # --------------------------------------------------------
    # GRAPH OPTIONS
    # --------------------------------------------------------

    net.set_options(
        """
        {
          "interaction": {
            "hover": true,
            "navigationButtons": true,
            "keyboard": true,
            "dragNodes": true,
            "zoomView": true
          },

          "physics": {
            "enabled": true,
            "solver": "forceAtlas2Based",

            "forceAtlas2Based": {
              "gravitationalConstant": -80,
              "centralGravity": 0.015,
              "springLength": 150,
              "springConstant": 0.08,
              "damping": 0.4,
              "avoidOverlap": 1
            },

            "stabilization": {
              "enabled": true,
              "iterations": 400
            }
          },

          "edges": {
            "smooth": {
              "enabled": true,
              "type": "dynamic"
            }
          },

          "nodes": {
            "borderWidth": 1,
            "shadow": true
          }
        }
        """
    )

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    st.markdown(
        "### 🔬 Semantic Knowledge Graph"
    )

    st.caption(
        f"Exploring `{selected_sample}` through "
        f"biological, experimental and dataset relationships"
    )

    # --------------------------------------------------------
    # LEGEND
    # --------------------------------------------------------

    st.markdown(
        """
        🔴 **Sample** &nbsp;&nbsp;
        🔷 **Study** &nbsp;&nbsp;
        🟡 **Biological Context** &nbsp;&nbsp;
        🟣 **Experimental Method** &nbsp;&nbsp;
        🟠 **Patient / Site** &nbsp;&nbsp;
        🔵 **Cell Types**
        """
    )

    # --------------------------------------------------------
    # RENDER GRAPH
    # --------------------------------------------------------

    html = net.generate_html()

    components.html(
        html,
        height=720,
        scrolling=False
    )

    # --------------------------------------------------------
    # SEMANTIC SUMMARY
    # --------------------------------------------------------

    st.markdown(
        "### 🧠 Semantic Relationship Summary"
    )

    summary = []

    for cluster_name, members in clusters.items():

        if members:

            summary.append(
                {
                    "Knowledge Group": cluster_name,
                    "Connected Entities": len(members)
                }
            )

    summary_df = pd.DataFrame(
        summary
    )

    if not summary_df.empty:

        st.dataframe(
            summary_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# SEARCH RESULTS
# ============================================================

if search_button:

    results = search_datasets()

    st.session_state[
        "search_results"
    ] = results


# ============================================================
# DISPLAY SEARCH RESULTS
# ============================================================

if "search_results" in st.session_state:

    results = st.session_state[
        "search_results"
    ]

    st.subheader(
        "🔬 Search Results"
    )

    # --------------------------------------------------------
    # RESULT METRICS
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Matching samples",
            f"{len(results):,}"
        )

    with col2:

        st.metric(
            "Studies",
            f"{results['study'].nunique():,}"
        )

    with col3:

        st.metric(
            "Regions",
            f"{results['region'].nunique():,}"
        )

    # --------------------------------------------------------
    # EMPTY RESULTS
    # --------------------------------------------------------

    if len(results) == 0:

        st.warning(
            "No datasets matched your filters."
        )

    else:

        # ====================================================
        # RESULT TABLE
        # ====================================================

        display_columns = [

            "study",

            "region",

            "sample",

            "condition",

            "technology_clean",

            "site_clean",

            "n_cells"
        ]

        display_columns = [

            c
            for c in display_columns
            if c in results.columns
        ]

        st.dataframe(
            results[
                display_columns
            ],
            use_container_width=True,
            hide_index=True
        )

        # ====================================================
        # DISCOVERY INSIGHTS
        # ====================================================

        show_discovery_insights(
            results,
            cell_links
        )

        # ====================================================
        # SELECT SAMPLE
        # ====================================================

        st.subheader(
            "🔬 Explore a dataset"
        )

        sample_options = (
            results["sample_id"]
            .dropna()
            .astype(str)
            .tolist()
        )

        # ----------------------------------------------------
        # DEFAULT SAMPLE
        # ----------------------------------------------------

        if (
            "selected_sample"
            not in st.session_state
            or
            st.session_state[
                "selected_sample"
            ]
            not in sample_options
        ):

            st.session_state[
                "selected_sample"
            ] = sample_options[0]

        # ----------------------------------------------------
        # SAMPLE SELECTOR
        # ----------------------------------------------------

        selected_sample = st.selectbox(
            "Select a sample to explore its relationships",
            sample_options,
            index=sample_options.index(
                st.session_state[
                    "selected_sample"
                ]
            ),
            key="sample_selector"
        )

        # ----------------------------------------------------
        # SAVE SAMPLE
        # ----------------------------------------------------

        st.session_state[
            "selected_sample"
        ] = selected_sample

        # ====================================================
        # SHOW GRAPH
        # ====================================================

        show_sample_graph(
            G,
            selected_sample
        )

        # ====================================================
        # DATASET SUMMARY
        # ====================================================

        st.subheader(
            "📊 Dataset Summary"
        )

        left, right = st.columns(2)

        # ----------------------------------------------------
        # REGION SUMMARY
        # ----------------------------------------------------

        with left:

            st.write(
                "**Samples by region**"
            )

            region_counts = (
                results["region"]
                .value_counts()
                .rename_axis("Region")
                .reset_index(
                    name="Samples"
                )
            )

            st.dataframe(
                region_counts,
                use_container_width=True,
                hide_index=True
            )

        # ----------------------------------------------------
        # STUDY SUMMARY
        # ----------------------------------------------------

        with right:

            st.write(
                "**Samples by study**"
            )

            study_counts = (
                results["study"]
                .value_counts()
                .rename_axis("Study")
                .reset_index(
                    name="Samples"
                )
            )

            st.dataframe(
                study_counts,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# DEFAULT DASHBOARD
# ============================================================

else:

    st.subheader(
        "📚 Atlas Overview"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Studies",
            f"{samples['study'].nunique():,}"
        )

    with col2:

        st.metric(
            "Samples",
            f"{len(samples):,}"
        )

    with col3:

        st.metric(
            "Cell types",
            f"{cell_links['cell_type_clean'].nunique():,}"
        )

    with col4:

        st.metric(
            "Regions",
            f"{samples['region'].nunique():,}"
        )

    st.info(
        "Use the filters on the left to discover "
        "datasets through the knowledge graph."
    )