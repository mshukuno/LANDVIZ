@echo off
cd ..\PreProcTool
preproctool.exe preproc -p ..\small_example\preproc_VizTool_example.xml -o ..\small_example_output\output %*
pause

 