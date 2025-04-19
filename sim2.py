import random
import pandas as pd
import json

# === Ship and Fleet Classes ===
class Ship:
    def __init__(self, ship_type, stats):
        self.type = ship_type
        self.stats = stats
        self.hp = stats["HP"]
        self.org = stats["Org"]

    def is_alive(self):
        return self.hp > 0

    def take_damage(self, damage, max_hp):
        hp_loss, org_loss = calculate_hp_org_loss(damage, self.hp, self.org, max_hp)
        self.hp = max(0, self.hp - hp_loss)
        self.org = max(0, self.org - org_loss)
        return hp_loss, org_loss

    def get_effective_attack(self):
        # Apply ORG penalty: 50% attack reduction if ORG is 0
        return self.stats["Heavy Attack"] * (0.5 if self.org <= 0 else 1.0)

class Fleet:
    def __init__(self, composition, ship_templates):
        self.ships = self.create_fleet(composition, ship_templates)

    def create_fleet(self, composition, ship_templates):
        fleet = []
        for ship_type, count in composition.items():
            if ship_type not in ship_templates:
                raise ValueError(f"Unknown ship type: {ship_type}")
            for _ in range(count):
                fleet.append(Ship(ship_type, ship_templates[ship_type]))
        return fleet

    def get_active_ships(self):
        return [ship for ship in self.ships if ship.is_alive()]

    def is_defeated(self):
        return not any(ship.is_alive() for ship in self.ships)

# === Combat Mechanics ===
def calculate_damage_reduction(armor, piercing):
    """Calculate damage reduction based on armor and piercing."""
    return 90 * (1 - (piercing / armor)) if armor > piercing else 0

def calculate_hp_org_loss(damage, current_hp, current_org, max_hp):
    """Calculate HP and ORG loss with scaling."""
    org_loss_multiplier = 1 - (current_hp / max_hp)
    hp_loss = damage * 0.6  # 60% of damage to HP
    org_loss = damage * 0.4 * org_loss_multiplier  # ORG loss scales with HP lost
    return hp_loss, org_loss

def calculate_hit_chance(attacker_speed, target_speed):
    """Calculate hit chance based on speed difference."""
    return min(1.0, max(0.5, 0.8 + (attacker_speed - target_speed) / 100))

def calculate_critical_hit(piercing, armor):
    """Calculate critical hit multiplier if piercing significantly exceeds armor."""
    return 1.5 if piercing > 1.5 * armor else 1.0

# === Targeting Logic ===
def target_enemy(enemy_fleet):
    """Select a random active enemy ship as the target."""
    active_enemies = enemy_fleet.get_active_ships()
    return random.choice(active_enemies) if active_enemies else None

# === Combat Simulator ===
class CombatSimulator:
    def __init__(self, fleet1, fleet2, max_rounds=20):
        self.fleet1 = fleet1
        self.fleet2 = fleet2
        self.max_rounds = max_rounds
        self.battle_log = []

    def generate_log_columns(self):
        """Generate dynamic column names for the battle log."""
        columns = ["Round"]
        for fleet, name in [(self.fleet1, "Fleet1"), (self.fleet2, "Fleet2")]:
            for i, ship in enumerate(fleet.ships):
                columns.extend([
                    f"{name} Ship {i+1} ({ship.type}) HP",
                    f"{name} Ship {i+1} ({ship.type}) ORG"
                ])
        return columns

    def log_round(self, round_num):
        """Log the state of all ships in the current round."""
        log_data = [round_num]
        for fleet in [self.fleet1, self.fleet2]:
            for ship in fleet.ships:
                log_data.extend([ship.hp, ship.org])
        self.battle_log.append(log_data)

    def run_combat(self):
        """Run the combat simulation and return the battle log as a DataFrame."""
        for round_num in range(1, self.max_rounds + 1):
            if self.fleet1.is_defeated() or self.fleet2.is_defeated():
                break

            # Fleet 1 attacks
            for ship in self.fleet1.get_active_ships():
                target = target_enemy(self.fleet2)
                if target:
                    # Apply hit chance and critical hit
                    if random.random() < calculate_hit_chance(ship.stats["Speed"], target.stats["Speed"]):
                        damage = ship.get_effective_attack() * calculate_critical_hit(
                            ship.stats["Piercing"], target.stats["Armor"]
                        )
                        # Apply damage reduction
                        damage *= (1 - calculate_damage_reduction(target.stats["Armor"], ship.stats["Piercing"]) / 100)
                        target.take_damage(damage, target.stats["HP"])

            # Fleet 2 attacks
            for ship in self.fleet2.get_active_ships():
                target = target_enemy(self.fleet1)
                if target:
                    if random.random() < calculate_hit_chance(ship.stats["Speed"], target.stats["Speed"]):
                        damage = ship.get_effective_attack() * calculate_critical_hit(
                            ship.stats["Piercing"], target.stats["Armor"]
                        )
                        damage *= (1 - calculate_damage_reduction(target.stats["Armor"], ship.stats["Piercing"]) / 100)
                        target.take_damage(damage, target.stats["HP"])

            # Log the round
            self.log_round(round_num)

        # Create DataFrame for battle log
        return pd.DataFrame(self.battle_log, columns=self.generate_log_columns())

# === Configuration Loader ===
def load_ship_templates(ship_templates_path):
    """Load ship templates from a JSON file."""
    with open(ship_templates_path, "r") as f:
        return json.load(f)

def load_config(config_path):
    """Load fleet compositions and simulation parameters from a JSON config file."""
    with open(config_path, "r") as f:
        return json.load(f)

# === Main Execution ===
if __name__ == "__main__":
    # Load ship templates and config
    ship_templates = load_ship_templates("ships.json")
    config = load_config("config.json")

    # Create fleets
    fleet1 = Fleet(config["fleet1"], ship_templates)
    fleet2 = Fleet(config["fleet2"], ship_templates)
    max_rounds = config["max_rounds"]

    # Run simulation
    simulator = CombatSimulator(fleet1, fleet2, max_rounds)
    battle_log_df = simulator.run_combat()

    # Print results
    print("\n===== Battle Simulation Results =====\n")
    print(battle_log_df.to_string(index=False))