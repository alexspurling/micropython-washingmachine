@echo off

rshell -p COM5 -b 460800 rsync src/ /pyboard/
if ERRORLEVEL 1 echo Error
rshell -p COM5 -b 460800 repl ~ import main ~