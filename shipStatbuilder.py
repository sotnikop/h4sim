
from vendor import pdxparser
import pandas as pd
from collections import defaultdict

def parse_modules(file_path):
    raw = pdxparser.pdx_parse(file_path)
    return raw.get('equipment_modules', [None, {}])[1]

def parse_ships(file_path):
    raw = pdxparser.pdx_parse(file_path)
    return raw.get('equipments', [None, {}])[1]

def extract_module_stats(modules):
    module_data = {}
    for name, content in modules.items():
        if isinstance(content, list) and isinstance(content[1], dict):
            content = content[1]
        mod = {
            'add_stats': content.get('add_stats', [None, {}])[1],
            'multiply_stats': content.get('multiply_stats', [None, {}])[1],
            'add_average_stats': content.get('add_average_stats', [None, {}])[1],
        }
        module_data[name] = mod
    return module_data

def extract_ship_modules(ship):
    raw_modules = ship.get('default_modules', [None, {}])[1]
    return [mod[1] for mod in raw_modules.values() if isinstance(mod, list) and len(mod) == 2]


def extract_base_stats(ship):
    return {
        'manpower': float(ship.get('manpower', [None, 0])[1]),
        'naval_speed': float(ship.get('naval_speed', [None, 0])[1]),
        'build_cost_ic': float(ship.get('build_cost_ic', [None, 0])[1])
    }
def calculate_ship_stats(ship_name, ship_data, module_data):
    base = extract_base_stats(ship_data)
    modules = extract_ship_modules(ship_data)

    final_stats = defaultdict(float)
    averages = defaultdict(list)
    speed_mod = 0.0

    for mod in modules:
        if isinstance(mod, list):
            mod = mod[1]  # unwrap ['=', 'modulename']
        if mod == 'empty' or mod not in module_data:
            continue

        stats = module_data[mod]

        for k, v in stats.get('add_stats', {}).items():
            if isinstance(v, list): v = v[1]
            final_stats[k] += float(v)

        for k, v in stats.get('multiply_stats', {}).items():
            if k == 'naval_speed':
                if isinstance(v, list): v = v[1]
                speed_mod += float(v)

        for k, v in stats.get('add_average_stats', {}).items():
            if isinstance(v, list): v = v[1]
            averages[k].append(float(v))

    final_stats['manpower'] = base['manpower']
    final_stats['build_cost_ic'] += base['build_cost_ic']
    final_stats['naval_speed'] = base['naval_speed'] * (1 + speed_mod)

    for k, vals in averages.items():
        final_stats[k] = sum(vals) / len(vals) if vals else 0

    final_stats['ship_name'] = ship_name
    return final_stats

# === RUN ===
module_files = [
        "shipdata\\eng_ship_modules.txt",
        "shipdata\\jap_ship_modules.txt",
        "shipdata\\fra_ship_modules.txt",
        "shipdata\\ger_ship_modules.txt",
        "shipdata\\ita_ship_modules.txt",
        "shipdata\\sov_ship_modules.txt",
        "shipdata\\usa_ship_modules.txt",

    # Add more as needed
]
all_modules = {}
for path in module_files:
    modules = extract_module_stats(parse_modules(path))
    all_modules.update(modules)
modules = all_modules

ship_files = [
    "shipdata\\ship_hull_heavy.txt",
    "shipdata\\ship_hull_light.txt",
    "shipdata\\ship_hull_carrier.txt",
    "shipdata\\ship_hull_very_light.txt",
    "shipdata\\ship_hull_heavy_cruiser.txt",
]

results = []
for ship_file in ship_files:
    ships = parse_ships(ship_file)
    for name, pair in ships.items():
        if isinstance(pair, list) and len(pair) == 2 and isinstance(pair[1], dict):
            data = pair[1]
            if 'default_modules' in data and 'manpower' in data:
                result = calculate_ship_stats(name, data, modules)
                results.append(result)


df = pd.DataFrame(results)
df.to_csv("hoi4_ship_stats_output.csv", index=False)
print("✅ Output saved to hoi4_ship_stats_output.csv")
