"""Process varios files in the application folder for additional information"""
import json

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .discover import walk_path


def is_package_file(f: Path, sap_code: str, name_pattern: str) -> bool:
    """Determine if the file is the right application JSON file
    :param f (Path): json file path
    :param sap_code (str): Adobe SAP code for product being processed
    :param name_pattern (str): json filename patter to test"""
    return sap_code in str(f) and name_pattern in str(f)


def find_application_json(install_pkg: Path, sap_code: str,
                          name_pattern: str = "Application.json") -> Optional[Union[Path, List, None]]:
    """Find a matching Application.json based on SAP code
    :param installer_pkg (Path): installer pkg to process json from
    :param sap_code (str): Adobe SAP code for product being processed
    :paaram name_pattern (str): json filename pattern to test"""
    app_json_file = [f for f in walk_path(install_pkg, ".json") if is_package_file(f, sap_code, name_pattern)]
    app_json_file = app_json_file[0] if len(app_json_file) == 1 or len(app_json_file) > 1 else app_json_file
    result = app_json_file or None

    return result


def read_json_file(json_file: Path) -> Dict[Any, Any]:
    """Parse the application JSON file into native dict
    :param json_file (Path): JSON file to parse"""
    with open(json_file, 'r') as f:
        return json.load(f)
