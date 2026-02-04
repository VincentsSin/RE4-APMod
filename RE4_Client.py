import asyncio
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Set, List
import queue
import os
import sys

try:
    import websockets
except ImportError:
    print("ERROR: websockets library required!")
    print("Install with: pip install websockets")
    sys.exit(1)

APP_NAME = "Resident Evil 4 - Archipelago Client"
APP_VERSION = "1.0.0"
BASE_ID = 847000  # Must match APWorld
GAME_NAME = "Resident Evil 4"

# Default save paths by platform
if sys.platform == "win32":
    DEFAULT_SAVE_PATH = Path(os.environ.get("APPDATA", "")) / ".madgarden" / "DR2C"
elif sys.platform == "darwin":
    DEFAULT_SAVE_PATH = Path.home() / "Library" / "Application Support" / ".madgarden" / "DR2C"
else:
    DEFAULT_SAVE_PATH = Path.home() / ".madgarden" / "DR2C"

# Item data matching mod and APWorld
ITEM_NAMES = {
    # Basic Resources (100-104)
    100: "Food Pack (+5)", 101: "Food Crate (+15)", 102: "Gas Can (+50)",
    103: "Ammo Box (+20)", 104: "Medical Supplies (+5)",
    # Stat Training (110-115)
    110: "Shooting Training", 111: "Strength Training", 112: "Fitness Training",
    113: "Medical Training", 114: "Mechanical Training", 115: "Morale Boost",
    # Common Weapons (120-123)
    120: "Pistol", 121: "Shotgun", 122: "Uzi", 123: "Hunting Rifle",
    # Rare Weapons (124-127)
    124: "Grenades (x3)", 125: "Chainsaw", 126: "AK-47", 127: "Flamethrower",
    # Special (130-132)
    130: "Zombo Point", 131: "Car Repair Kit", 132: "Survivor Cache",
    # Progressive Food (200-203)
    200: "Small Food (+3)", 201: "Medium Food (+8)", 202: "Large Food (+12)", 203: "Huge Food (+20)",
    # Progressive Gas (210-213)
    210: "Small Gas (+25)", 211: "Medium Gas (+75)", 212: "Large Gas (+100)", 213: "Gas Tanker (+150)",
    # Progressive Ammo (220-223)
    220: "Small Ammo (+10)", 221: "Medium Ammo (+30)", 222: "Large Ammo (+50)", 223: "Ammo Depot (+75)",
    # Progressive Medical (230-232)
    230: "First Aid (+3)", 231: "Medical Bag (+8)", 232: "Hospital Cache (+15)",
    # Character Upgrades (300-314)
    300: "Strength Manual", 301: "Fitness Guide", 302: "Shooting Voucher",
    303: "Medical Textbook", 304: "Mechanic's Handbook",
    310: "Protein Powder (+2 STR)", 311: "Energy Drinks (+2 FIT)", 312: "Weapon Oil (+2 SHT)",
    313: "Medical Journals (+2 MED)", 314: "Tool Set (+2 MCH)",
    321: "Vitality Boost", 322: "Speed Boost",
    # Morale (400-412)
    400: "Morale +1", 401: "Morale +2", 402: "Morale +3", 403: "Morale +8",
    410: "Calming Tea", 411: "Friendship Token", 412: "Therapy Session",
    # Random Weapons (500-530)
    500: "Random Common Melee", 501: "Random Common Gun",
    502: "Random Uncommon Melee", 503: "Random Uncommon Gun",
    504: "Random Rare Melee", 505: "Random Rare Gun",
    510: "Random Weapons x3", 511: "Random Armory x5",
    520: "Molotov (x3)", 521: "Pipe Bombs (x3)", 522: "Grenade Bundle (x5)",
    530: "Legendary Weapon",
    # Utility (600-622)
    600: "Car Parts", 601: "Mechanic's Kit", 622: "Safe Haven (Full Heal)",
    # Zombo Points (700-702)
    700: "Zombo +1", 701: "Zombo +2", 702: "Zombo +5",
    # Special Items (710-730)
    710: "Mystery Box", 711: "Pandora's Box", 730: "Supply Drop",
    # Mode Unlocks (800-819)
    800: "Mode Unlock: Familiar Characters",
    801: "Mode Unlock: Rare Characters",
    802: "Mode Unlock: Short Trip",
    803: "Mode Unlock: Long Road",
    804: "Mode Unlock: Four Jerks",
    805: "Mode Unlock: Deadlier Road",
    806: "Mode Unlock: Familiar EXTREME",
    807: "Mode Unlock: Rare EXTREME",
    808: "Mode Unlock: Marathon",
    809: "Mode Unlock: K*E*P*A",
    810: "Mode Unlock: Four Jerks EXTREME",
    811: "Mode Unlock: Endless",
    812: "Mode Unlock: O*P*P",
    813: "Mode Unlock: Quick Death",
    814: "Mode Unlock: Infection",
    815: "Mode Unlock: Severe Weather",
    816: "Mode Unlock: RPG Mode",
    817: "Mode Unlock: Scepter Mode",
    818: "Mode Unlock: Mutation",
    819: "Mode Unlock: Infection EXTREME",
    # Traps (900-914)
    900: "TRAP: Food Spoiled", 901: "TRAP: Morale Crisis", 902: "TRAP: Ambush",
    903: "TRAP: Gas Leak", 904: "TRAP: Weapon Jam", 905: "TRAP: Thief",
    906: "TRAP: Injury", 907: "TRAP: Car Damage", 908: "TRAP: Argument",
    909: "TRAP: Bandits", 910: "TRAP: Bad Omen", 911: "TRAP: Bad Weather",
    912: "TRAP: Gear Lost", 913: "TRAP: Food Poison", 914: "TRAP: False Hope",
}

