VERSION = "0.3.1"


def get_current_version():
    """Get the current version from version.txt, fallback to VERSION constant."""
    import os
    try:
        with open(os.path.join(os.path.dirname(__file__), 'version.txt'), 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return VERSION