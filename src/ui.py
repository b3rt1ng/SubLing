import sys
import shutil
import time

LIGHT_BLUE = (179, 205, 224)
BLUE = (0, 91, 150)
DARK_BLUE = (1, 31, 75)
SPIDER_WHITE = (226, 226, 226)
SPIDER_RED = (172, 2, 2)
GREEN = (46, 204, 113)
YELLOW = (241, 196, 15)


def whole_line():
    return " " * shutil.get_terminal_size().columns


def gradient_text(text, start_color=LIGHT_BLUE, end_color=BLUE):
    if not sys.stdout.isatty():
        return text
    
    result = ""
    length = len(text)
    for i, char in enumerate(text):
        ratio = i / max(length - 1, 1)
        r = int(start_color[0] + ratio * (end_color[0] - start_color[0]))
        g = int(start_color[1] + ratio * (end_color[1] - start_color[1]))
        b = int(start_color[2] + ratio * (end_color[2] - start_color[2]))
        result += f"\033[38;2;{r};{g};{b}m{char}"
    result += "\033[0m"
    return result


def colored_text(text, foreground_color, background_color=None):
    if not sys.stdout.isatty():
        return str(text)
    
    r, g, b = foreground_color
    if background_color:
        bg_r, bg_g, bg_b = background_color
        return f"\033[38;2;{r};{g};{b}m\033[48;2;{bg_r};{bg_g};{bg_b}m{text}\033[0m"
    else:
        return f"\033[38;2;{r};{g};{b}m{text}\033[0m"


def colorize_status(status):
    if 200 <= status < 300:
        return f"[{colored_text(status, GREEN)}]"
    elif 300 <= status < 400:
        return f"[{colored_text(status, YELLOW)}]"
    elif 400 <= status < 500:
        return f"[{colored_text(status, LIGHT_BLUE)}]"
    elif 500 <= status < 600:
        return f"[{colored_text(status, SPIDER_RED)}]"
    else:
        return f"[{status}]"


def format_time(seconds):
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        mins = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds / 3600)
        mins = int((seconds % 3600) / 60)
        return f"{hours}h {mins}m"


def print_progress_bar(current, total, start_time, bar_length=40):
    if not sys.stdout.isatty():
        return
    
    ERASE_LINE = "\033[K"
    
    percentage = (current / total * 100) if total > 0 else 0
    filled_length = int(bar_length * current / total) if total > 0 else 0
    
    elapsed_time = time.time() - start_time
    if current > 0:
        avg_time_per_item = elapsed_time / current
        remaining_items = total - current
        eta_seconds = avg_time_per_item * remaining_items
        eta_str = format_time(eta_seconds)
    else:
        eta_str = "calculating..."
    
    bar_chars = "█" * filled_length + "░" * (bar_length - filled_length)
    bar_colored = gradient_text(bar_chars, start_color=LIGHT_BLUE, end_color=DARK_BLUE)
    
    progress_text = f"{bar_colored} {percentage:.1f}% ({current}/{total}) | ETA: {eta_str}"
    
    terminal_width = shutil.get_terminal_size().columns
    if len(f"{bar_chars} {percentage:.1f}% ({current}/{total}) | ETA: {eta_str}") > terminal_width:
        max_len = terminal_width - 4
        progress_text = progress_text[:max_len] + "..."
    
    print(f"\r{ERASE_LINE}{progress_text}", end="", flush=True)


def print_status_line(text):
    if not sys.stdout.isatty():
        return
    
    ERASE_LINE = "\033[K"
    terminal_width = shutil.get_terminal_size().columns
    
    output = f"{text}"
    
    if len(output) > terminal_width:
        output = output[:terminal_width - 4] + "..."
        
    print(f"\r{ERASE_LINE}{output}", end="", flush=True)


def print_report_box(title, data_dict):
    if not data_dict:
        return
    
    terminal_width = shutil.get_terminal_size().columns
    max_key_len = max(len(str(key)) for key in data_dict.keys()) if data_dict else 0

    max_content_width = 0
    if data_dict:
        max_content_width = max(7 + max_key_len + len(str(v)) for v in data_dict.values())
        if max_content_width > terminal_width:
            max_content_width = terminal_width

    header_text = f" {title} "
    total_width = max(len(header_text) + 4, max_content_width)

    print(gradient_text("\n" + header_text.center(total_width, "-")))
    
    for key, value in data_dict.items():
        print(f"  {key:<{max_key_len}} : {value}")
        
    print(gradient_text("-" * total_width))


