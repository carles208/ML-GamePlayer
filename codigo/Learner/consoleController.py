import subprocess
import threading

inputDictionary = {
    "left":     (':IN0', 'P1 Left'),
    "right":    (':IN0', 'P1 Right'),
    "action":   (':IN1', 'P1 Button 1'),
    "coin":     (':IN1', 'Coin 1'),
    "start":    (':IN1', '1 Player Start')
}

class Console():
    def __init__(self, mame_directory, game_name):
        self.process = subprocess.Popen(
            ['mame', '-console', game_name, '-skip_gameinfo'],
            cwd=mame_directory,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            shell=True)
        
        self._writeln('s = manager.machine.screens[":screen"]')
        self._writeln('releaseQueue = {}')
        self._writeln('actionsQueue = {}')
        self._writeln('function pipeData() \
        if (math.fmod(tonumber(s:frame_number()), 5) == 0) then \
        for i=1,#releaseQueue do  \
        releaseQueue[i](); \
        releaseQueue[i] = nil;\
        end; \
        for i=1,#actionsQueue do \
        actionFunc = load(actionsQueue[i]..":set_value(1)"); \
        actionFunc(); \
        releaseFunc = load(actionsQueue[i]..":set_value(0)"); \
        table.insert(releaseQueue, releaseFunc); \
        actionsQueue[i] = nil; \
        end; \
        end; \
        end')
        self._writeln('emu.register_frame(pipeData, "data")')
        threading.Thread(target=self.readln, args=(), daemon=True).start()
    
    def _send_input(self, input):
        if input in inputDictionary:
            tagField = inputDictionary[input]
            self._writeln('table.insert(actionsQueue, ' + f'"manager.machine.ioport.ports[\'{tagField[0]}\'].fields[\'{tagField[1]}\']")')

    def _writeln(self, string):
        self.process.stdin.write(string.encode("utf-8") + b'\n')
        self.process.stdin.flush()

    def _loadState(self, name):
        self._writeln("manager.machine:load('"+ name +"')")

    def _pause_game(self):
        self._writeln("emu.pause()")

    def _unpause_game(self):
        self._writeln("emu.unpause()")

    def readln(self):
        while True:
            self.process.stdout.readline()