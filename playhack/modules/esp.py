import time
import struct
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from ..core.memory import Memory
from ..core.offsets import Offsets

console = Console()

class ESP:
    def __init__(self, target_name="Poppy Playtime"):
        self.mem = Memory(target_name)
        self.players = []

    def update_players(self):
        # In a real scenario, we'd read the Player List pointer chain
        # Starting from LocalInstance root
        # For this prototype, we'll scan if the chain is broken
        if not self.players:
            import struct
            pattern = struct.pack('ff', 4.0, 7.0) # walk + sprint
            candidates = self.mem.find_pattern(pattern)
            self.players = [c - Offsets.WALK_SPEED for c in candidates]

    def get_player_data(self):
        data = []
        for addr in self.players:
            is_dead_raw = self.mem.read(addr + Offsets.IS_DEAD, 1)
            is_dead = struct.unpack('?', is_dead_raw)[0] if is_dead_raw else True
            
            # Position chain
            trans_ptr = self.mem.read_ptr(addr + Offsets.TRANSFORM)
            x = self.mem.read_float(trans_ptr + Offsets.POS_X) if trans_ptr else 0.0
            y = self.mem.read_float(trans_ptr + Offsets.POS_Y) if trans_ptr else 0.0
            z = self.mem.read_float(trans_ptr + Offsets.POS_Z) if trans_ptr else 0.0
            
            data.append({
                "address": hex(addr),
                "state": "[red]DEAD[/red]" if is_dead else "[green]ALIVE[/green]",
                "pos_str": f"({x:>7.2f}, {y:>7.2f}, {z:>7.2f})",
                "x": x, "y": y, "z": z
            })
        return data

def generate_table(esp_data) -> Table:
    table = Table(title="[bold cyan]Player List[/bold cyan]", expand=True)
    table.add_column("Index", justify="center", style="dim")
    table.add_column("State", justify="center")
    table.add_column("Position (X, Y, Z)", justify="left")

    for i, p in enumerate(esp_data):
        table.add_row(str(i), p['state'], p['pos_str'])
    return table

def generate_radar(esp_data) -> Panel:
    size = 15 # Radar grid size
    grid = [[" " for _ in range(size)] for _ in range(size)]
    center = size // 2
    grid[center][center] = "[blue]@[/blue]" # Local Player

    if len(esp_data) > 1:
        local = esp_data[0]
        scale = 5.0 # Units per grid cell
        for p in esp_data[1:]:
            # Relative coordinates
            dx = (p['x'] - local['x']) / scale
            dz = (p['z'] - local['z']) / scale
            
            # Map to grid
            gx = int(center + dx)
            gz = int(center - dz) # Invert Z for top-down map
            
            if 0 <= gx < size and 0 <= gz < size:
                if grid[gz][gx] == " ":
                    grid[gz][gx] = "[red]X[/red]"

    radar_text = "\n".join([" ".join(row) for row in grid])
    return Panel(radar_text, title="[bold green]Radar (Scale: 5.0)[/bold green]", border_style="green", padding=(1, 2))

def generate_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="middle"),
        Layout(name="status", size=5)
    )
    layout["middle"].split_row(
        Layout(name="main", ratio=2),
        Layout(name="radar", ratio=1)
    )
    return layout

def generate_status_panel(cheats_data) -> Panel:
    god = "[green]ON[/green]" if cheats_data['god'] else "[red]OFF[/red]"
    reach = "[green]ON[/green]" if cheats_data['reach'] else "[red]OFF[/red]"
    return Panel(
        f"God Mode: {god} | Infinite Reach: {reach}\nTarget: Poppy Playtime",
        title="[bold yellow]Cheat Status[/bold yellow]",
        border_style="yellow"
    )

def run(target):
    esp = ESP(target)
    layout = generate_layout()
    
    if not esp.mem.pid:
        console.print(f"[bold red][!] Target {target} not found. Simulation mode active.[/bold red]")
        sim_data = [
            {"address": "0x7F1000A0", "state": "[green]ALIVE[/green]", "pos_str": "(  0.00,   0.00,   0.00)", "x": 0.0, "y": 0.0, "z": 0.0},
            {"address": "0x7F1004B0", "state": "[red]DEAD[/red]", "pos_str": "(-10.00,   1.00,  15.00)", "x": -10.0, "y": 1.0, "z": 15.0},
            {"address": "0x7F1008C0", "state": "[green]ALIVE[/green]", "pos_str": "( 20.00,   2.10, -10.00)", "x": 20.0, "y": 2.1, "z": -10.0}
        ]
        cheats_data = {'god': False, 'reach': False}
        with Live(layout, refresh_per_second=4) as live:
            while True:
                layout["header"].update(Panel("[bold cyan]PlayHack ESP - Player Monitor[/bold cyan]"))
                layout["main"].update(generate_table(sim_data))
                layout["radar"].update(generate_radar(sim_data))
                layout["status"].update(generate_status_panel(cheats_data))
                time.sleep(1)
    
    with Live(layout, refresh_per_second=10) as live:
        while True:
            esp.update_players()
            data = esp.get_player_data()
            
            # Read cheat status from memory (simplified)
            p_local = esp.players[0] if esp.players else 0
            is_god = False
            if p_local:
                val = esp.mem.read(p_local + Offsets.IS_DEAD, 1)
                is_god = (struct.unpack('?', val)[0] == False) if val else False
            
            cheats_data = {'god': is_god, 'reach': False}
            
            layout["header"].update(Panel("[bold cyan]PlayHack ESP - Player Monitor[/bold cyan]"))
            layout["main"].update(generate_table(data))
            layout["radar"].update(generate_radar(data))
            layout["status"].update(generate_status_panel(cheats_data))
            time.sleep(0.1)