# Mode info for per-mode locations
MODE_INFO = {
    0: "Normal", 1: "Familiar", 2: "Rare", 3: "Short", 4: "Long",
    5: "Four Jerks", 6: "Deadlier", 7: "Familiar EX", 8: "Rare EX",
    9: "Marathon", 10: "KEPA", 11: "Four Jerks EX", 12: "Endless",
    13: "OPP", 14: "Quick Death", 15: "Infection", 16: "Weather",
    17: "RPG", 18: "Scepter", 19: "Mutation", 20: "Infection EX",
}

# Mode ID to goal_mode key mapping (for matching against slot_data)
MODE_ID_TO_KEY = {
    0: "normal", 1: "familiar", 2: "rare", 3: "short", 4: "long",
    5: "4jerks", 6: "deadlier", 7: "familiarEX", 8: "rareEX",
    9: "marathon", 10: "kepa", 11: "4jerksEX", 12: "endless",
    13: "opp", 14: "quickdeath", 15: "infection", 16: "weather",
    17: "rpg", 18: "scepter", 19: "mutation", 20: "infectionEX",
}

def get_location_name(loc_id: int) -> str:
    """Get location name from ID, handling all location types."""
    
    # Global Day Start: 1000 + day (1001-1030)
    if 1001 <= loc_id <= 1030:
        return f"Day {loc_id - 1000} Start"
    
    # Global Day Clear: 1100 + day (1101-1130)
    if 1101 <= loc_id <= 1130:
        return f"Day {loc_id - 1100} Clear"
    
    # Locations Visited: 2000 + count (2001-2320) - expanded to 320
    if 2001 <= loc_id <= 2320:
        return f"Locations Visited: {loc_id - 2000}"
    
    # Sieges: 3000 + count (3001-3065) - expanded to 65
    if 3001 <= loc_id <= 3065:
        return f"Sieges Survived: {loc_id - 3000}"
    
    # Weapon Categories: 4001-4007 (common) and 4102-4109 (rare)
    weapon_categories = {
        4001: "Found Handgun",
        4002: "Found Rifle",
        4003: "Found Shotgun", 
        4004: "Found Blade",
        4005: "Found Explosive",
        4006: "Found Heavy Weapon",
        4007: "Found Blunt Weapon",
        4102: "Found Flamethrower",
        4103: "Found Minigun",
        4105: "Found AK-47",
        4106: "Found Sledgehammer",
        4107: "Found Fire Axe",
        4109: "Found Bow",
    }
    if loc_id in weapon_categories:
        return weapon_categories[loc_id]
    
    # Weapons Collected: 4200 + count (4201-4420) - expanded to 220
    if 4201 <= loc_id <= 4420:
        return f"Weapons Collected: {loc_id - 4200}"
    
    # Kills 1100-11000: 5000 + (kills/100) (5011-5110) - expanded to 11000
    if 5011 <= loc_id <= 5110:
        return f"Zombie Kills: {(loc_id - 5000) * 100}"
    
    # Kills 50-1000: 6000 + kills, except 6999 = 1000 kills
    if loc_id == 6999:
        return "Zombie Kills: 1000"
    if 6050 <= loc_id <= 6950:
        return f"Zombie Kills: {loc_id - 6000}"
    
    # Toilets: 7000 + count (7001-7110) - expanded to 110
    if 7001 <= loc_id <= 7110:
        return f"Toilets Searched: {loc_id - 7000}"
    
    # Recruits: 8000 + count (8001-8065) - expanded to 65
    if 8001 <= loc_id <= 8065:
        return f"Characters Recruited: {loc_id - 8000}"
    
    # Containers: 9000 + count (9001-9880) - expanded to 880
    if 9001 <= loc_id <= 9880:
        return f"Containers Looted: {loc_id - 9000}"
    
    # Per-mode locations: 10000 + (mode_id * 100) + offset
    # offset 1-30 = day start, 31-60 = day clear, 99 = victory
    if 10000 <= loc_id <= 12199:
        mode_offset = loc_id - 10000
        mode_id = mode_offset // 100
        offset = mode_offset % 100
        
        mode_name = MODE_INFO.get(mode_id, f"Mode {mode_id}")
        
        if offset == 99:
            return f"[{mode_name}] Victory"
        elif 31 <= offset <= 60:
            return f"[{mode_name}] Day {offset - 30} Clear"
        elif 1 <= offset <= 30:
            return f"[{mode_name}] Day {offset} Start"
        else:
            return f"[{mode_name}] Unknown {offset}"
    
    return f"Unknown Location {loc_id}"


