import re
import pandas as pd
from datetime import datetime
from typing import List, Dict

LOG_FILE_PATH = "logs/resimhub.log"

def parse_experiment_logs(experiment_id: int) -> pd.DataFrame:
    """
    Parse resimhub.log and return a DataFrame with epoch, reward, timestamp for a given experiment_id.
    """
    pattern = re.compile(
        rf"Experiment {experiment_id} progress: (\d+)%"
    )
    
    data: List[Dict] = []
    
    try:
        with open(LOG_FILE_PATH, "r") as f:
            for line in f:
                if f"Experiment {experiment_id}" in line:
                    match = pattern.search(line)
                    if match:
                        data.append({
                            "timestamp": datetime.strptime(line[:23], "%Y-%m-%d %H:%M:%S,%f"),
                            "progress": int(match.group(1))
                        })
    except FileNotFoundError:
        return pd.DataFrame()
    
    return pd.DataFrame(data)
