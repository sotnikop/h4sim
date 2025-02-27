# Reinitialize variables due to execution state reset

import random
import pandas as pd
#import ace_tools as tools

# Given Stats (Reinitialize)
large_ship = {
    "HP": 1222,
    "Heavy Attack": 158,
    "Piercing": 612,
    "Armor": 500,
    "Speed": 28,
    "Org": 50
}

small_ship = {
    "HP": 283,
    "Heavy Attack": 68,
    "Piercing": 198,
    "Armor": 75,
    "Speed": 35,
    "Org": 50
}

num_small_ships = 4

# HOI4 Naval Damage Reduction Formula
def calculate_damage_reduction(armor, piercing):
    if armor > piercing:
        return 90 * (1 - (piercing / armor))  # Formula for damage reduction
    return 0  # No reduction if piercing >= armor

# HOI4 HP & ORG Loss Formula (Adjusted for ORG Immunity Scaling)
def calculate_hp_org_loss(damage, current_hp, current_org):
    """Applies scaling HP and ORG loss based on HP level."""
    org_loss_multiplier = 1 - (current_hp / small_ship["HP"])  # ORG damage scales with HP lost
    hp_loss = damage * 0.6  # 60% of damage applies to HP
    org_loss = damage * 0.4 * org_loss_multiplier  # ORG loss starts small, increases as HP is lost
    return hp_loss, org_loss

# Reset battle conditions for independent tracking of all small ships
large_ship_hp = large_ship["HP"]
large_ship_org = large_ship["Org"]
small_ships = [{"HP": small_ship["HP"], "ORG": small_ship["Org"]} for _ in range(num_small_ships)]

# Store battle progress for 20 rounds
battle_log = []

# Combat loop with independent ship tracking
for round_num in range(1, 21):  # First 20 rounds
    if large_ship_hp <= 0 or all(ship["HP"] <= 0 for ship in small_ships):
        break  # Stop if either side is fully eliminated

    # Remove any ships that have reached HP ≤ 0
    small_ships = [ship for ship in small_ships if ship["HP"] > 0]

    # Large ship randomly selects a small ship to attack (only among active ones)
    if small_ships:  # Ensure there are still ships to attack
        target_ship = random.choice(small_ships)

        # Large ship attacks the selected small ship
        hp_loss_small, org_loss_small = calculate_hp_org_loss(large_ship["Heavy Attack"], target_ship["HP"], target_ship["ORG"])
        target_ship["HP"] -= hp_loss_small
        target_ship["ORG"] -= max(0, org_loss_small)  # Ensure ORG doesn't become positive

        # If a ship reaches HP ≤ 0, remove it from the list
        small_ships = [ship for ship in small_ships if ship["HP"] > 0]

    # Small ships attack the large ship (only active ones contribute damage)
    active_small_ships = len(small_ships)
    total_damage_from_small_ships = active_small_ships * small_ship["Heavy Attack"] * (1 - (calculate_damage_reduction(large_ship["Armor"], small_ship["Piercing"]) / 100))
    #debug
    dr = calculate_damage_reduction(large_ship["Armor"], small_ship["Piercing"])

    hp_loss_large, org_loss_large = calculate_hp_org_loss(total_damage_from_small_ships, large_ship_hp, large_ship_org)
    large_ship_hp -= hp_loss_large

    # Ensure ORG loss is correctly scaled and does not become negative
    large_ship_org_loss_multiplier = 1 - (large_ship_hp / large_ship["HP"])
    org_loss_large = abs(org_loss_large * large_ship_org_loss_multiplier)  # Ensuring ORG loss is always positive
    large_ship_org = max(0, large_ship_org - org_loss_large)

    # Apply correct ORG penalty separately for each side
    large_ship_penalty = 0.5 if large_ship_org <= 0 else 0
    small_ships_penalty = 0.5 if any(ship["ORG"] <= 0 for ship in small_ships) else 0

    # Adjust effective attack values for both sides based on ORG penalties
    effective_large_ship_attack = large_ship["Heavy Attack"] * (1 - large_ship_penalty)
    effective_small_ship_attack = small_ship["Heavy Attack"] * (1 - small_ships_penalty)

    # Log the round details with independent ship tracking
    battle_log.append([
        round_num, large_ship_hp, large_ship_org, effective_large_ship_attack, total_damage_from_small_ships,dr,
        small_ships[0]["HP"] if len(small_ships) > 0 else None, small_ships[0]["ORG"] if len(small_ships) > 0 else None,
        small_ships[1]["HP"] if len(small_ships) > 1 else None, small_ships[1]["ORG"] if len(small_ships) > 1 else None,
        small_ships[2]["HP"] if len(small_ships) > 2 else None, small_ships[2]["ORG"] if len(small_ships) > 2 else None,
        small_ships[3]["HP"] if len(small_ships) > 3 else None, small_ships[3]["ORG"] if len(small_ships) > 3 else None
    ])

# Create DataFrame to display results for rounds 1-20
df_battle_log_debug = pd.DataFrame(battle_log, columns=[
    "Round", "Large Ship HP", "Large Ship ORG", "Effective Large Ship Attack", "Total Damage to Large Ship","dr",
    "Small Ship 1 HP", "Small Ship 1 ORG",
    "Small Ship 2 HP", "Small Ship 2 ORG",
    "Small Ship 3 HP", "Small Ship 3 ORG",
    "Small Ship 4 HP", "Small Ship 4 ORG"
])

''' # Extracting combat data between rounds 6 and 11 to analyze large ship's attack values
rounds_6_to_11_data = df_battle_log_debug[df_battle_log_debug["Round"].between(0, 11)][
    ["Round", "Large Ship ORG", "Effective Large Ship Attack"]
] '''

# Print the full battle log in terminal-friendly format
print("\n===== Battle Simulation Results =====\n")
print(df_battle_log_debug.to_string(index=False))