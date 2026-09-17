# 🧬 3CA Cancer Cell Atlas Explorer



🚀 **Live Demo:** 
[https://YOUR-STREAMLIT-URL.streamlit.app/](https://3ca-cancer-cell-atlas.streamlit.app/)



A knowledge-graph-powered discovery interface for exploring datasets from the **Curated Cancer Cell Atlas (3CA)**.

The prototype integrates sample-level metadata and cell-type relationships from multiple single-cell cancer datasets into a unified structure, represents relationships as a knowledge graph, and provides an interactive interface for searching datasets, generating discovery insights, and exploring biological relationships.

---

## 🎯 Problem

The 3CA contains datasets from multiple cancer studies, regions, experimental technologies, patients, sites, conditions, samples, and cell types.

When these datasets are considered independently, it can be difficult to:

- discover relevant datasets across studies
- connect samples with their biological and experimental context
- identify cell types represented across datasets
- understand relationships between samples, studies, patients, sites, and technologies
- explore the atlas through relationships rather than isolated tables

This project provides a unified discovery layer over the available dataset metadata.

---

## 💡 Solution

The system converts heterogeneous dataset metadata into:

1. **Unified tabular metadata**
2. **A knowledge graph**
3. **A search and filtering interface**
4. **Discovery summaries**
5. **An interactive semantic graph explorer**

The user can search for concepts such as:


HNSCC
breast
tumor

🏗️ Architecture

                3CA Dataset Archives
                         │
                         ▼
                  ┌─────────────┐
                  │ Data Loader │
                  └──────┬──────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        Samples.csv             Cells.csv
              │                     │
              └──────────┬──────────┘
                         ▼
                Unified Metadata
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
      Knowledge Graph          Search Layer
        (NetworkX)              (Streamlit)
             │                       │
             └───────────┬───────────┘
                         ▼
                Discovery Interface
                    │           │
                    ▼           ▼
             Insights       Graph Explorer


📊 Data Integration

The data loader processes the dataset archives and independently extracts information from Samples.csv and Cells.csv.

This is intentional because some archives contain sample metadata even when their cell metadata is missing or incomplete.

The loader:

* discovers dataset archives
* extracts sample metadata
* extracts cell-type relationships when available
* normalizes important fields
* creates unified sample identifiers
* creates unified cell-type relationships
* records files that could not be processed completely

Normalized identifiers

Samples are represented using:
study::sample
This provides a consistent identifier across the integrated datasets.

Cell-type relationships use the same sample identifier, allowing the sample metadata and cell-level metadata to be connected.

⸻

🕸️ Knowledge Graph

The knowledge graph is implemented using NetworkX.

The graph represents multiple entity types:
Sample
Patient
Site
Study
Condition
CellType
Technology
Region

Core relationships
Study ──contains──────────────► Sample

Region ──contains_sample──────► Sample

Condition ──has_condition─────► Sample

Technology ──generated_with───► Sample

Site ──from_site──────────────► Sample

Patient ──has_sample──────────► Sample

Sample ──contains_cell_type───► CellType

This allows a sample to act as a connection point between experimental, biological, clinical, and dataset-level information.

🔬 Semantic Graph Exploration

The graph explorer adds a semantic layer on top of the underlying knowledge graph.

For a selected sample, related entities are grouped into:

📚 Study

The study from which the sample originates.

🧪 Biological Context

Includes:

* Region
* Condition

⚙️ Experimental Method

Includes:

* Technology

👤 Patient / Site

Includes:

* Patient
* Site

🧬 Cell Types

Includes the cell types associated with the sample.

The underlying graph relationships remain explicit while the semantic grouping makes the graph easier to interpret visually.

⸻

🔎 Dataset Discovery

The application provides both free-text search and structured filters.

Free-text search

Users can search across dataset metadata using terms such as:
HNSCC
breast
tumor

Structured filters

Available filters include:
Region
Cell type
Cancer / condition
Technology
Site
Multiple filters can be combined to narrow the dataset space.

⸻

🧠 Discovery Insights

After a search, the system summarizes the matching dataset space.

The interface reports:

* number of studies
* number of samples
* number of conditions
* number of cell types

It also provides distributions for:

* experimental technologies
* cancer / condition
* cell types
* regions

This allows users to understand the composition of a search result rather than only viewing individual rows.

⸻

🛠️ Technology Stack
Component:
Language
Interface
Data processing
Knowledge graph
Interactive graph
Serialization
Data format

Technology:
Python
Streamlit
Pandas
NetworkX
PyVis
Python Pickle
CSV

📁 Project Structure
3CA-CANCER-CELL-ATLAS/
│
├── app.py
├── loader.py
├── build_graph.py
├── unified_samples.csv
├── cell_type_links.csv
├── knowledge_graph.pkl
├── requirements.txt
├── README.md
├── .gitignore
└── data/

Main files

loader.py

Loads and normalizes dataset metadata and creates the unified CSV files.

build_graph.py

Constructs the NetworkX knowledge graph from the unified metadata.

app.py

Runs the Streamlit discovery interface and interactive graph explorer.

unified_samples.csv

Unified sample-level metadata.

cell_type_links.csv

Relationships between samples and cell types.

knowledge_graph.pkl

Serialized NetworkX knowledge graph used by the application.

⸻

🚀 Running the Application

1. Clone the repository

git clone <REPOSITORY_URL>
cd 3CA-CANCER-CELL-ATLAS

2. Create a virtual environment

python -m venv .venv

3. Activate it

macOS / Linux:
source .venv/bin/activate

Windows:
.venv\Scripts\activate

4. Install dependencies

pip install -r requirements.txt

5. Run the application

python -m streamlit run app.py

The Streamlit interface will open in the browser.

⚙️ Rebuilding the Data

If the source archives are available under data/, the unified metadata can be regenerated using:

python loader.py

Then rebuild the knowledge graph:

python build_graph.py

The resulting files are:
unified_samples.csv
cell_type_links.csv
knowledge_graph.pkl


🧩 Design Choices

Why a knowledge graph?

A relational table is useful for filtering rows, but the central problem involves relationships between different entity types.

A graph representation makes these connections explicit and allows the interface to traverse relationships around a sample.

Why NetworkX?

NetworkX provides a lightweight graph representation suitable for a prototype and supports:

* heterogeneous node types
* explicit relationships
* graph traversal
* serialization
* integration with PyVis

Why Streamlit?

Streamlit allows the prototype to expose the data integration and graph functionality through an interactive interface without requiring a separate frontend/backend application.

Why semantic clustering?

A raw graph containing every connected node can become difficult to interpret.

Semantic groups organize related entities into meaningful categories while preserving the underlying relationships.

⸻

⚠️ Data Handling and Limitations

The source archives are not perfectly uniform.

During ingestion, some datasets were found to have:

* missing Cells.csv
* missing cell_type information
* missing sample fields
* encoding differences
* incomplete metadata

The loader therefore treats sample metadata and cell metadata independently and records processing issues instead of discarding an entire dataset when only one component is unavailable.

The current prototype focuses on metadata and cell-type relationships rather than expression matrices or full single-cell expression analysis.

⸻

🔮 Future Extensions

Potential extensions include:

1. Richer biological relationships

Add entities and relationships for:

Gene
Protein
Pathway
Mutation
Drug
Disease subtype


2. Expression-aware discovery

Connect the knowledge graph with gene-expression matrices so users can search for biological patterns in addition to metadata.

3. Cross-study comparison

Enable comparison of:

* cell-type composition
* experimental technologies
* cancer conditions
* patient cohorts

across studies.

4. Graph-based recommendations

Use graph traversal and similarity measures to surface related datasets based on shared:

* cell types
* conditions
* technologies
* regions
* study characteristics

5. Scalable graph database

For a production-scale deployment, the NetworkX prototype could be migrated to a graph database such as Neo4j or another scalable graph storage system.

⸻

📌 Prototype Status

This repository contains a working prototype demonstrating:

* heterogeneous dataset ingestion
* metadata normalization
* unified dataset representation
* knowledge-graph construction
* relationship-based exploration
* free-text dataset discovery
* structured filtering
* discovery summaries
* interactive semantic graph visualization
