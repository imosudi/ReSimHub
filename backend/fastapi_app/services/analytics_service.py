# backend/fastapi_app/services/analytics_service.py
import re
import pandas as pd
from pathlib import Path
from shared.utils.logger import get_logger

log = get_logger("AnalyticsService")

LOG_FILE = Path("logs/resimhub.log")


def _extract_reward_logs(experiment_id: int):
    """
    Parse rewards for a specific experiment from log file.
    Ignores old logs with percentage-only progress.
    Returns a list of (epoch, reward) tuples.
    """
    if not LOG_FILE.exists():
        log.warning(f"Log file not found at {LOG_FILE}")
        return []

    reward_pattern = re.compile(
        rf"Experiment {experiment_id}\s*\|\s*Epoch (\d+)/\d+\s*\|\s*Reward:\s*([\d\.]+)"
    )

    rewards = []

    with LOG_FILE.open("r") as f:
        for line in f:
            # Skip irrelevant or progress-only lines
            if "%" in line and "Reward" not in line:
                continue
            match = reward_pattern.search(line)
            if match:
                epoch = int(match.group(1))
                reward = float(match.group(2))
                rewards.append((epoch, reward))

    if not rewards:
        log.warning(f"No reward entries found for experiment {experiment_id}")

    return rewards


def compute_experiment_statistics(experiment_id: int):
    """
    Compute statistics (mean, std, convergence epoch) from log rewards.
    Returns a dictionary of analytics results.
    """
    rewards = _extract_reward_logs(experiment_id)
    if not rewards:
        return {"error": "No reward data found for experiment."}

    df = pd.DataFrame(rewards, columns=["epoch", "reward"])

    # Compute statistics
    mean_reward = round(df["reward"].mean(), 2)
    std_reward = round(df["reward"].std(), 2)

    # Define convergence as when reward stabilizes within 5% of final reward
    final_reward = df["reward"].iloc[-1]
    convergence_epoch = int(
        df[df["reward"] >= 0.95 * final_reward]["epoch"].min()
    )

    result = {
        "experiment_id": experiment_id,
        "mean_reward": mean_reward,
        "std_reward": std_reward,
        "convergence_epoch": convergence_epoch,
        "total_epochs": len(df),
    }

    log.info(
        f"Analytics computed for Experiment {experiment_id} → "
        f"Mean: {mean_reward}, Std: {std_reward}, Convergence: {convergence_epoch}"
    )

    return result


def list_recent_experiments(limit: int = 5):
    """
    Returns a summary of recent experiments detected in the log file.
    """
    if not LOG_FILE.exists():
        return {"error": "No log file found."}

    experiment_pattern = re.compile(r"Experiment (\d+).*Algo=(\w+)")
    records = []

    with LOG_FILE.open("r") as f:
        for line in f:
            match = experiment_pattern.search(line)
            if match:
                exp_id = int(match.group(1))
                algo = match.group(2)
                records.append((exp_id, algo))

    df = pd.DataFrame(records, columns=["experiment_id", "algorithm"])
    df = df.drop_duplicates(subset=["experiment_id"], keep="last").tail(limit)

    return df.to_dict(orient="records")



class AnalyticsService:
    reward_pattern = re.compile(
        r"Training job for Experiment (\d+) completed.*accuracy: (\d+\.\d+)"
    )

    @staticmethod
    def parse_experiment_logs(experiment_id: int):
        """
        Parse logs to extract rewards for the specified experiment.
        Returns a DataFrame with columns: ['epoch', 'reward'].
        """
        if not LOG_FILE.exists():
            return pd.DataFrame(columns=["epoch", "reward"])

        rewards = []
        with LOG_FILE.open("r") as f:
            for line in f:
                match = AnalyticsService.reward_pattern.search(line)
                if match:
                    exp_id = int(match.group(1))
                    reward = float(match.group(2))
                    if exp_id == experiment_id:
                        rewards.append(reward)

        df = pd.DataFrame({"reward": rewards})
        df["epoch"] = df.index + 1
        return df

    @staticmethod
    def compute_statistics(df: pd.DataFrame):
        """
        Compute mean, std, and convergence epoch.
        Convergence is defined as the first epoch where reward > mean + std.
        """
        if df.empty:
            return {"mean_reward": None, "std_reward": None, "convergence_epoch": None}

        mean_reward = df["reward"].mean()
        std_reward = df["reward"].std()
        # Convergence criterion: first epoch where reward >= mean + std
        convergence_epoch = df[df["reward"] >= mean_reward + std_reward]["epoch"].min()
        if pd.isna(convergence_epoch):
            convergence_epoch = df["epoch"].max()
        return {
            "mean_reward": round(mean_reward, 2),
            "std_reward": round(std_reward, 2),
            "convergence_epoch": int(convergence_epoch),
        }
