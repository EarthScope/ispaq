import os


def get_package_versions():
    """Parse ispaq-conda-install.txt to get package versions."""
    versions = {}
    conda_file = os.path.join(
        os.path.dirname(__file__), "..", "ispaq-conda-install.txt"
    )

    with open(conda_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and "=" in line:
                package, version = line.split("=", 1)
                versions[package] = version

    return versions


def get_required_versions():
    """Get required versions for key packages."""
    all_versions = get_package_versions()
    return {
        "obspy": all_versions.get("obspy", "1.4.2"),
        "r": all_versions.get("r-base", "4.4.3"),
        "pandas": all_versions.get("pandas", "2.2.3"),
        "rpy2": all_versions.get("rpy2", "3.2.2"),
        "numpy": all_versions.get("numpy", "2.3.2"),
    }
