from typing import Callable, Dict, NamedTuple, Optional

from BaseClasses import Location, MultiWorld


class RE4Location(Location):
    game = "Resident Evil 4"


class RE4LocationData(NamedTuple):
    region: str
    address: Optional[int] = None
    can_create: Callable = lambda options: True
    locked_item: Optional[str] = None

location_data_table: Dict[str, RE4LocationData] = {
    
}