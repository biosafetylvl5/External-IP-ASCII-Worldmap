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
import unicodedata

# Rich imports
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich import box
from rich.measure import Measurement

###
# LAT (Y): 90 (up) -90 (down)
# LON (X): -180 (left) 180 (right)
###

LAT_RANGE = 90  # Changed from 86 to standard 90 degrees
LON_RANGE = 180

worldMap = None
curSize = (-1, -1)
last_display_content = ""  # Store the last displayed content to avoid unnecessary refreshes
markOcean = False

# Removed hardcoded padding fix
console = Console()

def get_char_width(char):
    """Get the display width of a character, accounting for wide characters"""
    return 2 if unicodedata.east_asian_width(char) in ('F', 'W') else 1

def ensure_line_length(line, target_length):
    """Ensure each line is exactly the target length by truncating or padding"""
    # Calculate current visible width (accounting for wide characters)
    current_width = sum(get_char_width(c) for c in line)
    
    if current_width > target_length:
        # Truncate the line
        result = ""
        width = 0
        for char in line:
            char_width = get_char_width(char)
            if width + char_width <= target_length:
                result += char
                width += char_width
            else:
                break
        return result
    else:
        # Pad the line with spaces
        return line + " " * (target_length - current_width)

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
        
        # Get city and country
        city = data.get("city", "Unknown")
        region = data.get("region", "Unknown")
        country = data.get("country", "Unknown")
        
        return external_ip, geo, city, region, country
    except Exception as e:
        console.print(f"[bold red]Error fetching IP information:[/bold red] {e}")
        return None, None, None, None

def geo_to_ascii(geo, map_height, map_width):
    """
    Convert geographical coordinates to ASCII map coordinates
    Using improved mapping formula that properly handles the entire range
    """
    try:
        # Improved latitude mapping from [-90, 90] to [0, map_height]
        # Note: We invert and shift because in ASCII maps, 0 is at the top
        lat_normalized = (90 - geo[0]) / 180  # Normalize to [0, 1]
        lat = int(lat_normalized * map_height*(1/0.85))
        
        # Improved longitude mapping from [-180, 180] to [0, map_width]
        lon_normalized = (geo[1] + 180) / 360  # Normalize to [0, 1]
        lon = int(lon_normalized * map_width)
        
        # Ensure coordinates are within bounds
        lat = max(0, min(lat, map_height - 1))
        lon = max(0, min(lon, map_width - 1))
        
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

def calculate_effective_width(terminal_width):
    """Calculate the effective width available for the map content accounting for panel borders"""
    # For a Rich panel with ROUNDED box style, we lose 2 characters on each side
    panel_border_width = 4
    return terminal_width - panel_border_width

def generate_display_content(ip, city, region, country, worldMapTemp, ip_check_interval):
    """Generate the display content as a string for comparison"""
    content = f"IP: {ip}, Location: {city}, {region}, {country}, Updates every: {ip_check_interval}\n"
    
    for row in worldMapTemp:
        content += row + "\n"
    
    return content

