from environment import GameEnvironment
from stable_baselines3 import PPO

env = GameEnvironment('127.0.0.1', 8008, ['A', 'D', 'Ctrl'], 100)

model = PPO('CnnPolicy', env, verbose=1)

model.learn(total_timesteps=int(2e5), progress_bar=True)

model.save('models/PPO_'+'Galaga')