CONFIG_FILE = Path.home() / ".drtc_ap_client.json"

# Dark theme colors
DARK_BG = "#1a1a1a"
DARK_FG = "#e0e0e0"
DARK_ENTRY_BG = "#2d2d2d"
DARK_FRAME_BG = "#242424"
DARK_ACCENT = "#3d3d3d"
DARK_BORDER = "#404040"


class APClient:
    """Core Archipelago client logic with in-game integration."""
    
    def __init__(self, log_callback, status_callback):
        self.log = log_callback
        self.set_status = status_callback
        
        self.server: str = ""
        self.slot: str = ""
        self.password: str = ""
        self.save_path: Path = DEFAULT_SAVE_PATH
        
        self.ws = None
        self.connected: bool = False
        self.slot_info: Dict = {}
        self.team: int = 0
        self.players: Dict[int, str] = {}
        
        self.locations_checked: Set[int] = set()
        self.items_received: List[Dict] = []
        self.items_sent_to_game: Set[int] = set()
        self.item_queue: queue.Queue = queue.Queue()
        
        # ID to name mappings from DataPackage
        self.item_id_to_name: Dict[int, str] = {}
        self.location_id_to_name: Dict[int, str] = {}
        
        # Also store all games' data for cross-game lookups
        self.all_items: Dict[int, str] = {}
        self.all_locations: Dict[int, str] = {}
        
        self.goal_modes: Set[str] = {"normal"}  # Default to normal if not specified
        self.completed_goal_modes: Set[str] = set()  # Track which goal modes we've beaten
        
        self._running = False
        self.loop = None
    
    @property
    def inbox_path(self) -> Path:
        return self.save_path / "ap_inbox.txt"
    
    @property
    def outbox_path(self) -> Path:
        return self.save_path / "ap_outbox.txt"
    
    @property
    def status_path(self) -> Path:
        return self.save_path / "ap_status.txt"
    
    def write_status(self, status: str):
        try:
            self.status_path.write_text(status)
        except Exception as e:
            self.log(f"Error writing status: {e}", "error")
    
    def check_outbox(self) -> List[int]:
        try:
            if not self.outbox_path.exists():
                return []
            
            content = self.outbox_path.read_text().strip()
            if content:
                self.log(f"DEBUG: Outbox raw content: '{content}'", "debug")
                self.outbox_path.write_text("")
                locations = []
                for part in content.split(","):
                    part = part.strip()
                    if part:
                        try:
                            loc_id = int(part)
                            self.log(f"DEBUG: Parsed location ID: {loc_id}", "debug")
                            if loc_id not in self.locations_checked:
                                self.locations_checked.add(loc_id)
                                locations.append(loc_id)
                        except ValueError:
                            self.log(f"DEBUG: Failed to parse: '{part}'", "error")
                return locations
        except Exception as e:
            self.log(f"Error reading outbox: {e}", "error")
        return []
    
    def send_item_to_game(self, item_id: int) -> bool:
        """Append item to inbox. Returns True if written successfully."""
        try:
            local_id = item_id - BASE_ID
            
            # Append to existing content with comma separator (batch mode)
            if self.inbox_path.exists():
                content = self.inbox_path.read_text().strip()
                if content:
                    # Append to existing items
                    self.inbox_path.write_text(f"{content},{local_id}")
                else:
                    self.inbox_path.write_text(str(local_id))
            else:
                self.inbox_path.write_text(str(local_id))
            return True
        except Exception as e:
            self.log(f"Error writing inbox: {e}", "error")
            return False
    
    def get_item_name(self, item_id: int) -> str:
        """Get item name from ID, checking all sources."""
        # Check DataPackage data first (all games)
        if item_id in self.all_items:
            return self.all_items[item_id]
        # Check our game's mapping
        if item_id in self.item_id_to_name:
            return self.item_id_to_name[item_id]
        # Fall back to local lookup
        local_id = item_id - BASE_ID
        return ITEM_NAMES.get(local_id, f"Unknown Item {item_id}")
    
    def get_location_name_by_id(self, loc_id: int) -> str:
        """Get location name from ID, checking all sources."""
        # Check DataPackage data first (all games)
        if loc_id in self.all_locations:
            return self.all_locations[loc_id]
        # Check our game's mapping
        if loc_id in self.location_id_to_name:
            return self.location_id_to_name[loc_id]
        # Fall back to local lookup
        local_id = loc_id - BASE_ID
        return get_location_name(local_id)
    
    def get_player_name(self, player_id: int) -> str:
        """Get player name from ID."""
        return self.players.get(player_id, f"Player {player_id}")
    
    async def send_message(self, msg: dict):
        if self.ws:
            await self.ws.send(json.dumps([msg]))
    
    async def handle_message(self, msg: dict):
        cmd = msg.get("cmd", "")
        
        if cmd == "RoomInfo":
            self.log("Connected to room, requesting data...", "info")
            # Request data package for ALL games in the room
            games = msg.get("games", [])
            self.log(f"Games in room: {len(games)} games", "info")
            await self.send_message({
                "cmd": "GetDataPackage",
                "games": games  # Request all games for cross-game lookups
            })
            await self.send_connect()
        
        elif cmd == "DataPackage":
            data = msg.get("data", {}).get("games", {})
            for game_name, game_data in data.items():
                items = game_data.get("item_name_to_id", {})
                locations = game_data.get("location_name_to_id", {})
                # Store reverse mappings for all games
                for name, id in items.items():
                    self.all_items[id] = name
                for name, id in locations.items():
                    self.all_locations[id] = name
                # Also store our game's specific mapping
                if game_name == GAME_NAME:
                    self.item_id_to_name.update({v: k for k, v in items.items()})
                    self.location_id_to_name.update({v: k for k, v in locations.items()})
            self.log(f"Loaded data for {len(data)} game(s): {', '.join(data.keys())}", "info")
        
        elif cmd == "Connected":
            self.connected = True
            self.team = msg.get("team", 0)
            self.slot_info = msg.get("slot_info", {})
            checked = msg.get("checked_locations", [])
            self.locations_checked = set(loc - BASE_ID for loc in checked)
            
            # Parse slot_data for goal_modes
            slot_data = msg.get("slot_data", {})
            if "goal_modes" in slot_data:
                self.goal_modes = set(slot_data["goal_modes"])
                self.log(f"  Goal modes: {', '.join(self.goal_modes)}", "info")
            
            # Check already-completed locations for goal mode victories
            self.completed_goal_modes = set()
            for loc in self.locations_checked:
                if 10000 <= loc <= 12199:
                    mode_offset = loc - 10000
                    mode_id = mode_offset // 100
                    offset = mode_offset % 100
                    if offset == 99:  # Victory location
                        mode_key = MODE_ID_TO_KEY.get(mode_id)
                        if mode_key and mode_key in self.goal_modes:
                            self.completed_goal_modes.add(mode_key)
            
            if self.completed_goal_modes:
                remaining = self.goal_modes - self.completed_goal_modes
                self.log(f"  Goals completed: {', '.join(self.completed_goal_modes)} ({len(self.completed_goal_modes)}/{len(self.goal_modes)})", "info")
                if remaining:
                    self.log(f"  Goals remaining: {', '.join(remaining)}", "info")
            
            for player in msg.get("players", []):
                self.players[player["slot"]] = player["name"]
            
            slot_num = msg.get("slot", 0)
            self.log(f"✓ Connected as {self.slot} (Slot {slot_num})", "success")
            self.log(f"  Players: {', '.join(self.players.values())}", "info")
            self.log(f"  Already checked: {len(self.locations_checked)} locations", "info")
            self.set_status("Connected", "#00ff00")
            self.write_status("CONNECTED")
        
        elif cmd == "ReceivedItems":
            start_index = msg.get("index", 0)
            for i, item in enumerate(msg.get("items", [])):
                item_index = start_index + i
                item_id = item["item"]
                sender = self.players.get(item["player"], "Server")
                item_name = self.get_item_name(item_id)
                
                if item_index not in self.items_sent_to_game:
                    self.items_received.append(item)
                    self.item_queue.put((item_index, item_id))
                    self.log(f"⬇ Received: {item_name} from {sender}", "item")
        
        elif cmd == "PrintJSON":
            text_parts = []
            for part in msg.get("data", []):
                if isinstance(part, dict):
                    part_type = part.get("type")
                    part_text = part.get("text", "")
                    
                    if part_type == "player_id":
                        # Resolve player ID to name
                        try:
                            player_id = int(part_text)
                            text_parts.append(self.get_player_name(player_id))
                        except ValueError:
                            text_parts.append(part_text)
                    
                    elif part_type == "item_id":
                        # Resolve item ID to name
                        try:
                            item_id = int(part_text)
                            text_parts.append(self.get_item_name(item_id))
                        except ValueError:
                            text_parts.append(part_text)
                    
                    elif part_type == "location_id":
                        # Resolve location ID to name
                        try:
                            loc_id = int(part_text)
                            text_parts.append(self.get_location_name_by_id(loc_id))
                        except ValueError:
                            text_parts.append(part_text)
                    
                    else:
                        # Regular text or unknown type - just use the text
                        text_parts.append(part_text)
                else:
                    text_parts.append(str(part))
            
            text = "".join(text_parts)
            if text:
                self.log(f"[Server] {text}", "server")
        
        elif cmd == "ConnectionRefused":
            errors = msg.get("errors", ["Unknown error"])
            self.log(f"Connection refused: {', '.join(errors)}", "error")
            self.set_status("Refused", "#ff4444")
            self.write_status("REFUSED")
    
    async def send_connect(self):
        msg = {
            "cmd": "Connect",
            "game": GAME_NAME,
            "name": self.slot,
            "uuid": "",
            "version": {"major": 0, "minor": 5, "build": 1, "class": "Version"},
            "items_handling": 0b111,
            "tags": [],
            "password": self.password,
            "slot_data": True,
        }
        await self.send_message(msg)
    
    async def send_location_checks(self, locations: List[int]):
        if not self.connected or not locations:
            return
        
        ap_locations = [loc + BASE_ID for loc in locations]
        await self.send_message({"cmd": "LocationChecks", "locations": ap_locations})
        
        for loc in locations:
            loc_name = get_location_name(loc)
            self.log(f"⬆ Checked: {loc_name}", "location")
            
            # Check if this is a victory location (10000 + mode*100 + 99)
            if 10000 <= loc <= 12199:
                mode_offset = loc - 10000
                mode_id = mode_offset // 100
                offset = mode_offset % 100
                
                if offset == 99:  # Victory!
                    mode_key = MODE_ID_TO_KEY.get(mode_id)
                    mode_name = MODE_INFO.get(mode_id, f"Mode {mode_id}")
                    
                    if mode_key and mode_key in self.goal_modes:
                        # Add to completed goals
                        self.completed_goal_modes.add(mode_key)
                        remaining = self.goal_modes - self.completed_goal_modes
                        
                        if remaining:
                            # Still more goals to complete
                            self.log(f"🏆 {mode_name} Victory! ({len(self.completed_goal_modes)}/{len(self.goal_modes)} goals)", "success")
                            self.log(f"   Remaining: {', '.join(remaining)}", "info")
                        else:
                            # ALL goal modes complete!
                            self.log(f"🎉 ALL GOALS COMPLETE - {mode_name} was the final victory!", "success")
                            await self.trigger_goal_complete()
                    else:
                        self.log(f"ℹ {mode_name} Victory (not a goal mode)", "info")
    
    async def process_item_queue(self):
        """Process all pending items - writes them all to inbox at once (batch mode)."""
        items_sent = []
        while not self.item_queue.empty():
            try:
                item_index, item_id = self.item_queue.get_nowait()
                if self.send_item_to_game(item_id):
                    self.items_sent_to_game.add(item_index)
                    items_sent.append((item_index, item_id))
                else:
                    # Put it back if failed
                    self.item_queue.put((item_index, item_id))
                    break
            except queue.Empty:
                break
        
        # Log all items sent in this batch
        for item_index, item_id in items_sent:
            item_name = self.get_item_name(item_id)
            self.log(f"→ Sent to game: {item_name}", "game")
    
    async def run(self):
        self._running = True
        self.loop = asyncio.get_event_loop()
        url = f"wss://{self.server}" if not self.server.startswith("ws") else self.server
        
        self.log(f"Connecting to {self.server}...", "info")
        self.set_status("Connecting...", "#ffcc00")
        self.write_status("CONNECTING")
        
        try:
            # max_size=None removes the 1MB default limit for large multiworlds
            async with websockets.connect(url, max_size=None) as ws:
                self.ws = ws
                self.log("WebSocket connected!", "success")
                
                monitor_task = asyncio.create_task(self.file_monitor())
                
                try:
                    async for message in ws:
                        if not self._running:
                            break
                        try:
                            data = json.loads(message)
                            for msg in data:
                                await self.handle_message(msg)
                        except json.JSONDecodeError:
                            pass
                except websockets.exceptions.ConnectionClosed as e:
                    self.log(f"Connection closed: {e}", "error")
                finally:
                    monitor_task.cancel()
        
        except Exception as e:
            self.log(f"Connection error: {e}", "error")
        
        self.connected = False
        self.ws = None
        self.set_status("Disconnected", "#ff4444")
        self.write_status("DISCONNECTED")
        self._running = False
    
    async def file_monitor(self):
        while self._running:
            if self.connected:
                locations = self.check_outbox()
                if locations:
                    await self.send_location_checks(locations)
                
                for _ in range(5):
                    if self.item_queue.empty():
                        break
                    await self.process_item_queue()
                    await asyncio.sleep(0.15)
            
            await asyncio.sleep(0.25)
    
    async def trigger_goal_complete(self):
        """Send goal completion to server."""
        await self.send_message({
            "cmd": "StatusUpdate",
            "status": 30  # CLIENT_GOAL
        })
    
    def stop(self):
        self._running = False
        self.write_status("DISCONNECTED")
        if self.ws and self.loop and self.loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(self.ws.close(), self.loop)
            except:
                pass


