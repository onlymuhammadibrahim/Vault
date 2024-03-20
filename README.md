# Vault

This Vault app is a password manager available on Windows/ MacOS and Android. It uses the MySQL database to store passwords online in encrypted form using the Fernet module. The Fernet module guarantees that data encrypted using it cannot be further manipulated or read without the key.

Usage:

1) Download the app from https://bit.ly/492lrHo
2) Since we will need a database as a free alternative, I would suggest to use https://www.clever-cloud.com/
3) Sign Up and create a MySQL addon with a free tier.
4) Now note down Database Credentials.
5) Open your app and click "Get new key." Save this key somewhere safe, and don't lose it.
6) Then click "Edit Details" and fill in the fields with your Database Credentials and Key that we just generated.
7) Then log in with your key and Start using the app.

IMP:
As we are using a free database, it is vital to back it up weekly or monthly to avoid losing data. 

1) Go to your addon
2) Go to PHPMyAdmin
3) Select your Database
4) Click the export tab
5) Then click export


---------------------------------------------------

For Devs only:

Build on MacOs:
1) Change Path in main.py file to the mac one.

2) Replace path of main.py in the following command and run it in terminal

pyinstaller -y --clean --windowed --name vault --icon vault.ico \
  --exclude-module _tkinter \
  --exclude-module Tkinter \
  --exclude-module enchant \
  --exclude-module twisted \
  <path to main.py file>

3) You will get .app file in dist folder



Build on Android:
1) Run "buildozer init" in terminal

2) change requirements in buildozer.spec file to:

requirements = python3,kivy,cryptography,pymysql

3) Change application name and Add icon path spec file

4) Uncomment android.permissions line

5) buildozer android debug

6) You will get .apk in bin folder



Build on Windows:
1) Run this command in CMD:

python -m PyInstaller --onefile --name vault --icon vault.ico main.py

2) Keep spec file and delete other files that were created

3) Add this to start of spec file:

from kivy_deps import sdl2, glew

4) Add this in exe at end of spec file and change console to False:

*[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)]

5) Run this command:

python -m PyInstaller vault.spec

6) You will get .exe in dist folder.

7) Run program as administrator