# This is also Bet testing

import pygame
import sys
import math
import random
import pymunk
import pymunk.pygame_util
from pygame import gfxdraw

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Advanced Interactive Gun Simulation")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)
BROWN = (139, 69, 19)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
GOLD = (212, 175, 55)
DARK_GRAY = (50, 50, 50)

# Physics setup
space = pymunk.Space()
space.gravity = (0, 980)  # More realistic gravity
draw_options = pymunk.pygame_util.DrawOptions(screen)

# Physics constants
RECOIL_FORCE = 800
BULLET_SPEED = 3000
GUN_MASS = 5
MAGAZINE_MASS = 1

class Gun:
    def __init__(self):
        # Gun body physics
        moment = pymunk.moment_for_box(GUN_MASS, (60, 20))
        self.body = pymunk.Body(GUN_MASS, moment)
        self.body.position = WIDTH // 4, HEIGHT - 100
        self.shape = pymunk.Poly.create_box(self.body, (60, 20))
        self.shape.friction = 0.7
        self.shape.elasticity = 0.3
        space.add(self.body, self.shape)
        
        # Gun parameters
        self.length = 60
        self.width = 20
        self.color = GRAY
        self.barrel_length = 80
        self.angle = 0
        self.recoil_force = 0
        self.cooldown = 0
        self.magazine = None
        self.magazine_attached = True
        self.bullets = []
        self.muzzle_flash = []
        self.trigger_pulled = False
        
        # Create magazine
        self.create_magazine()
    
    def create_magazine(self):
        if self.magazine is not None:
            space.remove(self.magazine.body, self.magazine.shape)
        
        moment = pymunk.moment_for_box(MAGAZINE_MASS, (30, 40))
        self.magazine = pymunk.Body(MAGAZINE_MASS, moment)
        self.magazine.position = self.body.position[0] - 20, self.body.position[1] + 30
        self.magazine_shape = pymunk.Poly.create_box(self.magazine, (30, 40))
        self.magazine_shape.friction = 0.8
        self.magazine_shape.elasticity = 0.2
        self.magazine_shape.color = DARK_GRAY
        space.add(self.magazine, self.magazine_shape)
        
        # Create joint when attached
        if self.magazine_attached:
            self.create_magazine_joint()
    
    def create_magazine_joint(self):
        self.joint = pymunk.PivotJoint(self.body, self.magazine, 
                                      (self.body.position[0] - 20, self.body.position[1] + 30))
        space.add(self.joint)
    
    def update(self, mouse_pos):
        # Update angle based on mouse position
        dx = mouse_pos[0] - self.body.position.x
        dy = mouse_pos[1] - self.body.position.y
        self.angle = math.degrees(math.atan2(dy, dx))
        
        # Apply recoil force
        if self.recoil_force > 0:
            recoil_direction = -math.radians(self.angle)
            force_x = math.cos(recoil_direction) * self.recoil_force
            force_y = math.sin(recoil_direction) * self.recoil_force
            self.body.apply_impulse_at_local_point((force_x, force_y))
            self.recoil_force *= 0.8  # Dampen recoil
        
        # Cooldown between shots
        if self.cooldown > 0:
            self.cooldown -= 1
        
        # Update muzzle flash particles
        for particle in self.muzzle_flash[:]:
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.muzzle_flash.remove(particle)
        
        # Check magazine attachment
        if self.magazine_attached:
            dist = (self.magazine.position - self.body.position).length
            if dist > 50:  # If magazine is pulled too far
                self.magazine_attached = False
                space.remove(self.joint)
    
    def fire(self):
        if (self.cooldown <= 0 and self.magazine_attached and 
            hasattr(self, 'magazine') and self.trigger_pulled):
            
            # Calculate bullet starting position
            barrel_end_x = self.body.position.x + math.cos(math.radians(self.angle)) * self.barrel_length
            barrel_end_y = self.body.position.y + math.sin(math.radians(self.angle)) * self.barrel_length
            
            # Create bullet physics
            bullet_body = pymunk.Body(0.1, pymunk.moment_for_circle(0.1, 0, 5))
            bullet_body.position = barrel_end_x, barrel_end_y
            bullet_shape = pymunk.Circle(bullet_body, 5)
            bullet_shape.elasticity = 0.8
            bullet_shape.friction = 0.5
            bullet_shape.collision_type = 1
            space.add(bullet_body, bullet_shape)
            
            # Apply bullet velocity
            velocity_x = math.cos(math.radians(self.angle)) * BULLET_SPEED
            velocity_y = math.sin(math.radians(self.angle)) * BULLET_SPEED
            bullet_body.velocity = (velocity_x, velocity_y)
            
            # Apply recoil
            self.recoil_force = RECOIL_FORCE
            
            # Set cooldown
            self.cooldown = 10
            
            # Create muzzle flash
            for _ in range(15):
                angle_variation = random.uniform(-15, 15)
                speed = random.uniform(50, 200)
                particle_angle = self.angle + angle_variation
                vx = math.cos(math.radians(particle_angle)) * speed
                vy = math.sin(math.radians(particle_angle)) * speed
                
                self.muzzle_flash.append({
                    'x': barrel_end_x,
                    'y': barrel_end_y,
                    'vx': vx,
                    'vy': vy,
                    'life': random.randint(5, 15),
                    'color': random.choice([ORANGE, YELLOW, RED]),
                    'size': random.randint(3, 8)
                })
            
            return True
        return False
    
    def draw(self, surface):
        # Draw gun body
        vertices = [
            self.body.position.x + math.cos(math.radians(self.angle + 90)) * 10,
            self.body.position.y + math.sin(math.radians(self.angle + 90)) * 10
        ], [
            self.body.position.x + math.cos(math.radians(self.angle - 90)) * 10,
            self.body.position.y + math.sin(math.radians(self.angle - 90)) * 10
        ], [
            self.body.position.x + math.cos(math.radians(self.angle - 90)) * 10 + 
            math.cos(math.radians(self.angle)) * self.length,
            self.body.position.y + math.sin(math.radians(self.angle - 90)) * 10 + 
            math.sin(math.radians(self.angle)) * self.length
        ], [
            self.body.position.x + math.cos(math.radians(self.angle + 90)) * 10 + 
            math.cos(math.radians(self.angle)) * self.length,
            self.body.position.y + math.sin(math.radians(self.angle + 90)) * 10 + 
            math.sin(math.radians(self.angle)) * self.length
        ]
        
        pygame.draw.polygon(surface, self.color, vertices)
        
        # Draw gun barrel
        barrel_end_x = self.body.position.x + math.cos(math.radians(self.angle)) * self.barrel_length
        barrel_end_y = self.body.position.y + math.sin(math.radians(self.angle)) * self.barrel_length
        pygame.draw.line(surface, DARK_GRAY, self.body.position, (barrel_end_x, barrel_end_y), 8)
        
        # Draw muzzle flash
        for particle in self.muzzle_flash:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            pygame.draw.circle(surface, particle['color'], 
                             (int(particle['x']), int(particle['y'])), particle['size'])
        
        # Draw magazine if it exists
        if hasattr(self, 'magazine'):
            mag_vertices = [
                (self.magazine.position.x - 15, self.magazine.position.y - 20),
                (self.magazine.position.x + 15, self.magazine.position.y - 20),
                (self.magazine.position.x + 15, self.magazine.position.y + 20),
                (self.magazine.position.x - 15, self.magazine.position.y + 20)
            ]
            pygame.draw.polygon(surface, DARK_GRAY, mag_vertices)
            
            # Draw bullets in magazine
            if self.magazine_attached:
                for i in range(10):
                    bullet_x = self.magazine.position.x - 10 + random.uniform(-2, 2)
                    bullet_y = self.magazine.position.y - 15 + i * 3 + random.uniform(-1, 1)
                    pygame.draw.circle(surface, GOLD, (int(bullet_x), int(bullet_y)), 2)

