from typing import Dict, List, Any, ClassVar
from BaseClasses import Item, ItemClassification, Region, Location
from worlds.AutoWorld import World, WebWorld
from .items import RE4Item, item_table, create_item_pool
from .locations import RE4Location, location_table, create_all_location_names
from .options import RE4Options
from .regions import create_regions


class RE4WebWorld(WebWorld):
    theme = "ocean"
    tutorials = [
        Tutorial(
            tutorial_name="Setup Guide",
            description="A guide to setting up Resident Evil 4 UHDE for Archipelago multiworld.",
            language="English",
            file_name="setup_en.md",
            link="setup/en",
            authors=["VincentsSin"]
        )
    ]


class RE4World(World):
    """
    Resident Evil 4 is a survival horror game, the first entry in the series as a player-focused, third-person shooter
    instead of fixed camera from previous entries. Players utilize resource management for crowd control, laser-sighted
    weapons for precision targeting, and "stop-and-shoot" combat against swarming enemies.
    """

    game = "Resident Evil 4 UHDE"
    options_dataclass = RE4Options
    options: RE4Options
    
    topology_present = True
    
    item_name_to_id: ClassVar[Dict[str, int]] = {name: data["id"] for name, data in item_table.items()}
    location_name_to_id: ClassVar[Dict[str, int]] = location_table
    
    required_client_version = (0, 5, 0)
    
    def create_item(self, name: str) -> RE4Item:
        """Create an item for this world."""
        item_data = item_table[name]
        return RE4Item(name, item_data["classification"], item_data["id"], self.player)
    
    def create_items(self) -> None:
        """Create and add items to the multiworld pool."""
        item_pool = create_item_pool(self)
        self.multiworld.itempool += item_pool
    
    def create_regions(self) -> None:
        """Create regions and locations."""
        create_regions(self)
    
    def set_rules(self) -> None:
        """Set access rules for locations."""
        from .rules import set_rules
        set_rules(self)
    
    def generate_basic(self) -> None:
        """Generate basic structures."""
        pass
    
    def generate_output(self, output_directory: str) -> None:
        """Generate output files if needed."""
        pass
    
    def fill_slot_data(self) -> Dict[str, Any]:
        """Return data to be sent to the client."""
        return {
            "goal_modes": list(self.options.goal_modes.value),
            "enabled_modes": list(self.options.enabled_modes.value),
            "death_link": self.options.death_link.value,
        }
    
    def get_filler_item_name(self) -> str:
        """Return the name of a filler item."""
        return "Plaga Virus"