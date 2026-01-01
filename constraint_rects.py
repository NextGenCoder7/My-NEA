import pygame
from constants import RED, BLUE, ORANGE, TILE_SIZE


class ConstraintRect(pygame.sprite.Sprite):

    def __init__(self, x, y, width, height, tile_number):
        super().__init__()

        self.colour = None
        if tile_number == 25:
            self.colour = RED
        elif tile_number == 26:
            self.colour = BLUE
        elif tile_number == 29:
            self.colour = ORANGE

        self.rect = pygame.Rect(x, y, width, height)   
        
    def draw(self, win):
        pygame.draw.rect(win, self.colour, self.rect)


def compute_danger_zones(constraint_group):
    """
    Find orange marker rects and return list of (bounding_rect, validated) tuples.

    Behaviour:
        - Looks for ConstraintRect instances with colour == ORANGE.
        - Builds a bounding rect from their extents.
        - Validates that there are rectangles at the four expected corner toplefts
          (uses TILE_SIZE as the corner rect size).
    
    Returns:
        empty list if no orange markers found.
    """
    orange_rects = [r for r in constraint_group if getattr(r, "colour", None) == ORANGE]
    if not orange_rects:
        return []

    xs = [r.rect.x for r in orange_rects]
    ys = [r.rect.y for r in orange_rects]
    rights = [r.rect.right for r in orange_rects]
    bottoms = [r.rect.bottom for r in orange_rects]

    big = pygame.Rect(min(xs), min(ys), max(rights) - min(xs), max(bottoms) - min(ys))

    expected_corners = [
        (big.left, big.top),
        (big.right - TILE_SIZE, big.top),
        (big.left, big.bottom - TILE_SIZE),
        (big.right - TILE_SIZE, big.bottom - TILE_SIZE)
    ]

    validated = True
    for cx, cy in expected_corners:
        if not any(abs(r.rect.x - cx) <= 1 and abs(r.rect.y - cy) <= 1 for r in orange_rects):
            validated = False
            break

    return [(big, validated)]
