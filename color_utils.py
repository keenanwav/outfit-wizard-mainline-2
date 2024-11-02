import numpy as np

def rgb_to_hsv(rgb):
    rgb = rgb.astype('float')
    hsv = np.zeros_like(rgb)
    hsv[..., 3:] = rgb[..., 3:]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    maxc = np.max(rgb[..., :3], axis=-1)
    minc = np.min(rgb[..., :3], axis=-1)
    hsv[..., 2] = maxc
    mask = maxc != minc
    hsv[mask, 1] = (maxc - minc)[mask] / maxc[mask]
    rc = np.zeros_like(r)
    gc = np.zeros_like(g)
    bc = np.zeros_like(b)
    rc[mask] = (maxc - r)[mask] / (maxc - minc)[mask]
    gc[mask] = (maxc - g)[mask] / (maxc - minc)[mask]
    bc[mask] = (maxc - b)[mask] / (maxc - minc)[mask]
    hsv[..., 0] = np.select(
        [r == maxc, g == maxc], [bc - gc, 2.0 + rc - bc], default=4.0 + gc - rc)
    hsv[..., 0] = (hsv[..., 0] / 6.0) % 1.0
    return hsv

def hsv_to_rgb(hsv):
    rgb = np.empty_like(hsv)
    rgb[..., 3:] = hsv[..., 3:]
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    i = (h * 6.0).astype('uint8')
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6
    conditions = [s == 0.0, i == 1, i == 2, i == 3, i == 4, i == 5]
    rgb[..., 0] = np.select(conditions, [v, q, p, p, t, v], default=v)
    rgb[..., 1] = np.select(conditions, [v, v, v, q, p, p], default=t)
    rgb[..., 2] = np.select(conditions, [v, p, t, v, v, q], default=p)
    return rgb.astype('uint8')

def get_color_palette(base_color, palette_type):
    base_hsv = rgb_to_hsv(np.array(base_color))[0]
    h, s, v = base_hsv
    
    if palette_type == "Monochromatic":
        colors = [
            hsv_to_rgb(np.array([[h, s, v]]))[0],
            hsv_to_rgb(np.array([[h, s * 0.7, v]]))[0],
            hsv_to_rgb(np.array([[h, s, v * 0.7]]))[0]
        ]
    elif palette_type == "Analogous":
        colors = [
            hsv_to_rgb(np.array([[h, s, v]]))[0],
            hsv_to_rgb(np.array([[(h + 1/12) % 1, s, v]]))[0],
            hsv_to_rgb(np.array([[(h - 1/12) % 1, s, v]]))[0]
        ]
    elif palette_type == "Complementary":
        colors = [
            hsv_to_rgb(np.array([[h, s, v]]))[0],
            hsv_to_rgb(np.array([[(h + 0.5) % 1, s, v]]))[0],
            hsv_to_rgb(np.array([[h, s * 0.8, v * 0.8]]))[0]
        ]
    elif palette_type == "Triadic":
        colors = [
            hsv_to_rgb(np.array([[h, s, v]]))[0],
            hsv_to_rgb(np.array([[(h + 1/3) % 1, s, v]]))[0],
            hsv_to_rgb(np.array([[(h + 2/3) % 1, s, v]]))[0]
        ]
    else:
        raise ValueError("Invalid palette type")
    
    return colors

