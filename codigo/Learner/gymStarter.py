from environment import GameEnvironment
from stable_baselines3 import PPO
from gymnasium.wrappers import FlattenObservation

emulatorDir = 'C:/Users/franc/Desktop/Emulator'
game = 'Galaga'

env = GameEnvironment('127.0.0.1', 65432, emulatorDir, game, ['left', 'right', 'action'], 50)
env = FlattenObservation(env)

model = PPO('MlpPolicy', env, verbose=1, device='cpu')

model.learn(total_timesteps=int(2e5), progress_bar=True)

model.save(f'models/PPO_{game}')