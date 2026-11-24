# Rebuilds the city maps from the tree cards (fields b = birth, place = residence, d = death).
# Run after every change to a card's birth, residence or death:  python -I tools/maps/run.py
# Maps: sofer.json -> sofer-map/,  ovadia.json -> ovadia-map/.
# A new person added to one of these trees must also be added to ids_sofer.txt / ids_ovadia.txt,
# and a new city must be added to cities.py (Hebrew name, foreign name, lat, lon, aliases).
import os, subprocess, sys
D = os.path.dirname(os.path.abspath(__file__))
for cfg in (sys.argv[1:] or ['sofer.json', 'ovadia.json']):
    subprocess.run([sys.executable, '-I', os.path.join(D, 'build.py'), D, cfg], check=True)
