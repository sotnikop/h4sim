Setup is as follows using poetry as the venv manager

```
pip install poetry
poetry.exe init
poetry lock
poetry add pandas
poetry shell
python .\sim2.py
```

How to use
```
1. Edit the config.json to setup your scenario
2. Run python ./sim2.py to generate the simulation.
3. Results will appear on the console
```

Todo 
```
1. Generate the default ship stats for all major nations
2. Have config.json be able to reference the ships by name and pull stats from the shipstats.csv
3. Generate a simulation summary
4. Convert to javascript and have it run in the browser
```