def draw(refreshRate=10.0, ip_check_interval=60):
    global curSize
    global worldMap
    global console
    global last_display_content

    refreshTime = 1.0 / refreshRate
    
    # Initialize IP data
    ip, geo, city, region, country = get_external_ip_location()
    if geo is None:
        console.print("[bold red]Could not determine your location.[/bold red]")
        return
    
    last_ip_check = time.time()
    update_display = True  # Force initial display
    map_needs_update = True
    
    while True:
        try:
            # Check if it's time to refresh the IP data
            current_time = time.time()
            ip_changed = False
            
            if current_time - last_ip_check > ip_check_interval:
                new_ip, new_geo, new_city, new_region, new_country = get_external_ip_location()
                if new_ip and (new_ip != ip):
                    ip, geo, city, region, country = new_ip, new_geo, new_city, new_region, new_country
                    #console.print(f"[bold green]IP or location changed:[/bold green] {ip} - {city}, {country}")
                    update_display = True
                    ip_changed = True
                last_ip_check = current_time
            
            # Get terminal size
            terminal_height, terminal_width = get_terminal_size()
            
            # Calculate effective width for the map content
            effective_width = calculate_effective_width(terminal_width)
            
            # Check if terminal size changed
            if curSize[0] != terminal_height or curSize[1] != terminal_width:
                curSize = (terminal_height, terminal_width)
                try:
                    # Calculate appropriate aspect ratio based on terminal dimensions
                    # Most terminals have characters roughly twice as tall as they are wide
                    # So we adjust the aspect ratio to maintain geographical proportions
                    aspect_ratio = ((terminal_height - 5) / (effective_width)) * 2.2
                    
                    # Use the correct function name from the worldmap module
                    worldMap = worldmap.convertImageToAscii("map.png", effective_width, aspect_ratio, False)
                except AttributeError:
                    # If the first attempt fails, try the alternative function name
                    try:
                        #console.print("[bold yellow]Warning: Using alternative function name 'covertImageToAscii'[/bold yellow]")
                        worldMap = worldmap.covertImageToAscii("map.png", effective_width, aspect_ratio, False)
                    except Exception as e:
                        console.print(f"[bold red]Error creating world map:[/bold red] {e}")
                        time.sleep(5)
                        continue
                except Exception as e:
                    console.print(f"[bold red]Error creating world map:[/bold red] {e}")
                    time.sleep(5)
                    continue
                
                # Ensure all lines are of consistent length
                for i in range(len(worldMap)):
                    worldMap[i] = ensure_line_length(worldMap[i], effective_width)
                
                update_display = True
                map_needs_update = True

            # Only process the map if we need to update the display
            if update_display:
                if map_needs_update or ip_changed:
                    worldMapTemp = worldMap.copy()
                    
                    # Mark your location on the map
                    map_height = len(worldMapTemp)
                    map_width = len(worldMapTemp[0]) if map_height > 0 else 0
                    
                    pos = geo_to_ascii(geo, map_height, map_width)
                    if pos and 0 <= pos[0] < map_height and 0 <= pos[1] < map_width:
                        worldMapTemp[pos[0]] = replace_str_index(worldMapTemp[pos[0]], pos[1], "X")
                    
                    # Double-check all lines are consistent length after modification
                    for i in range(len(worldMapTemp)):
                        worldMapTemp[i] = ensure_line_length(worldMapTemp[i], effective_width)
                    
                    map_needs_update = False
                
                # Generate current content for comparison
                current_content = generate_display_content(ip, city, region, country, worldMapTemp, ip_check_interval)
                
                # Only update the display if content has changed
                if current_content != last_display_content or update_display:
                    last_display_content = current_content
                    
                    # Create the map text
                    map_text = Text()
                    for row in worldMapTemp:
                        line_length = 0
                        for char in row:
                            if char == "X":
                                map_text.append(char, style="bold red")
                            elif char == "@":
                                map_text.append(char, style="yellow")
                            elif char == " " and markOcean:
                                map_text.append(".", style="grey")
                            else:
                                map_text.append(char, style="green")
                            line_length += get_char_width(char)
                            
                            # Safety check - if we're at the effective width, break
                            if line_length >= effective_width:
                                break
                                
                        map_text.append("\n")

                    # Create layout with appropriate sizes
                    layout = Layout()
                    header_size = 3  # Fixed size for header
                    layout.split(
                        Layout(name="header", size=header_size),
                        Layout(name="main", size=terminal_height - header_size - 2)  # Account for layout margins
                    )
                    
                    # Create header with IP info
                    header_text = Text.from_markup(
                        f"[bold cyan]External IP:[/bold cyan] [yellow]{ip}[/yellow] -- "
                        f"[bold cyan]Location:[/bold cyan] [yellow]{city}, {region}, {country}[/yellow] -- "
                        f"[dim](Updates every {ip_check_interval} seconds)[/dim]"
                    )
                    layout["header"].update(Panel(header_text, box=box.ROUNDED))
                    
                    # Update main content with map
                    layout["main"].update(Panel(map_text, box=box.ROUNDED))
                    
                    # Clear screen and render
                    os.system('cls' if os.name == 'nt' else 'clear')
                    console.print(layout)
                    
                    update_display = False
            
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