# =============================================================================
# GUI APPLICATION
# =============================================================================

class RE4ClientApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("700x600")
        self.root.minsize(600, 500)
        self.root.configure(bg=DARK_BG)
        
        self.setup_dark_theme()
        
        self.client: Optional[APClient] = None
        self.client_thread = None
        self.loop = None
        
        self.config = self.load_config()
        
        self.server_var = tk.StringVar()
        self.slot_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.path_var = tk.StringVar()
        
        self.create_widgets()
        self.load_settings()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def setup_dark_theme(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(".", background=DARK_BG, foreground=DARK_FG, 
                       fieldbackground=DARK_ENTRY_BG)
        style.configure("TFrame", background=DARK_FRAME_BG)
        style.configure("TLabel", background=DARK_FRAME_BG, foreground=DARK_FG)
        style.configure("TButton", background=DARK_ACCENT, foreground=DARK_FG,
                       borderwidth=1, focuscolor=DARK_ACCENT)
        style.map("TButton", 
                 background=[("active", DARK_BORDER), ("pressed", DARK_BG)])
        style.configure("TEntry", fieldbackground=DARK_ENTRY_BG, 
                       foreground=DARK_FG, insertcolor=DARK_FG)
        style.configure("TLabelframe", background=DARK_FRAME_BG)
        style.configure("TLabelframe.Label", background=DARK_FRAME_BG, 
                       foreground=DARK_FG)
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        header = ttk.Label(main_frame, text=APP_NAME, font=("Helvetica", 14, "bold"))
        header.pack(pady=(0, 5))
        
        version_label = ttk.Label(main_frame, text=f"v{APP_VERSION}", font=("Helvetica", 9))
        version_label.pack(pady=(0, 10))
        
        conn_frame = ttk.LabelFrame(main_frame, text="Connection", padding="10")
        conn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(conn_frame, text="Server:").grid(row=0, column=0, sticky="w", pady=2)
        self.server_entry = ttk.Entry(conn_frame, textvariable=self.server_var, width=35)
        self.server_entry.grid(row=0, column=1, columnspan=2, sticky="ew", pady=2, padx=5)
        
        ttk.Label(conn_frame, text="Slot Name:").grid(row=1, column=0, sticky="w", pady=2)
        self.slot_entry = ttk.Entry(conn_frame, textvariable=self.slot_var, width=35)
        self.slot_entry.grid(row=1, column=1, columnspan=2, sticky="ew", pady=2, padx=5)
        
        ttk.Label(conn_frame, text="Password:").grid(row=2, column=0, sticky="w", pady=2)
        self.password_entry = ttk.Entry(conn_frame, textvariable=self.password_var, show="*", width=35)
        self.password_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=2, padx=5)
        
        conn_frame.columnconfigure(1, weight=1)
        
        path_frame = ttk.LabelFrame(main_frame, text="Game Save Path", padding="10")
        path_frame.pack(fill=tk.X, pady=5)
        
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=50)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.browse_btn = ttk.Button(path_frame, text="Browse", command=self.browse_path)
        self.browse_btn.pack(side=tk.LEFT)
        
        sync_frame = ttk.Frame(main_frame)
        sync_frame.pack(fill=tk.X, pady=5)
        
        self.sync_btn = ttk.Button(sync_frame, text="Sync from Game", command=self.sync_from_game)
        self.sync_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.push_btn = ttk.Button(sync_frame, text="Push to Game", command=self.push_to_game)
        self.push_btn.pack(side=tk.LEFT)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.connect_btn = ttk.Button(btn_frame, text="Connect", command=self.connect)
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.disconnect_btn = ttk.Button(btn_frame, text="Disconnect", command=self.disconnect, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.clear_btn = ttk.Button(btn_frame, text="Clear Log", command=self.clear_log)
        self.clear_btn.pack(side=tk.RIGHT)
        
        self.status_label = ttk.Label(main_frame, text="Disconnected", font=("Helvetica", 10, "bold"))
        self.status_label.pack(pady=5)
        
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=15, wrap=tk.WORD, state=tk.DISABLED,
            bg=DARK_ENTRY_BG, fg=DARK_FG, insertbackground=DARK_FG, font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self.log_text.tag_configure("info", foreground="#ffffff")      # White - general info
        self.log_text.tag_configure("success", foreground="#00ff00")   # Bright green
        self.log_text.tag_configure("error", foreground="#ff4444")     # Red
        self.log_text.tag_configure("item", foreground="#ffcc00")      # Gold - items received
        self.log_text.tag_configure("location", foreground="#00ccff")  # Cyan - locations checked
        self.log_text.tag_configure("game", foreground="#ff99ff")      # Pink - sent to game
        self.log_text.tag_configure("server", foreground="#cc99ff")    # Lavender - server messages
        self.log_text.tag_configure("debug", foreground="#aaaaaa")     # Grey - debug only
    
    def log(self, message: str, tag: str = "info"):
        def _log():
            self.log_text.configure(state=tk.NORMAL)
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
        self.root.after(0, _log)
    
    def set_status(self, text: str, color: str):
        def _status():
            self.status_label.configure(text=text, foreground=color)
        self.root.after(0, _status)
    
    def clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def browse_path(self):
        path = filedialog.askdirectory(
            title="Select RE4 Save Folder",
            initialdir=self.path_var.get() or str(DEFAULT_SAVE_PATH)
        )
        if path:
            self.path_var.set(path)
    
    def load_config(self) -> dict:
        try:
            if CONFIG_FILE.exists():
                return json.loads(CONFIG_FILE.read_text())
        except:
            pass
        return {}
    
    def save_config(self):
        config = {
            "server": self.server_var.get(),
            "slot": self.slot_var.get(),
            "save_path": self.path_var.get(),
        }
        try:
            CONFIG_FILE.write_text(json.dumps(config, indent=2))
        except:
            pass
    
    def load_settings(self):
        self.server_var.set(self.config.get("server", "archipelago.gg:38281"))
        self.slot_var.set(self.config.get("slot", ""))
        self.path_var.set(self.config.get("save_path", str(DEFAULT_SAVE_PATH)))
    
    def sync_from_game(self):
        save_path = Path(self.path_var.get())
        config_path = save_path / "ap_config.txt"
        
        if not config_path.exists():
            messagebox.showinfo("Sync from Game", 
                "No game config found.\n\nConfigure connection in the game's\nArchipelago menu first.")
            return
        
        try:
            content = config_path.read_text().strip()
            if not content:
                messagebox.showinfo("Sync from Game", "Game config file is empty.")
                return
            
            parts = content.split("|")
            if len(parts) >= 1 and parts[0]:
                self.server_var.set(parts[0])
            if len(parts) >= 2 and parts[1]:
                self.slot_var.set(parts[1])
            if len(parts) >= 3:
                self.password_var.set(parts[2])
            
            self.log(f"Synced from game: {parts[0]} / {parts[1] if len(parts) > 1 else '?'}", "success")
            self.save_config()
            
        except Exception as e:
            messagebox.showerror("Sync Error", f"Failed to read game config:\n{e}")
    
    def push_to_game(self):
        save_path = Path(self.path_var.get())
        
        if not save_path.exists():
            messagebox.showerror("Error", f"Save path does not exist:\n{save_path}")
            return
        
        config_path = save_path / "ap_config.txt"
        
        try:
            server = self.server_var.get().strip()
            slot = self.slot_var.get().strip()
            password = self.password_var.get()
            
            content = f"{server}|{slot}|{password}|0"
            config_path.write_text(content)
            
            self.log(f"Pushed to game: {server} / {slot}", "success")
            
        except Exception as e:
            messagebox.showerror("Push Error", f"Failed to write game config:\n{e}")
    
    def validate_inputs(self) -> bool:
        if not self.server_var.get().strip():
            messagebox.showerror("Error", "Please enter a server address")
            return False
        if not self.slot_var.get().strip():
            messagebox.showerror("Error", "Please enter your slot name")
            return False
        if not self.path_var.get().strip():
            messagebox.showerror("Error", "Please select your save path")
            return False
        
        save_path = Path(self.path_var.get())
        if not save_path.exists():
            messagebox.showerror("Error", f"Save path does not exist:\n{save_path}")
            return False
        
        return True
    
    def connect(self):
        if not self.validate_inputs():
            return
        
        self.save_config()
        
        self.connect_btn.configure(state=tk.DISABLED)
        self.disconnect_btn.configure(state=tk.NORMAL)
        self.server_entry.configure(state=tk.DISABLED)
        self.slot_entry.configure(state=tk.DISABLED)
        self.password_entry.configure(state=tk.DISABLED)
        self.path_entry.configure(state=tk.DISABLED)
        self.browse_btn.configure(state=tk.DISABLED)
        self.sync_btn.configure(state=tk.DISABLED)
        self.push_btn.configure(state=tk.DISABLED)
        
        self.client = APClient(self.log, self.set_status)
        self.client.server = self.server_var.get().strip()
        self.client.slot = self.slot_var.get().strip()
        self.client.password = self.password_var.get()
        self.client.save_path = Path(self.path_var.get())
        
        self.client_thread = threading.Thread(target=self.run_client, daemon=True)
        self.client_thread.start()
    
    def run_client(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.client.run())
        except Exception as e:
            self.log(f"Client error: {e}", "error")
        finally:
            self.loop.close()
            self.root.after(0, self.on_disconnect)
    
    def disconnect(self):
        if self.client:
            self.client.stop()
        self.log("Disconnecting...", "info")
    
    def on_disconnect(self):
        self.connect_btn.configure(state=tk.NORMAL)
        self.disconnect_btn.configure(state=tk.DISABLED)
        self.server_entry.configure(state=tk.NORMAL)
        self.slot_entry.configure(state=tk.NORMAL)
        self.password_entry.configure(state=tk.NORMAL)
        self.path_entry.configure(state=tk.NORMAL)
        self.browse_btn.configure(state=tk.NORMAL)
        self.sync_btn.configure(state=tk.NORMAL)
        self.push_btn.configure(state=tk.NORMAL)
        self.set_status("Disconnected", "#888888")
    
    def on_close(self):
        if self.client:
            self.client.stop()
        self.save_config()
        self.root.destroy()
    
    def run(self):
        self.log(f"Welcome to {APP_NAME}", "info")
        self.log("Enter server details and click Connect to start", "info")
        self.root.mainloop()


if __name__ == "__main__":
    app = RE4ClientApp()
    app.run()