def display_art():
    terminal_width = shutil.get_terminal_size().columns
    
    art = r"""⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠀⢰⠛⠉⠳⡀⠀⠀⠀⠀⢀⣠⠤⠴⠒⠒⠒⠒⠤⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⡾⠉⠙⠻⣧⠀⠀⢳⡀⠀⣠⠞⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⢳⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡤⠶⢻⢷⣤⡀⠀⠈⢧⡀⠀⣷⠞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⢣⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⠋⠀⠀⢸⠀⠙⢿⡄⠀⠀⢱⣴⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣇⣠⠴⡶⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡞⠁⣀⣀⣴⡛⠳⣄⠀⠙⣦⣄⣠⣇⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⢁⣴⢧⡈⠳⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⡴⣏⢀⡼⠁⢹⠀⠉⠉⢙⣳⡾⠁⠀⠀⠀⠀⠉⠙⠲⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡾⠋⡇⠀⠙⢷⣌⠓⢄⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡤⠞⠁⠀⣨⠏⠀⣠⡼⠲⡶⣶⠋⢹⡗⣦⣀⣀⡀⣀⣀⣤⠀⠈⢳⡀⠀⢀⣀⣀⠀⢀⡞⠉⢳⣤⠞⠁⢠⠏⠙⠦⡀⠙⢧⠚⢳⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣠⡴⠚⠁⠀⣀⣴⠞⠁⣠⠞⡿⠀⢀⡇⠸⣤⣸⡶⠿⣇⣶⡇⠻⠿⠀⠀⠀⠀⢹⠀⡏⠀⢹⡄⢸⣧⠀⠘⡏⠀⢠⠏⠀⠀⠀⠈⠳⣄⠱⢬⣧⡀⠀⠀⠀⠀⠀  .dP"Y8 88   88 88""Yb 88     88 88b 88  dP""b8 
⠀⠀⠀⠀⠀⣠⠞⠁⣠⣶⣶⠟⠋⠁⢀⡴⠃⣰⠁⢀⣾⠀⣠⠟⠋⢳⡶⠛⢥⡀⠀⠀⠀⡤⢶⣶⡋⠸⡇⠀⠈⣿⡟⢹⠀⠀⣿⡶⠋⠀⠀⠀⠀⠀⠀⠈⠳⣾⣿⣏⠓⠤⣄⠀⠀  `Ybo." 88   88 88__dP 88     88 88Yb88 dP   `" 
⠀⠀⢀⡤⠞⠁⣠⣾⠟⠁⠀⣠⡤⠖⠋⠀⢠⠧⣄⡞⠈⡿⠁⠀⢀⡞⠀⠀⠀⣷⡀⠀⣼⠁⢸⣀⣿⠖⣇⠀⠀⣿⣿⠶⡇⠀⢹⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢏⠹⣟⠊⠉⠀⠀  o.`Y8b Y8   8P 88""Yb 88  .o 88 88 Y88 Yb  "88 
⠀⠀⠈⠓⠒⣻⠿⠃⣠⠖⠋⠁⠀⠀⠀⣖⠁⣠⠏⠀⢸⠀⠀⢠⠎⠀⠀⠀⡾⠁⠉⢉⡇⠀⡜⠉⠀⠀⢸⠀⠀⢻⠁⠀⣼⠀⠈⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢣⡘⢦⡀⠀⠀  8bodP' `YbodP' 88oodP 88ood8 88 88  Y8  YboodP 
⠀⠀⠀⡠⠞⢁⣠⠞⠁⠀⠀⠀⠀⠀⠀⠈⠉⠁⠀⠀⠘⠷⠤⢼⣀⠀⠀⣼⠇⠀⢀⡞⠀⣸⠃⠀⠀⠀⠀⡇⠀⢸⠀⠀⢸⡖⠒⢻⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⣏⠓⢤⣀
⣤⠖⠋⣀⠴⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠉⠀⠀⡞⠀⢠⠇⠀⠀⠀⠀⠀⡷⠒⠺⡇⠀⠀⣇⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠑⠒⠒
⠉⠉⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢺⣀⣀⡾⠀⠀⠀⠀⠀⠀⢸⠀⠀⡇⠀⠀⢿⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣇⠀⢹⠀⠀⢸⡄⣸⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡀⢸⠀⠀⢸⡏⠉⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀By @b3rt1ng
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣧⠾⡇⠀⠘⡇⠀⢳⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀https://github.com/b3rt1ng
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⠀⢳⠀⠀⠹⣤⣼⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⠀⢸⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢐⣇⣀⣸⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"""
    
    small_art = r"""
  ██████  █    ██  ▄▄▄▄    ██▓     ██▓ ███▄    █   ▄████ 
▒██    ▒  ██  ▓██▒▓█████▄ ▓██▒    ▓██▒ ██ ▀█   █  ██▒ ▀█▒
░ ▓██▄   ▓██  ▒██░▒██▒ ▄██▒██░    ▒██▒▓██  ▀█ ██▒▒██░▄▄▄░
  ▒   ██▒▓▓█  ░██░▒██░█▀  ▒██░    ░██░▓██▒  ▐▌██▒░▓█  ██▓
▒██████▒▒▒▒█████▓ ░▓█  ▀█▓░██████▒░██░▒██░   ▓██░░▒▓███▀▒
▒ ▒▓▒ ▒ ░░▒▓▒ ▒ ▒ ░▒▓███▀▒░ ▒░▓  ░░▓  ░ ▒░   ▒ ▒  ░▒   ▒ 
░ ░▒  ░ ░░░▒░ ░ ░ ▒░▒   ░ ░ ░ ▒  ░ ▒ ░░ ░░   ░ ▒░  ░   ░ 
░  ░  ░   ░░░ ░ ░  ░    ░   ░ ░    ▒ ░   ░   ░ ░ ░ ░   ░ 
      ░     ░      ░          ░  ░ ░           ░       ░ 
                        ░                                
         By @b3rt1ng"""
    
    very_small_art = r"""
  ___      _    _    _           
 / __|_  _| |__| |  (_)_ _  __ _ 
 \__ \ || | '_ \ |__| | ' \/ _` |
 |___/\_,_|_.__/____|_|_||_\__, |
                           |___/   
        By @b3rt1ng"""
    
    if terminal_width < 81:
        print(gradient_text(very_small_art))
    elif terminal_width < 139:
        print(gradient_text(small_art))
    else:
        print(gradient_text(art))