class Target:
    def __init__(self, x, y):
        self.radius = 30
        self.body = pymunk.Body(10, pymunk.moment_for_circle(10, 0, self.radius))
        self.body.position = x, y
        self.shape = pymunk.Circle(self.body, self.radius)
        self.shape.elasticity = 0.8
        self.shape.friction = 0.5
        self.shape.collision_type = 2
        space.add(self.body, self.shape)
        
        self.color = RED
        self.hit = False
        self.hit_time = 0
    
    def draw(self, surface):
        if self.hit:
            # Draw explosion effect
            pygame.draw.circle(surface, ORANGE, (int(self.body.position.x), int(self.body.position.y)), 
                             self.radius + 5)
            pygame.draw.circle(surface, YELLOW, (int(self.body.position.x), int(self.body.position.y)), 
                             self.radius + 2)
            self.hit_time -= 1
            if self.hit_time <= 0:
                self.hit = False
                # Give the target a new random velocity
                self.body.velocity = (random.uniform(-200, 200), random.uniform(-200, 200))
        else:
            # Draw target rings
            pygame.draw.circle(surface, self.color, (int(self.body.position.x), int(self.body.position.y)), 
                             self.radius)
            pygame.draw.circle(surface, WHITE, (int(self.body.position.x), int(self.body.position.y)), 
                             int(self.radius * 0.7))
            pygame.draw.circle(surface, self.color, (int(self.body.position.x), int(self.body.position.y)), 
                             int(self.radius * 0.4))
            pygame.draw.circle(surface, WHITE, (int(self.body.position.x), int(self.body.position.y)), 
                             int(self.radius * 0.1))

