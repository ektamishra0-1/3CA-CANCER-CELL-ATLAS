import pickle
import pandas as pd
import networkx as nx


SAMPLES_FILE = "unified_samples.csv"
CELL_LINKS_FILE = "cell_type_links.csv"
GRAPH_FILE = "knowledge_graph.pkl"


def clean_value(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


def add_node(G, node_id, node_type, **attributes):
    attributes["type"] = node_type
    G.add_node(node_id, **attributes)


def add_relationship(G, source, target, relationship):
    G.add_edge(
        source,
        target,
        relationship=relationship
    )


def build_graph():

    print("Loading unified metadata...")

    samples = pd.read_csv(SAMPLES_FILE)
    cell_links = pd.read_csv(CELL_LINKS_FILE)

    G = nx.Graph()

    # --------------------------------------------------
    # STUDIES
    # --------------------------------------------------

    print("Adding study nodes...")

    for study in samples["study"].dropna().unique():

        study = clean_value(study)

        if study is None:
            continue

        add_node(
            G,
            f"study::{study}",
            "Study",
            name=study
        )

    # --------------------------------------------------
    # REGIONS
    # --------------------------------------------------

    print("Adding region nodes...")

    for region in samples["region"].dropna().unique():

        region = clean_value(region)

        if region is None:
            continue

        add_node(
            G,
            f"region::{region}",
            "Region",
            name=region
        )

    # --------------------------------------------------
    # CONDITIONS / CANCER TYPES
    # --------------------------------------------------

    print("Adding condition nodes...")

    for condition in samples["condition"].dropna().unique():

        condition = clean_value(condition)

        if condition is None:
            continue

        add_node(
            G,
            f"condition::{condition}",
            "Condition",
            name=condition
        )

    # --------------------------------------------------
    # TECHNOLOGIES
    # --------------------------------------------------

    print("Adding technology nodes...")

    for technology in samples["technology_clean"].dropna().unique():

        technology = clean_value(technology)

        if technology is None:
            continue

        add_node(
            G,
            f"technology::{technology}",
            "Technology",
            name=technology
        )

    # --------------------------------------------------
    # SITES
    # --------------------------------------------------

    print("Adding site nodes...")

    for site in samples["site_clean"].dropna().unique():

        site = clean_value(site)

        if site is None:
            continue

        add_node(
            G,
            f"site::{site}",
            "Site",
            name=site
        )

    # --------------------------------------------------
    # PATIENTS
    # --------------------------------------------------

    print("Adding patient nodes...")

    if "patient_id" in samples.columns:

        for patient in samples["patient_id"].dropna().unique():

            patient = clean_value(patient)

            if patient is None:
                continue

            add_node(
                G,
                f"patient::{patient}",
                "Patient",
                name=patient
            )

    # --------------------------------------------------
    # CELL TYPES
    # --------------------------------------------------

    print("Adding cell-type nodes...")

    for cell_type in cell_links["cell_type_clean"].dropna().unique():

        cell_type = clean_value(cell_type)

        if cell_type is None:
            continue

        add_node(
            G,
            f"celltype::{cell_type}",
            "CellType",
            name=cell_type
        )

    # --------------------------------------------------
    # SAMPLE NODES + RELATIONSHIPS
    # --------------------------------------------------

    print("Adding samples and relationships...")

    for _, row in samples.iterrows():

        sample_id = clean_value(row["sample_id"])

        if sample_id is None:
            continue

        study = clean_value(row["study"])
        region = clean_value(row["region"])
        condition = clean_value(row.get("condition"))
        technology = clean_value(row.get("technology_clean"))
        site = clean_value(row.get("site_clean"))
        patient = clean_value(row.get("patient_id"))

        # Sample node

        add_node(
            G,
            f"sample::{sample_id}",
            "Sample",
            name=sample_id,
            study=study,
            region=region
        )

        # Study -> Sample

        if study:
            add_relationship(
                G,
                f"study::{study}",
                f"sample::{sample_id}",
                "contains"
            )

        # Region -> Sample

        if region:
            add_relationship(
                G,
                f"region::{region}",
                f"sample::{sample_id}",
                "contains_sample"
            )

        # Condition -> Sample

        if condition:
            add_relationship(
                G,
                f"condition::{condition}",
                f"sample::{sample_id}",
                "has_condition"
            )

        # Technology -> Sample

        if technology:
            add_relationship(
                G,
                f"technology::{technology}",
                f"sample::{sample_id}",
                "generated_with"
            )

        # Site -> Sample

        if site:
            add_relationship(
                G,
                f"site::{site}",
                f"sample::{sample_id}",
                "from_site"
            )

        # Patient -> Sample

        if patient:
            add_relationship(
                G,
                f"patient::{patient}",
                f"sample::{sample_id}",
                "has_sample"
            )

    # --------------------------------------------------
    # SAMPLE -> CELL TYPE
    # --------------------------------------------------

    print("Adding sample-cell-type relationships...")

    for _, row in cell_links.iterrows():

        sample_id = clean_value(row["sample_id"])
        cell_type = clean_value(row["cell_type_clean"])

        if sample_id is None or cell_type is None:
            continue

        sample_node = f"sample::{sample_id}"
        cell_node = f"celltype::{cell_type}"

        if sample_node not in G:
            continue

        if cell_node not in G:
            continue

        add_relationship(
            G,
            sample_node,
            cell_node,
            "contains_cell_type"
        )

    return G


if __name__ == "__main__":

    G = build_graph()

    print("\n" + "=" * 60)
    print("KNOWLEDGE GRAPH COMPLETE")
    print("=" * 60)

    print("Nodes:", G.number_of_nodes())
    print("Edges:", G.number_of_edges())

    print("\nNode types:")

    node_types = pd.Series(
        [
            data.get("type")
            for _, data in G.nodes(data=True)
        ]
    )

    print(node_types.value_counts().to_string())

    print("\nRelationship types:")

    relationship_types = pd.Series(
        [
            data.get("relationship")
            for _, _, data in G.edges(data=True)
        ]
    )

    print(
        relationship_types
        .value_counts()
        .to_string()
    )

    with open(GRAPH_FILE, "wb") as f:
        pickle.dump(G, f)

    print(f"\nSaved: {GRAPH_FILE}")