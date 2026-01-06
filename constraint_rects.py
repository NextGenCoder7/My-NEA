import pygame
from constants import RED, PURPLE, ORANGE, TILE_SIZE


class ConstraintRect(pygame.sprite.Sprite):
    """
    A rectangle used to define constraints in the level editor. These rectangles are not visible in the game,
    and serve as constraints and markers for all the game enemies, in particular Fierce Tooth and Pink Star enemies. 

    The red ones serve as constraints for vision and physical movement, creating zones for Fierce Tooth and Seashell Pearl enemies.
    The orange ones act as corners for 'danger zones' which are guarded by Pink Star enemies.
    The purple ones are used as jump triggers for Fierce and Pink enemies, indicating where they should jump.

    Attributes:
        colour (tuple): The RGB colour of the rectangle based on the tile number.
        rect (Rect): The Pygame rectangle defining the position and size of the constraint.
    """

    def __init__(self, x, y, width, height, tile_number):
        """
        Initialise the ConstraintRect object.

        Args:
            x (int): The x-coordinate of the rectangle's top-left corner.
            y (int): The y-coordinate of the rectangle's top-left corner.
            width (int): The width of the rectangle.
            height (int): The height of the rectangle.
            tile_number (int): The tile number indicating the type of constraint (25: red, 26: purple, 29: orange).
        """

        super().__init__()

        self.colour = None
        if tile_number == 25:
            self.colour = RED
        elif tile_number == 26:
            self.colour = PURPLE
        elif tile_number == 29:
            self.colour = ORANGE

        self.rect = pygame.Rect(x, y, width, height)   
        
    def draw(self, win):
        pygame.draw.rect(win, self.colour, self.rect)


def compute_danger_zones(constraint_group):
    """
    Find orange marker rects and return a list of (bounding_rect, validated) tuples.

    Basically builds a bounding rect from their extents and validates that there are rectangles 
    at the four expected corner toplefts.

    Args:
        constraint_group (Group): A Pygame sprite group containing ConstraintRect objects.
    
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
