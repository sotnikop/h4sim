# Reset battle conditions for independent tracking of all small ships
large_ship_hp = large_ship["HP"]
large_ship_org = large_ship["Org"]
small_ships = [{"HP": small_ship["HP"], "ORG": small_ship["Org"]} for _ in range(num_small_ships)]

# Store battle progress for 20 rounds (fixing ORG penalty application)
battle_log = []

# Combat loop with properly applied ORG penalties and attack reduction
for round_num in range(1, 21):  # 20 rounds total
    if large_ship_hp <= 0 or all(ship["HP"] <= 0 for ship in small_ships):
        break  # Stop if either side is fully eliminated

    # Remove any ships that have reached HP ≤ 0
    small_ships = [ship for ship in small_ships if ship["HP"] > 0]

    # Calculate ORG Loss Multiplier (ensuring ORG loss scales with HP% correctly)
    large_ship_hp_ratio = large_ship_hp / large_ship["HP"]
    large_ship_org_loss_multiplier = 1 - large_ship_hp_ratio  # Ensuring ORG loss scales up as HP drops

    # Large ship randomly selects a small ship to attack (only among active ones)
    if small_ships:
        target_ship = random.choice(small_ships)

        # Large ship attacks the selected small ship
        hp_loss_small, org_loss_small = calculate_hp_org_loss(large_ship["Heavy Attack"], target_ship["HP"], target_ship["ORG"])
        target_ship["HP"] -= hp_loss_small
        target_ship["ORG"] -= max(0, org_loss_small)  # Ensure ORG doesn't become positive

    # Small ships attack the large ship (only active ones contribute damage)
    active_small_ships = len(small_ships)
    total_damage_from_small_ships = active_small_ships * small_ship["Heavy Attack"] * (1 - (calculate_damage_reduction(large_ship["Armor"], small_ship["Piercing"]) / 100))

    # Apply proper ORG loss scaling based on HP% remaining
    hp_loss_large, org_loss_large = calculate_hp_org_loss(total_damage_from_small_ships, large_ship_hp, large_ship_org)
    org_loss_large = abs(org_loss_large * large_ship_org_loss_multiplier)  # Ensuring ORG loss is always positive

    # Ensure ORG cannot increase and does not drop below 0
    large_ship_org = max(0, large_ship_org - org_loss_large)
    for ship in small_ships:
        ship["ORG"] = max(0, ship["ORG"])

    # Apply correct ORG penalty separately for each side
    large_ship_penalty = 0.5 if large_ship_org <= 0 else 0
    small_ships_penalty = 0.5 if any(ship["ORG"] <= 0 for ship in small_ships) else 0

    # Adjust effective attack values for both sides based on ORG penalties
    effective_large_ship_attack = large_ship["Heavy Attack"] * (1 - large_ship_penalty)
    effective_small_ship_attack = small_ship["Heavy Attack"] * (1 - small_ships_penalty)

    # Log the round details with debugging values
    battle_log.append([
        round_num, large_ship_hp, large_ship_org, effective_large_ship_attack, total_damage_from_small_ships, org_loss_large,
        small_ships[0]["HP"] if len(small_ships) > 0 else 0, small_ships[0]["ORG"] if len(small_ships) > 0 else 0,
        small_ships[1]["HP"] if len(small_ships) > 1 else 0, small_ships[1]["ORG"] if len(small_ships) > 1 else 0,
        small_ships[2]["HP"] if len(small_ships) > 2 else 0, small_ships[2]["ORG"] if len(small_ships) > 2 else 0,
        small_ships[3]["HP"] if len(small_ships) > 3 else 0, small_ships[3]["ORG"] if len(small_ships) > 3 else 0
    ])

# Create DataFrame to display results for all 20 rounds (including debug values)
df_battle_log_fixed = pd.DataFrame(battle_log, columns=[
    "Round", "Large Ship HP", "Large Ship ORG", "Effective Large Ship Attack", "Total Damage to Large Ship", "Large Ship ORG Loss",
    "Small Ship 1 HP", "Small Ship 1 ORG",
    "Small Ship 2 HP", "Small Ship 2 ORG",
    "Small Ship 3 HP", "Small Ship 3 ORG",
    "Small Ship 4 HP", "Small Ship 4 ORG"
])

# Display the updated battle log with debugging values
tools.display_dataframe_to_user(name="Fixed Battle Log (20 Rounds, ORG Penalty Correctly Applied)", dataframe=df_battle_log_fixed)
