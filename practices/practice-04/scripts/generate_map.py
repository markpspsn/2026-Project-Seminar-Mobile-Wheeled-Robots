import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


root = Path(__file__).resolve().parents[1]
resolution = 0.01
origin = -3.03
image = np.full((606, 606), 254, dtype=np.uint8)
rectangles = [
    (-3.03, -3.0, -3.0, 3.0),
    (3.0, -3.0, 3.03, 3.0),
    (-3.03, -3.03, 3.03, -3.0),
    (-3.03, 3.0, 3.03, 3.03),
]
blocks = [
    (-0.9, 0.0, 0.25, 1.6),
    (-1.05, 0.7, 0.55, 0.25),
    (-0.9, -0.8, 0.8, 0.25),
    (0.475, 0.0, 0.25, 1.35),
    (1.325, 0.0, 0.25, 1.35),
    (0.9, 0.8, 1.1, 0.25),
    (0.9, -0.8, 1.1, 0.25),
]
for x, y, width, height in blocks:
    rectangles.append((x - width / 2, y - height / 2, x + width / 2, y + height / 2))
for x0, y0, x1, y1 in rectangles:
    left = math.floor((x0 - origin) / resolution + 1e-8)
    right = math.ceil((x1 - origin) / resolution - 1e-8)
    bottom = math.floor((y0 - origin) / resolution + 1e-8)
    top = math.ceil((y1 - origin) / resolution - 1e-8)
    image[606 - top:606 - bottom, left:right] = 0
maps = root / 'maps'
(maps / 'digits_10.pgm').write_bytes(b'P5\n606 606\n255\n' + image.tobytes())
(maps / 'digits_10.yaml').write_text(
    'image: digits_10.pgm\nmode: trinary\nresolution: 0.01\n'
    'origin: [-3.03, -3.03, 0.0]\nnegate: 0\n'
    'occupied_thresh: 0.65\nfree_thresh: 0.25\n'
)
plt.imsave(maps / 'digits_10.png', image, cmap='gray', vmin=0, vmax=255)
print('Map saved: 606 x 606 pixels, 0.01 m/pixel')
