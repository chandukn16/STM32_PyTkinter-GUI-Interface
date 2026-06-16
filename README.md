# STM32_PyTkinter-GUI-Interface
Python Tkinter GUI Developed a custom graphical user interface (GUI) to STM32 monitoring, debugging, and command execution. GUI enables bidirectional communication between PC &amp; MCU using UART Tx/Rx interrupt-based data transmission. UART commands transmitted directly from the GUI while receiving real-time responses from the STM32.

[1] Verify Python Installation First:
Before running the code, verify Python is installed: 
           python --version  //Should show: Python 3.x.x
Check if tkinter works:
           python -m tkinter  //Should open a small Tk window

[Imp1] Create Standalone Executable (.exe)
If you want a professional .exe file that anyone can run:
Step 1: Install PyInstaller
Open Command Prompt and type:
          pip install pyinstaller
Step 2: Convert to EXE
Navigate to where your .py file is:
          cd Desktop (go to your actual file location)
          pyinstaller --onefile --windowed mygui.py  //run this code creates .EXE file
Step 3: Find Your EXE
Go to Desktop → dist folder
You'll find my_gui_app.exe

[B] Creation File
  Step 1: Create a new file at Notepad
Open Notepad and paste example code
  Step 2: Save the File Correctly
In Notepad, click File → Save As
IMPORTANT Steps:
Navigate to Desktop
In "File name", type: mygui.py
In "Save as type", select: "All Files (.)"
In "Encoding", select: "UTF-8"
Click Save

[C] How to run python script file created through Notepad.
- open command prompt 
- admin is come first then type "      cd Desktop/Py_tkinter      " 
this command take to actual file directory then 
- then type "   python mygui.py    "  
this can run your tkinter file and open external window. 

[D] Install PySerial Library
   Step 1: Install pyserial
Type this command and press Enter:   pip install pyserial
Step 2: Verify Installation:         pip show pyserial    //shows like this-- Name: pyserial
Version: 3.5
Summary: Python Serial Port Extension

[E] Navigate to Your File Location
In Command Prompt, navigate to where you saved the file:
If saved on Desktop: cd Desktop
Or if saved in a specific folder: cd C:\Users\YourName\Documents\PythonProjects

Useful commands:
dir          # List all files in current folder
cd ..        # Go up one folder
cd foldername # Enter a folder

Step 4: Run the Python File
Simply type:
        python mygui.py
Or if you have multiple Python versions:
        python3 first_gui.py
