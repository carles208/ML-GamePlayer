import socket
import json
import gymnasium as gym
import numpy as np
from consoleController import Console

SEPARETOR = "<END>"

class GameEnvironment(gym.Env):
    def __init__(self, host, port, emulatorDir, gameName, buttons, maxEnemies):
        super().__init__()
        self.maxEnemies = maxEnemies

        # Se incia el emulador
        self.console = Console(emulatorDir, gameName)
        self.console._loadState("1")
        self.console._pause_game()

        # Se define el socket que se utilizará para comunicarse con el scanner
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.socket.listen(1)
        self.conn, _ = self.socket.accept()

        # Espacio de salida de la red a partir de una lista de botones (0 representa no pulsar ninguno)
        self.buttons = buttons
        self.action_space = gym.spaces.Discrete(len(buttons)+1)

        self.prev_score = 0
        self.game_speed = 1.0
        self.seen_player = False

        # Espacio de observaciones basado tamaño y posción de jugador y enemigos (hasta maxEnemies), 
        # y el score
        player_location = gym.spaces.Box(low=0, high=1, shape=(2,), dtype=np.float32)
        enemy_location  = gym.spaces.Box(low=0, high=1, shape=(2,), dtype=np.float32)
        self.observation_space = gym.spaces.Dict({
            "player_location": player_location,
            "enemy_locations": gym.spaces.Tuple([enemy_location for _ in range(maxEnemies)])
        })

    def _receive_json(self):
        buffer = ""
        while True:
            try:
                data = self.conn.recv(1024).decode()
                if not data:
                    break
                buffer += data
                while SEPARETOR in buffer:
                    message, buffer = buffer.split(SEPARETOR, 1)
                    json_data = json.loads(json.loads(message))
                    return json_data
            except Exception as e:
                break

    def _ask_info(self, ):
        try:
            mensaje = " "
            self.conn.sendall(mensaje.encode())
        except Exception as e:
            print(f"[Error enviando]: {e}")

    def _get_obs_and_score(self):
        self._ask_info()
        json_data = self._receive_json()
        if json_data == None:
            json_data = {
                "detections": [],
                "score": "0"
            }
            
        detections = json_data['detections']
        score = json_data['score']
        if len(score) > 0:
            score = float(score)
        else:
            score = 0
        
        enemies = []
        players = []
        for det in detections:
            if det['class'] == 'Player':
                players.append(det['position'])
            else:
                enemies.append(det['position'])
        enemies.sort()

        player_location = [-1, -1]
        for p in players:
            if p[1] < 0.92:
                player_location = p
                self.seen_player = True

        while len(enemies) < self.maxEnemies:
            enemies.append([-1, -1])
            
        diff = 0
        if score > self.prev_score:
            diff = score - self.prev_score
            self.prev_score = score

        return {
            "player_location": player_location,
            "enemy_locations": enemies
        }, diff

    def _perform_action(self, action):
        if action != 0:
            self.console._send_input(self.buttons[action-1])

    def step(self, action):
        self._perform_action(action)
        obs, reward = self._get_obs_and_score()
        done = obs['player_location'][0] == -1 and self.seen_player
        if done:
            reward = -1000
        info = {}
        return obs, reward, done, False, info

    def _reset_game(self):
        self.console._loadState("1")
        self.console._pause_game()
        self.prev_score = 0
        self.seen_player = False

    def reset(self, seed, options):
        self._reset_game()
        self.console._unpause_game()
        initial_obs, _ = self._get_obs_and_score()
        return initial_obs, {}

    def close(self):
        self.socket.close()