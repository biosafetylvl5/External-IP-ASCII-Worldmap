# Worldmap IP location display

# Imports
import requests
import os
import sys
import json
import time
import argparse
import worldmap
import shutil

# Rich imports
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich import box

###
# LAT (Y): 86 (up) -86 (down)
# LON (X): -180 (left) 180 (right)
###

latRange = 86
lonRange = 180

worldMap = None
curSize = (-1, -1)

paddingFix = (-5, -13)  # Geo coords, fixes worldmap placement
console = Console()

def replace_str_index(text, index=0, replacement=''):
    return "{}{}{}".format(text[:int(index)], replacement, text[int(index)+1:])

def get_external_ip_location():
    try:
        # Get external IP
        external_ip = requests.get("https://f13rce.net/ip.php", timeout=5).content.decode("utf-8").strip()
        
        # Get geolocation data for the IP
        url = f"https://ipinfo.io/{external_ip}/json"
        r = requests.get(url, timeout=5)
        data = json.loads(r.content.decode("utf-8"))
        
        if not data.get("loc"):
            return None, None, None, None
        
        loc = data["loc"].split(",")
        geo = (float(loc[0]), float(loc[1]))
        
        # Add padding fix
        adjusted_geo = (geo[0] + paddingFix[0], geo[1] + paddingFix[1])
        
        # Get city and country
        city = data.get("city", "Unknown")
        country = data.get("country", "Unknown")
        
        return external_ip, adjusted_geo, city, country
    except Exception as e:
        console.print(f"[bold red]Error fetching IP information:[/bold red] {e}")
        return None, None, None, None

def geo_to_ascii(geo):
    global worldMap
    if worldMap is None:
        return None

    try:
        lat = int(len(worldMap) - len(worldMap) / (latRange * 2) * (geo[0] + latRange))
        lon = int(len(worldMap[0]) / (lonRange * 2) * (geo[1] + lonRange))
        
        # Ensure coordinates are within bounds
        lat = max(0, min(lat, len(worldMap) - 1))
        lon = max(0, min(lon, len(worldMap[0]) - 1))
        
        return (lat, lon)
    except Exception as e:
        console.print(f"[bold red]Error converting geo coordinates:[/bold red] {e}")
        return (0, 0)

def get_terminal_size():
    try:
        # First try shutil which is more reliable
        columns, rows = shutil.get_terminal_size()
        return rows, columns
    except Exception as e:
        try:
            # Fallback to os.get_terminal_size
            columns, rows = os.get_terminal_size()
            return rows, columns
        except Exception as e:
            # If all else fails, use a default size
            console.print(f"[bold yellow]Warning: Could not determine terminal size, using default.[/bold yellow] Error: {e}")
            return 24, 80

def draw(refreshRate=10.0, ip_check_interval=60):
    global curSize
    global worldMap
    global console

    refreshTime = 1.0 / refreshRate
    
    # Initialize IP data
    ip, geo, city, country = get_external_ip_location()
    if geo is None:
        console.print("[bold red]Could not determine your location.[/bold red]")
        return
    
    last_ip_check = time.time()
    
    while True:
        try:
            # Check if it's time to refresh the IP data
            current_time = time.time()
            if current_time - last_ip_check > ip_check_interval:
                new_ip, new_geo, new_city, new_country = get_external_ip_location()
                if new_ip and new_ip != ip:
                    ip, geo, city, country = new_ip, new_geo, new_city, new_country
                    console.print(f"[bold green]IP changed to:[/bold green] {ip}")
                last_ip_check = current_time
            
            # Get terminal size
            terminal_height, terminal_width = get_terminal_size()
            
            if curSize[0] != terminal_height or curSize[1] != terminal_width:
                curSize = (terminal_height, terminal_width)
                try:
                    worldMap = worldmap.convertImageToAscii("worldmap.png", terminal_width, 0.43, False)
                except AttributeError:
                    # If the first attempt fails, try the alternative function name
                    try:
                        console.print("[bold yellow]Warning: Using alternative function name 'covertImageToAscii'[/bold yellow]")
                        worldMap = worldmap.covertImageToAscii("worldmap.png", terminal_width, 0.43, False)
                    except Exception as e:
                        console.print(f"[bold red]Error creating world map:[/bold red] {e}")
                        time.sleep(5)
                        continue
                except Exception as e:
                    console.print(f"[bold red]Error creating world map:[/bold red] {e}")
                    time.sleep(5)
                    continue

            worldMapTemp = worldMap.copy()
            
            # Mark location on the map
            pos = geo_to_ascii(geo)
            if pos and 0 <= pos[0] < len(worldMapTemp) and 0 <= pos[1] < len(worldMapTemp[pos[0]]):
                worldMapTemp[pos[0]] = replace_str_index(worldMapTemp[pos[0]], pos[1], "@")

            # Create the map text
            map_text = Text()
            for row in worldMapTemp:
                for char in row:
                    if char == "@":
                        map_text.append(char, style="bold yellow")
                    else:
                        map_text.append(char, style="green")
                map_text.append("\n")

            # Create layout
            layout = Layout()
            layout.split(
                Layout(name="header", size=3),
                Layout(name="main")
            )
            
            # Create header with IP info
            header_text = Text.from_markup(
                f"[bold cyan]External IP:[/bold cyan] [yellow]{ip}[/yellow]\n"
                f"[bold cyan]Location:[/bold cyan] [yellow]{city}, {country}[/yellow]\n"
                f"[dim](Updates every {ip_check_interval} seconds)[/dim]"
            )
            layout["header"].update(Panel(header_text, box=box.ROUNDED))
            
            # Update main content with map
            layout["main"].update(Panel(map_text, box=box.ROUNDED))
            
            # Clear screen and render
            os.system('cls' if os.name == 'nt' else 'clear')
            console.print(layout)
            
            # Until next time!
            time.sleep(refreshTime)
            
        except Exception as e:
            console.print(f"[bold red]An error occurred:[/bold red] {e}")
            time.sleep(5)  # Wait a bit before retrying

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A tool to display your external IP location on an ASCII world map.")
    parser.add_argument("-r", "--refreshrate", help="Refresh rate of the worldmap. The value is X times per second. Default = 10")
    parser.add_argument("-i", "--ipcheckinterval", help="How often to check for IP changes (in seconds). Default = 60")

    # parse arguments
    args = parser.parse_args()

    try:
        rr = 10.0
        if args.refreshrate:
            if float(args.refreshrate) == 0:
                console.print("[bold red]Refresh rate cannot be 0! This will cause a division by 0.[/bold red]")
                sys.exit(1)
            rr = float(args.refreshrate)

        ip_interval = 60
        if args.ipcheckinterval:
            ip_interval = int(args.ipcheckinterval)

        # Draw the map with your IP location
        draw(rr, ip_interval)
    except KeyboardInterrupt:
        console.print("[bold cyan]Exiting...[/bold cyan]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]Fatal error:[/bold red] {e}")
        sys.exit(1)
