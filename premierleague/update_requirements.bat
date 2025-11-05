@echo off
M:
cd M:\projects\Python\PremierLeague

call premierleague\virtualenvironment\Scripts\activate.bat
pip freeze > requirements.txt
