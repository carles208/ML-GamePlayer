@echo off
REM Activar el ambiente de Conda deseado
call conda deactivate
call conda activate MLGamePlayer

REM Lanzar el script del entorno Gym
start python Learner/gymTesterInputs.py

timeout /t 1 > nul

REM Lanzar el Scanner
start python Scanner/scanner.py

REM Mantener la ventana de comandos abierta
REM cmd /k