from app._version import get_version_info
if __name__ == "__main__":
    vi = get_version_info()
    print(f"{vi['version']} | {vi['date_utc']} | {vi['summary']}")
