import subprocess
import platform
from django.shortcuts import redirect

def restart_server():
    # Check the operating system
    if platform.system() == 'Windows':
        # Windows-specific commands
        stop_command = ["taskkill", "/F", "/IM", "python.exe"]
        start_command = ["python", "manage.py", "runserver"]
    else:
        # Unix/Linux-specific commands
        stop_command = ["pkill", "-f", "runserver"]
        start_command = ["python", "manage.py", "runserver"]
    print("RESTARTING SERVER")
    # Stop the current runserver process
    # subprocess.call(stop_command)

    # Start a new runserver process
    subprocess.Popen(start_command)

    # Redirect to a new URL or template
    # return redirect('home')  # Replace 'home' with the appropriate URL pattern name or URL path
restart_server()