import socket
import json
import keyboard
import pygetwindow as gw
import time
import gymnasium as gym
import numpy as np

SEPARETOR = "<END>"

class GameEnvironment(gym.Env):
    def __init__(self, host, port, buttons, maxEnemies):
        super().__init__()

        # Se define el socket que se utilizará para comunicarse con el scanner
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

        # Espacio de salida de la red a partir de una lista de botones (0 representa no pulsar ninguno)
        self.buttons = buttons
        self.action_space = gym.spaces.Discrete(len(buttons)+1)

        # Espacio de observaciones basado tamaño y posción de jugador y enemigos (hasta maxEnemies), 
        # y el score
        player_location = gym.spaces.Box(low=0, high=1000, shape=(2,), dtype=np.float32)
        enemy_location  = gym.spaces.Box(low=0, high=1000, shape=(2,), dtype=np.float32)
        score           = gym.spaces.Box(low=0, high=1000, shape=(1,), dtype=np.float32)
        self.observation_space = gym.spaces.Dict({
            "player_location": player_location,
            "enemy_locations": gym.spaces.Tuple([enemy_location for _ in range(maxEnemies)]),
            "score": score
        })

    def _receive_obs(self):
        # Se puede mandar al scanner que mande mensaje
        buffer = ""
        while True:
            try:
                data = self.socket.recv(1024).decode()
                if not data:
                    break
                buffer += data
                while SEPARETOR in buffer:
                    message, buffer = buffer.split(SEPARETOR, 1)
                    json_data = json.loads(message)
                    return json_data
            except Exception as e:
                break

    def _focus_game_window(self):
        windows = gw.getWindowsWithTitle(self.windowTitle)
        if windows:
            game_window = windows[0]
            game_window.activate()
            time.sleep(0.001)
            return True
        else:
            return False

    def _perform_action(self, action):
        if action != 0:
            action -= 1
            if self._focus_game_window():
                keyboard.press_and_release(self.buttons[action])
                time.sleep(0.001)

    def step(self, action):
        self._perform_action(action)
        json_obs = self._receive_obs()
        obs = None
        reward = 0
        done = False
        info = {}
        return obs, reward, done, False, info

    def _reset_game():
        pass

    def reset(self):
        self._reset_game()
        initial_obs = self._receive_obs()
        return initial_obs, {}

    def close(self):
        self.socket.close()