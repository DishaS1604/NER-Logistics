"""Small geometry helpers (distances in km)."""
import math

R = 6371.0


def haversine_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def path_length_km(path):
    return sum(haversine_km(path[i - 1], path[i]) for i in range(1, len(path)))


def point_along(path, frac):
    """Point at fraction 0..1 of the length of a polyline."""
    frac = min(1.0, max(0.0, frac))
    total = path_length_km(path)
    if total == 0:
        return list(path[0])
    target = frac * total
    for i in range(1, len(path)):
        seg = haversine_km(path[i - 1], path[i])
        if target <= seg or i == len(path) - 1:
            t = 0 if seg == 0 else min(1.0, target / seg)
            return [path[i - 1][0] + (path[i][0] - path[i - 1][0]) * t,
                    path[i - 1][1] + (path[i][1] - path[i - 1][1]) * t]
        target -= seg
    return list(path[-1])


def distance_to_path_km(p, path):
    """Approximate distance from a point to a polyline (flat-earth approximation)."""
    kx = 111.32 * math.cos(math.radians(p[0]))
    ky = 110.57
    best = float("inf")
    for i in range(1, len(path)):
        ax, ay = (path[i - 1][1] - p[1]) * kx, (path[i - 1][0] - p[0]) * ky
        bx, by = (path[i][1] - p[1]) * kx, (path[i][0] - p[0]) * ky
        dx, dy = bx - ax, by - ay
        l2 = dx * dx + dy * dy
        t = 0 if l2 == 0 else max(0, min(1, (-ax * dx - ay * dy) / l2))
        best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best
