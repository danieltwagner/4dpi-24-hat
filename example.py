from adafruit_rgb_display import color565
from PIL import Image, ImageDraw, ImageFont
import ili9341_4dpi

import subprocess
import time

display = ili9341_4dpi.ILI9341_4DPI()
# Fill the screen red, green, blue, then black:
for color in ((255, 0, 0), (0, 255, 0), (0, 0, 255)):
    display.fill(color565(color))
    time.sleep(1)
# Clear the display
display.fill(0)
# Draw a red pixel in the center.
display.pixel(display.width // 2, display.height // 2, color565(255, 0, 0))

image = Image.new("RGB", (display.width, display.height))
draw = ImageDraw.Draw(image)
draw.rectangle((0, 0, display.width, display.height), outline=0, fill=(0, 0, 0))
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)

cmd = "hostname -I | cut -d' ' -f1"
IP = "IP: " + subprocess.check_output(cmd, shell=True).decode("utf-8")
cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
CPU = subprocess.check_output(cmd, shell=True).decode("utf-8")
cmd = "free -m | awk 'NR==2{printf \"Mem %s/%s MB  %.2f%%\", $3,$2,$3*100/$2 }'"
MemUsage = subprocess.check_output(cmd, shell=True).decode("utf-8")
cmd = 'df -h | awk \'$NF=="/"{printf "Disk: %d/%d GB  %s", $3,$2,$5}\''
Disk = subprocess.check_output(cmd, shell=True).decode("utf-8")
cmd = "cat /sys/class/thermal/thermal_zone0/temp |  awk '{printf \"CPU Temp: %.1f C\", $(NF-0) / 1000}'"  # pylint: disable=line-too-long
Temp = subprocess.check_output(cmd, shell=True).decode("utf-8")

# Write four lines of text.
padding = -2
x = 0
y = padding
draw.text((x, y), IP, font=font, fill="#FFFFFF")
y += font.getsize(IP)[1]
draw.text((x, y), CPU, font=font, fill="#FFFF00")
y += font.getsize(CPU)[1]
draw.text((x, y), MemUsage, font=font, fill="#00FF00")
y += font.getsize(MemUsage)[1]
draw.text((x, y), Disk, font=font, fill="#0000FF")
y += font.getsize(Disk)[1]
draw.text((x, y), Temp, font=font, fill="#FF00FF")

# Display image.
display.image(image)
