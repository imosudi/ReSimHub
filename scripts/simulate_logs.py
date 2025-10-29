import random
from datetime import datetime
from pathlib import Path
import time

LOG_FILE = Path("logs/resimhub.log")
LOG_FILE.parent.mkdir(exist_ok=True)

def simulate_experiment(experiment_id, env_name, algo, total_epochs=5):
    """
    Simulate per-epoch training logs for an experiment.
    """
    with LOG_FILE.open("a") as f:
        for epoch in range(1, total_epochs + 1):
            reward = round(random.uniform(180, 250), 2)
            timestamp = datetime.utcnow().isoformat()
            log_line = (
                f"{timestamp} | INFO  | Training job for Experiment {experiment_id} "
                f"| Epoch {epoch}/{total_epochs} | Reward: {reward}\n"
            )
            f.write(log_line)

        # Final summary line
        final_accuracy = round(random.uniform(0.8, 0.99), 4)
        timestamp = datetime.utcnow().isoformat()
        f.write(
            f"{timestamp} | INFO  | Training job for Experiment {experiment_id} completed "
            f"| Env={env_name} | Algo={algo} | Final Accuracy: {final_accuracy}\n"
        )


def simulate_multiple_experiments(num_experiments=5):
    envs = ["CartPole-v1", "LunarLander-v2", "MountainCar-v0"]
    algos = ["DQN", "PPO", "A2C"]

    for exp_id in range(1, num_experiments + 1):
        env = random.choice(envs)
        algo = random.choice(algos)
        simulate_experiment(exp_id, env, algo)



NUM_EXPERIMENTS = 3
EPOCHS_PER_EXPERIMENT = 5

with LOG_FILE.open("a") as f:
    for exp_id in range(1, NUM_EXPERIMENTS + 1):
        env = random.choice(["CartPole", "LunarLander", "MountainCar"])
        algo = random.choice(["DQN", "PPO", "A2C"])
        for epoch in range(1, EPOCHS_PER_EXPERIMENT + 1):
            reward = round(random.uniform(180, 250), 2)
            f.write(f"{datetime.utcnow()} | INFO | Training | Experiment {exp_id} | Epoch {epoch}/{EPOCHS_PER_EXPERIMENT} | Reward: {reward}\n")
        final_acc = round(random.uniform(0.8, 0.99), 4)
        f.write(f"{datetime.utcnow()} | INFO | Training | Experiment {exp_id} completed | Env={env} | Algo={algo} | Final Accuracy: {final_acc}\n")

print(f"Simulated {NUM_EXPERIMENTS} experiments in {LOG_FILE}")


experiments = [
    {"id": 1, "env": "MountainCar", "algo": "A2C", "epochs": 5},
    {"id": 2, "env": "CartPole", "algo": "DQN", "epochs": 5},
    {"id": 3, "env": "LunarLander", "algo": "PPO", "epochs": 5},
]

with LOG_FILE.open("a") as f:
    for exp in experiments:
        for epoch in range(1, exp["epochs"] + 1):
            reward = round(random.uniform(180, 250), 2)
            timestamp = datetime.utcnow().isoformat()
            line = f"{timestamp} | INFO | SimLogger | Experiment {exp['id']} | Epoch {epoch}/{exp['epochs']} | Reward: {reward}\n"
            f.write(line)
            time.sleep(0.05)  # simulate time passing
        # Final experiment summary
        final_accuracy = round(random.uniform(0.8, 0.99), 4)
        line = f"{datetime.utcnow().isoformat()} | INFO | SimLogger | Training job for Experiment {exp['id']} completed | Env={exp['env']} | Algo={exp['algo']} | Final Accuracy: {final_accuracy}\n"
        f.write(line)

#if __name__ == "__main__":
if 1 == 2:
    simulate_multiple_experiments(num_experiments=10)
    print(f"Simulation complete. Logs written to {LOG_FILE}")
