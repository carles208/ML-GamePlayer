from environment import GameEnvironment
from stable_baselines3 import PPO
from gymnasium.wrappers import FlattenObservation

env = GameEnvironment('127.0.0.1', 65432, 'C:/Users/Fran/Desktop/Emulator', 'Galaga', ['left', 'right', 'action'], 100)
env = FlattenObservation(env)

model = PPO('MlpPolicy', env, verbose=1)

model.learn(total_timesteps=int(2e5), progress_bar=True)

model.save('models/PPO_'+'Galaga')