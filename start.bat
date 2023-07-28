@echo off

rem Replace 'bs-w-instr' with the name of your Anaconda environment
call activate bs-w-instr

rem Replace 'path_to_python' with the full path to your Python executable
rem (e.g., C:\Users\YourUsername\Anaconda3\envs\bs-w-instr\python.exe)
set "python_exe=C:\Users\denko\anaconda3\envs\bs-w-instr\python.exe"

rem Replace 'path_to_manage_py' with the full path to your manage.py file
rem (e.g., C:\Users\YourUsername\PSI\qc_website-main\manage.py)
set "manage_py=C:\Users\denko\PSI\qc_website-main\manage.py"

rem Start Django server
"%python_exe%" "%manage_py%" runserver