def bullet_target_collision(arbiter, space, data):
    bullet, target = arbiter.shapes
    target.hit = True
    target.hit_time = 30
    space.remove(bullet.body, bullet)
    return True
# TODO: This is stupid

# Set up collision handler
handler = space.add_collision_handler(1, 2)  # Bullet and target
handler.begin = bullet_target_collision

# Create game objects
gun = Gun()
targets = [Target(random.randint(WIDTH//2, WIDTH-50), random.randint(50, HEIGHT-50)) for _ in range(3)]
score = 0
font = pygame.font.SysFont('Arial', 24)

# Dragging variables
dragging = None
selected_object = None

# Game loop
clock = pygame.time.Clock()
running = True

while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = pymunk.pygame_util.get_mouse_pos(screen)
                # Check if we clicked the magazine
                if (hasattr(gun, 'magazine') and 
                    (mouse_pos - gun.magazine.position).length < 30):
                    selected_object = gun.magazine
                    dragging = mouse_pos
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left click release
                if selected_object == gun.magazine:
                    # Check if magazine is close enough to attach
                    if (gun.magazine.position - gun.body.position).length < 50:
                        gun.magazine_attached = True
                        gun.create_magazine_joint()
                dragging = None
                selected_object = None
        
        elif event.type == pygame.MOUSEMOTION:
            if dragging and selected_object:
                mouse_pos = pymunk.pygame_util.get_mouse_pos(screen)
                selected_object.position = mouse_pos
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and not gun.magazine_attached:
                gun.create_magazine()
                gun.magazine_attached = True
                gun.create_magazine_joint()
    
    # Check trigger state
    gun.trigger_pulled = pygame.mouse.get_pressed()[0]
    
    # Update game objects
    gun.update(pygame.mouse.get_pos())
    gun.fire()
    
    # Update physics
    space.step(1/60.0)
    
    # Draw everything
    screen.fill(BLACK)
    
    # Draw ground
    pygame.draw.rect(screen, BROWN, (0, HEIGHT - 20, WIDTH, 20))
    
    # Draw targets
    for target in targets:
        target.draw(screen)
    
    # Draw gun
    gun.draw(screen)
    
    # Draw UI
    score_text = font.render(f"Score: {score}", True, WHITE)
    status_text = font.render(f"Magazine: {'Attached' if gun.magazine_attached else 'Detached'}", True, WHITE)
    help_text = font.render("Drag magazine to detach, Press R to reattach", True, WHITE)
    
    screen.blit(score_text, (10, 10))
    screen.blit(status_text, (10, 40))
    screen.blit(help_text, (10, 70))
    
    # Debug draw physics (optional)
    # space.debug_draw(draw_options)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
