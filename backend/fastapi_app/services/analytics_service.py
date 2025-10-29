import re
import pandas as pd
from pathlib import Path
from shared.utils.logger import get_logger

log = get_logger("AnalyticsService")

LOG_FILE = Path("logs/resimhub.log")


class AnalyticsService:
    reward_pattern = re.compile(
        r"Experiment (\d+)\s*\| Epoch (\d+)/(\d+)\s*\| Reward:\s*([\d\.]+)"
    )
    final_accuracy_pattern = re.compile(
        r"Experiment (\d+) completed.*Env=(\w+).*Algo=(\w+).*Final Accuracy: ([\d\.]+)"
    )

    @staticmethod
    def parse_experiment_logs(experiment_id: int):
        """
        Parse logs for a specific experiment.
        Returns a DataFrame with columns: ['epoch', 'reward'].
        """
        if not LOG_FILE.exists():
            log.warning(f"No log file found at {LOG_FILE}")
            return pd.DataFrame(columns=["epoch", "reward"])

        rewards = []
        with LOG_FILE.open("r") as f:
            for line in f:
                match = AnalyticsService.reward_pattern.search(line)
                if match:
                    exp_id = int(match.group(1))
                    epoch = int(match.group(2))
                    reward = float(match.group(4))
                    if exp_id == experiment_id:
                        rewards.append((epoch, reward))

        df = pd.DataFrame(rewards, columns=["epoch", "reward"])
        return df

    @staticmethod
    def compute_statistics(df: pd.DataFrame):
        """
        Compute mean, std, and convergence epoch.
        Convergence is defined as first epoch >= mean + std.
        """
        if df.empty:
            return {"mean_reward": None, "std_reward": None, "convergence_epoch": None}

        mean_reward = df["reward"].mean()
        std_reward = df["reward"].std()
        convergence_epoch = df[df["reward"] >= mean_reward + std_reward]["epoch"].min()
        if pd.isna(convergence_epoch):
            convergence_epoch = df["epoch"].max()

        return {
            "mean_reward": round(mean_reward, 2),
            "std_reward": round(std_reward, 2),
            "convergence_epoch": int(convergence_epoch),
        }

    @staticmethod
    def list_recent_experiments(limit: int = 5):
        """
        Detect all experiments in logs, return most recent `limit` experiments.
        """
        if not LOG_FILE.exists():
            return []

        experiments = {}
        with LOG_FILE.open("r") as f:
            for line in f:
                match = AnalyticsService.final_accuracy_pattern.search(line)
                if match:
                    exp_id = int(match.group(1))
                    env = match.group(2)
                    algo = match.group(3)
                    final_accuracy = float(match.group(4))
                    experiments[exp_id] = {
                        "experiment_id": exp_id,
                        "env": env,
                        "algorithm": algo,
                        "final_accuracy": final_accuracy,
                    }

        # Return the most recent experiments sorted by ID
        recent_experiments = sorted(experiments.values(), key=lambda x: x["experiment_id"], reverse=True)
        return recent_experiments[:limit]

@staticmethod
def list_recent_experiments(limit: int = 5):
    """
    Returns a summary of recent experiments detected in the log file
    with experiment_id, env, algorithm, and last reward/final accuracy.
    """
    from pathlib import Path
    import re
    import pandas as pd

    LOG_FILE = Path("logs/resimhub.log")
    if not LOG_FILE.exists():
        return []

    # Pattern to capture completed experiments
    pattern = re.compile(
        r"Experiment (\d+) completed.*Env=(\w+).*Algo=(\w+).*Final Accuracy: ([\d\.]+)"
    )
    records = []
    with LOG_FILE.open("r") as f:
        for line in f:
            match = pattern.search(line)
            if match:
                exp_id = int(match.group(1))
                env = match.group(2)
                algo = match.group(3)
                final_accuracy = float(match.group(4))
                records.append({
                    "experiment_id": exp_id,
                    "env": env,
                    "algorithm": algo,
                    "final_accuracy": final_accuracy
                })

    df = pd.DataFrame(records)
    df = df.drop_duplicates(subset=["experiment_id"], keep="last").tail(limit)
    return df.to_dict(orient="records")
