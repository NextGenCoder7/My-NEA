import pygame 


class Button():
	"""
	A class to create and manage clickable buttons in a Pygame application from imported images.

	Attributes:
		image (Surface): The Pygame surface representing the button image.
		rect (Rect): The rectangle defining the button's position and size.
		clicked (bool): A flag indicating whether the button has been clicked.
	"""

	def __init__(self, x, y, image, scale):
		"""
		Initialise the Button with position, image, and scale.

		Args:
			x (int): The x-coordinate of the button's top-left corner.
			y (int): The y-coordinate of the button's top-left corner.
			image (Surface): The Pygame surface representing the button image.
			scale (float): The scale factor to resize the button image.
		"""

		width = image.get_width()
		height = image.get_height()
		self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
		self.rect = self.image.get_rect()
		self.rect.topleft = (x, y)
		self.clicked = False

	def draw(self, win):
		"""
		Draw the button on the provided surface and handle click detection at the same time.
		If this function is called, even within an if statement, the button will be drawn.

		Args:
			win (Surface): The Pygame surface to draw the button on.

		Returns:
			bool: True if the button was clicked, False otherwise.
		"""

		action = False

		pos = pygame.mouse.get_pos()

		if self.rect.collidepoint(pos):
			if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
				action = True
				self.clicked = True

		if pygame.mouse.get_pressed()[0] == 0:
			self.clicked = False

		win.blit(self.image, (self.rect.x, self.rect.y))

		return action
