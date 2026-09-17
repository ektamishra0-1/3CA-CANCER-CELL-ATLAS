from pathlib import Path
import tarfile
import pandas as pd


DATA_DIR = Path("data")
OUTPUT_DIR = Path(".")


def get_study_info(archive_path):
    archive_path = Path(archive_path)

    study = archive_path.name.replace("Meta-data_", "").replace(".tar.gz", "")
    region = archive_path.parent.name.replace("Meta-data_", "")

    return study, region


def get_member(tar, filename):
    for member in tar.getmembers():
        if member.name.endswith(filename):
            return member

    raise FileNotFoundError(f"{filename} not found in archive")


def load_samples_from_archive(archive_path):
    study, region = get_study_info(archive_path)

    with tarfile.open(archive_path, "r:gz") as tar:

        sample_member = get_member(tar, "Samples.csv")

        samples = pd.read_csv(
            tar.extractfile(sample_member)
        )

    samples["study"] = study
    samples["region"] = region

    return samples


def load_cell_type_links_from_archive(archive_path):
    study, region = get_study_info(archive_path)

    links = []

    with tarfile.open(archive_path, "r:gz") as tar:

        cell_member = get_member(tar, "Cells.csv")

        cell_file = tar.extractfile(cell_member)

        for chunk in pd.read_csv(
            cell_file,
            usecols=["sample", "cell_type"],
            chunksize=100_000
        ):

            chunk = chunk.dropna(
                subset=["sample", "cell_type"]
            )

            chunk["study"] = study
            chunk["region"] = region

            links.append(
                chunk[
                    ["study", "region", "sample", "cell_type"]
                ].drop_duplicates()
            )

    if not links:
        return pd.DataFrame(
            columns=[
                "study",
                "region",
                "sample",
                "cell_type"
            ]
        )

    return pd.concat(
        links,
        ignore_index=True
    ).drop_duplicates()


def normalize_samples(samples):

    samples = samples.copy()

    # Unique sample identifier across studies
    samples["sample_id"] = (
        samples["study"].astype(str)
        + "::"
        + samples["sample"].astype(str)
    )

    # Canonical technology field
    if "technology" in samples.columns:
        samples["technology_clean"] = (
            samples["technology"]
            .astype("string")
            .str.strip()
            .str.lower()
        )

        samples["technology_clean"] = (
            samples["technology_clean"]
            .replace({
                "10x": "10x",
                "10x genomics": "10x",
                "10x chromium": "10x",
                "smart-seq2": "SmartSeq2",
                "smartseq2": "SmartSeq2",
            })
        )

    else:
        samples["technology_clean"] = pd.NA

    # Canonical site
    if "site" in samples.columns:
        samples["site_clean"] = (
            samples["site"]
            .astype("string")
            .str.strip()
            .str.lower()
        )
    else:
        samples["site_clean"] = pd.NA

    # Canonical cancer / condition
    if "cancer_type" in samples.columns:
        samples["condition"] = (
            samples["cancer_type"]
            .astype("string")
            .str.strip()
        )
    else:
        samples["condition"] = pd.NA

    # Canonical patient ID
    if "patient" in samples.columns:
        patient_values = (
            samples["patient"]
            .astype("string")
            .str.strip()
        )

        samples["patient_id"] = (
            samples["study"].astype(str)
            + "::"
            + patient_values
        )
    else:
        samples["patient_id"] = pd.NA

    return samples


def normalize_cell_links(links):

    links = links.copy()

    links["cell_type_clean"] = (
        links["cell_type"]
        .astype("string")
        .str.strip()
        .str.replace("_", " ", regex=False)
    )

    links["sample_id"] = (
        links["study"].astype(str)
        + "::"
        + links["sample"].astype(str)
    )

    return links.drop_duplicates(
        subset=[
            "study",
            "region",
            "sample",
            "cell_type_clean"
        ]
    )


def build_dataset():
    archives = sorted(DATA_DIR.rglob("*.tar.gz"))

    print("=" * 60)
    print("3CA DATASET LOADER")
    print("=" * 60)
    print(f"Found {len(archives)} archives")

    if not archives:
        raise RuntimeError("No .tar.gz archives found inside data/")

    all_samples = []
    all_cell_links = []

    sample_success = 0
    cell_success = 0
    errors = []

    for i, archive in enumerate(archives, start=1):
        print(f"[{i}/{len(archives)}] {archive.name}")

        # -------------------------
        # 1. Always try Samples.csv
        # -------------------------
        try:
            samples = load_samples_from_archive(archive)
            all_samples.append(samples)
            sample_success += 1
            print(f"    samples={len(samples):,}")
        except Exception as e:
            errors.append((archive.name, "Samples.csv", str(e)))
            print(f"    Samples ERROR: {e}")
            continue

        # -------------------------
        # 2. Independently try Cells.csv
        # -------------------------
        try:
            cell_links = load_cell_type_links_from_archive(archive)

            if not cell_links.empty:
                all_cell_links.append(cell_links)
                cell_success += 1

            print(f"    cell-type-links={len(cell_links):,}")

        except Exception as e:
            errors.append((archive.name, "Cells.csv", str(e)))
            print(f"    Cells ERROR: {e}")

    # -------------------------
    # Combine samples
    # -------------------------
    print("\nCombining sample metadata...")

    if not all_samples:
        raise RuntimeError("No Samples.csv files could be loaded.")

    samples = pd.concat(
        all_samples,
        ignore_index=True,
        sort=False
    )

    print("Normalizing samples...")
    samples = normalize_samples(samples)

    # -------------------------
    # Combine cell relationships
    # -------------------------
    print("\nCombining cell-type relationships...")

    if all_cell_links:
        cell_links = pd.concat(
            all_cell_links,
            ignore_index=True
        )
        cell_links = normalize_cell_links(cell_links)
    else:
        cell_links = pd.DataFrame(
            columns=[
                "study",
                "region",
                "sample",
                "cell_type",
                "cell_type_clean",
                "sample_id"
            ]
        )

    # -------------------------
    # Save
    # -------------------------
    samples.to_csv(
        OUTPUT_DIR / "unified_samples.csv",
        index=False
    )

    cell_links.to_csv(
        OUTPUT_DIR / "cell_type_links.csv",
        index=False
    )

    # -------------------------
    # Summary
    # -------------------------
    print("\n" + "=" * 60)
    print("BUILD COMPLETE")
    print("=" * 60)

    print(f"Archives found:       {len(archives):,}")
    print(f"Sample files loaded:  {sample_success:,}")
    print(f"Cell files loaded:    {cell_success:,}")
    print(f"Studies:              {samples['study'].nunique():,}")
    print(f"Regions:              {samples['region'].nunique():,}")
    print(f"Samples:              {len(samples):,}")
    print(f"Cell types:           {cell_links['cell_type_clean'].nunique():,}")
    print(f"Relationships:        {len(cell_links):,}")

    print("\nSaved:")
    print("  unified_samples.csv")
    print("  cell_type_links.csv")

    print("\nSamples by region:")
    print(samples["region"].value_counts().to_string())

    # -------------------------
    # Errors
    # -------------------------
    if errors:
        print("\n" + "=" * 60)
        print("FILES WITH ISSUES")
        print("=" * 60)

        for filename, filetype, error in errors:
            print(f"- {filename} [{filetype}]: {error}")

        print(f"\nTotal issues: {len(errors)}")

if __name__ == "__main__":
    build_dataset()