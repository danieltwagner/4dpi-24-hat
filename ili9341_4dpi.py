try:
    import struct
except ImportError:
    import ustruct as struct

from adafruit_rgb_display.rgb import Display
import pigpio
import time

# We'll use the 3-wire SPI protocol, as there is no Data Control pin.
# For some reason the spidev won't show up when the HAT is plugged in at boot.
# We'll use pigpio instead...
class ILI9341_4DPI(Display):
    """
    A simple driver for the 4D Systems 4DPI-24-HAT (ILI9341 based).
    """

    _LCDPI_LONG  = (1<<7)
    _LCDPI_BLOCK = (1<<6)
    _LCDPI_RESET = (1<<5)
    _LCDPI_RS    = (1<<4)
    _LCDPI_BL    = (1<<3)
    _LCDPI_RD    = (1<<2)

    _HX8357_SET_COLUMN_ADDRESS = 0x2a
    _HX8357_SET_PAGE_ADDRESS = 0x2b
    _HX8357_WRITE_MEMORY_START = 0x2c

    _MAX_DMA_PIXELS = 32767

    _COLUMN_SET = 0x2A
    _PAGE_SET = 0x2B
    _RAM_WRITE = 0x2C
    _RAM_READ = 0x2E
    _INIT = (
        (0xEF, b"\x03\x80\x02"),
        (0xCF, b"\x00\xc1\x30"),
        (0xED, b"\x64\x03\x12\x81"),
        (0xE8, b"\x85\x00\x78"),
        (0xCB, b"\x39\x2c\x00\x34\x02"),
        (0xF7, b"\x20"),
        (0xEA, b"\x00\x00"),
        (0xC0, b"\x23"),  # Power Control 1, VRH[5:0]
        (0xC1, b"\x10"),  # Power Control 2, SAP[2:0], BT[3:0]
        (0xC5, b"\x3e\x28"),  # VCM Control 1
        (0xC7, b"\x86"),  # VCM Control 2
        (0x36, b"\x68"),  # Memory Access Control, default rotation (top to bottom)
        (0x3A, b"\x55"),  # Pixel Format
        (0xB1, b"\x00\x18"),  # FRMCTR1
        (0xB6, b"\x0A\xA2"),  # Display Function Control
        (0xF2, b"\x00"),  # 3Gamma Function Disable
        (0x26, b"\x01"),  # Gamma Curve Selected
        (
            0xE0,  # Set Gamma
            b"\x0f\x31\x2b\x0c\x0e\x08\x4e\xf1\x37\x07\x10\x03\x0e\x09\x00",
        ),
        (
            0xE1,  # Set Gamma
            b"\x00\x0e\x14\x03\x11\x07\x31\xc1\x48\x08\x0f\x0c\x31\x36\x0f",
        ),
        (0x11, None),
        (0x29, None),
    )

    def __init__(
        self,
        spi_channel=0,
        baudrate=24000000,
        width=320,
        height=240,
        rotation=0,
        x_offset=0,
        y_offset=0,
        polarity=0,
        phase=0,
    ):
        self.pi = pigpio.pi()
        mode = ((polarity&0x1) << 1) | (phase&0x1)
        self.spi_handle = self.pi.spi_open(spi_channel, baudrate, mode)

        self._X_START = x_offset  # pylint: disable=invalid-name
        self._Y_START = y_offset  # pylint: disable=invalid-name

        self._scroll = 0

        # custom init
        self.pi.spi_write(self.spi_handle, [self._LCDPI_RESET | self._LCDPI_RD, 0x00, 0x00])
        time.sleep(0.1)
        self.pi.spi_write(self.spi_handle, [self._LCDPI_RD, 0x00, 0x00])
        time.sleep(0.1)
        self.pi.spi_write(self.spi_handle, [self._LCDPI_RESET | self._LCDPI_RD, 0x00, 0x00])
        time.sleep(0.15)

        super().__init__(width, height, rotation)

    def __del__(self):
        self.pi.spi_close(self.spi_handle)

    def reset(self):
        """Reset the device"""
        pass


    def xilinx_write_cmd(self, value):
        cmd = self._LCDPI_RESET | self._LCDPI_RD | self._LCDPI_BL
        to_send = [cmd, 0x00, (value)&0xff]
        self.pi.spi_write(self.spi_handle, to_send)

    def xilinx_write_data(self, values):
        cmd = self._LCDPI_RESET | self._LCDPI_RD | self._LCDPI_BL | self._LCDPI_RS

        for value in values:
            to_send = [cmd, (value>>8)&0xff, (value)&0xff]
            self.pi.spi_write(self.spi_handle, to_send)

    def xilinx_write_lots_of_data(self, values):
        cmd = self._LCDPI_RESET | self._LCDPI_RD | self._LCDPI_BL | self._LCDPI_RS | self._LCDPI_LONG

        self.write(self._HX8357_WRITE_MEMORY_START);

        sent = 0
        while sent < len(values):
            to_send = 2 * self.width * (self._MAX_DMA_PIXELS//self.width)
            data = cmd.to_bytes(1, 'big') + b"\x00\x00" + values[sent:sent + to_send]
            sent += to_send
            y_pos = sent//(2*self.width)

            self.pi.spi_write(self.spi_handle, data)
            self.write(self._HX8357_SET_COLUMN_ADDRESS, [0x00, 0x00, (self.width - 1) >> 8, self.width & 0x00ff])
            self.write(self._HX8357_SET_PAGE_ADDRESS, [y_pos >> 8, y_pos & 0x00ff, (self.height - 1) >> 8, (self.height - 1) & 0x00ff])
            self.write(self._HX8357_WRITE_MEMORY_START);


    def write(self, command=None, data=None):
        """SPI write to the device: commands and data"""
        if data is not None and (command is None or command == self._RAM_WRITE):
            self.xilinx_write_lots_of_data(data)
        else:
            if command is not None:
                self.xilinx_write_cmd(command)
            if data is not None:
                self.xilinx_write_data(data)

    def read(self, command=None, count=0):
        """SPI read from device with optional command"""
        pass

    def scroll(self, dy=None):
        """Scroll the display by delta y"""
        if dy is None:
            return self._scroll
        self._scroll = (self._scroll + dy) % self.height
        self.write(0x37, struct.pack(">H", self._scroll))
        return None
