import json
import os
from ..ACUPDlib import path

def check_update_status() -> bool:
    res = False

    if os.path.exists(path.update_status):
        with open(path.update_status, "r") as f:
            res = json.load(f)["status"]
    
    return res