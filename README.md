# Social Emperors

Social Empires preservation project.

## Installation
### Windows 
You first need to install Python. 
I have currently run this on 3.10.1, but you may be able to use any version from 3.7-3.10.
After you have installed Python, you will need to use your favorite package manager (usually `pip`) to install PyInstaller and Flask.
You can run `pip install -U flask pyinstaller` to do this.

You will notice a `build` directory, containing a `build.bat` batch script.
To build the app, you will need to run this script.
Once it has finished, you will see a file called `social-emperors_0.01a.exe` in `build/dist`.
Move this out to the root directory `socialemperors`.
You will be able to run this application, but it is just a server for the Social Empires game.
There will be a line in the terminal that says something like `* Running on http://127.0.0.1:5050`. 
Keep this address in mind.

In order to actually play the game, you will need to use a browser that is still capable of running Flash. 
[I use this browser](https://github.com/radubirsan/FlashBrowser/). 
After you open the browser, enter the address from the `* Running` line and then you should be able to play the game.

Have fun! :)

### Other OSes
TODO