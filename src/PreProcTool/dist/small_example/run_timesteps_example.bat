@echo off
cd ..\PreProcTool
preproctool.exe timesteps -i "{directory}\NoAM\Rep1\bda\bda-log.csv" -f "bda-log-timesteps.csv" -ts_c "Time" -ts_i 1 -ts_min 0 -ts_max 114 -g "AgentName" %*
pause

