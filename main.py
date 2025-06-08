import pygame
import random
import time

# Инициализация Pygame
pygame.init()

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
COLORS = [
    (0, 255, 255),  # I - голубой
    (128, 0, 128),  # T - фиолетовый
    (255, 0, 0),    # Z - красный
    (0, 255, 0),    # S - зеленый
    (255, 255, 0),  # O - желтый
    (255, 165, 0),  # L - оранжевый
    (0, 0, 255)     # J - синий
]

# Настройки игры
CELL_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
SCREEN_WIDTH = CELL_SIZE * (GRID_WIDTH + 6)
SCREEN_HEIGHT = CELL_SIZE * GRID_HEIGHT
GAME_AREA_LEFT = CELL_SIZE

# Фигуры Тетриса (тетромино)
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 0], [0, 1, 1]],  # Z
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1], [1, 1]],  # O
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]]   # J
]

class Tetris:
    def __init__(self):
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.game_over = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.fall_speed = 0.5  # секунды
        self.fall_time = 0
        self.paused = False
        self.ghost_piece = True  # Показывать "призрачную" фигуру
        
    def new_piece(self):
        # Выбираем случайную фигуру
        shape_idx = random.randint(0, len(SHAPES) - 1)
        return {
            'shape': SHAPES[shape_idx],
            'color': COLORS[shape_idx],
            'x': GRID_WIDTH // 2 - len(SHAPES[shape_idx][0]) // 2,
            'y': 0
        }
    
    def valid_position(self, shape=None, x=None, y=None):
        if shape is None:
            shape = self.current_piece['shape']
        if x is None:
            x = self.current_piece['x']
        if y is None:
            y = self.current_piece['y']
            
        for i, row in enumerate(shape):
            for j, cell in enumerate(row):
                if cell:
                    if (x + j < 0 or x + j >= GRID_WIDTH or 
                        y + i >= GRID_HEIGHT or 
                        (y + i >= 0 and self.grid[y + i][x + j])):
                        return False
        return True
    
    def rotate_piece(self):
        # Поворот матрицы фигуры на 90 градусов
        rotated = list(zip(*self.current_piece['shape'][::-1]))
        rotated = [list(row) for row in rotated]
        
        old_shape = self.current_piece['shape']
        self.current_piece['shape'] = rotated
        
        # Проверка стенки кикс (wall kick)
        if not self.valid_position():
            # Пробуем сместить фигуру влево/вправо при повороте
            for offset in [1, -1, 2, -2]:
                self.current_piece['x'] += offset
                if self.valid_position():
                    return
                self.current_piece['x'] -= offset
                
            # Если не получилось - возвращаем старую форму
            self.current_piece['shape'] = old_shape
    
    def move(self, dx, dy):
        self.current_piece['x'] += dx
        self.current_piece['y'] += dy
        
        if not self.valid_position():
            self.current_piece['x'] -= dx
            self.current_piece['y'] -= dy
            return False
        return True
    
    def drop(self):
        # Мгновенное падение
        while self.move(0, 1):
            pass
        self.lock_piece()
    
    def lock_piece(self):
        # Фиксация фигуры на поле
        for i, row in enumerate(self.current_piece['shape']):
            for j, cell in enumerate(row):
                if cell and self.current_piece['y'] + i >= 0:
                    self.grid[self.current_piece['y'] + i][self.current_piece['x'] + j] = self.current_piece['color']
        
        self.clear_lines()
        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()
        
        if not self.valid_position():
            self.game_over = True
    
    def clear_lines(self):
        new_grid = [row for row in self.grid if any(cell == 0 for cell in row)]
        lines_cleared = GRID_HEIGHT - len(new_grid)
        
        if lines_cleared > 0:
            self.lines_cleared += lines_cleared
            self.score += self.calculate_score(lines_cleared)
            self.level = self.lines_cleared // 10 + 1
            self.fall_speed = max(0.05, 0.5 - (self.level - 1) * 0.05)
            self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(lines_cleared)] + new_grid
    
    def calculate_score(self, lines):
        # Система подсчета очков как в классическом Тетрисе
        return {1: 100, 2: 300, 3: 500, 4: 800}[lines] * self.level
    
    def get_ghost_position(self):
        # Возвращает позицию "призрачной" фигуры (где она окажется при дропе)
        ghost = self.current_piece.copy()
        while True:
            ghost['y'] += 1
            if not self.valid_position(ghost['shape'], ghost['x'], ghost['y']):
                ghost['y'] -= 1
                return ghost

def draw_grid(surface, grid):
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell:
                pygame.draw.rect(surface, cell, 
                                (GAME_AREA_LEFT + x * CELL_SIZE, y * CELL_SIZE, 
                                 CELL_SIZE - 1, CELL_SIZE - 1))

def draw_piece(surface, piece, ghost=False):
    color = piece['color']
    if ghost:
        color = (*color[:3], 128)  # Полупрозрачный цвет для призрака
        alpha_surface = pygame.Surface((CELL_SIZE - 1, CELL_SIZE - 1), pygame.SRCALPHA)
        pygame.draw.rect(alpha_surface, color, (0, 0, CELL_SIZE - 1, CELL_SIZE - 1))
        
        for i, row in enumerate(piece['shape']):
            for j, cell in enumerate(row):
                if cell:
                    surface.blit(alpha_surface, 
                                (GAME_AREA_LEFT + (piece['x'] + j) * CELL_SIZE, 
                                 (piece['y'] + i) * CELL_SIZE))
    else:
        for i, row in enumerate(piece['shape']):
            for j, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(surface, color, 
                                    (GAME_AREA_LEFT + (piece['x'] + j) * CELL_SIZE, 
                                     (piece['y'] + i) * CELL_SIZE, 
                                     CELL_SIZE - 1, CELL_SIZE - 1))

def draw_next_piece(surface, piece):
    font = pygame.font.SysFont(None, 30)
    text = font.render("Next:", True, WHITE)
    surface.blit(text, (GAME_AREA_LEFT + GRID_WIDTH * CELL_SIZE + 20, 30))
    
    for i, row in enumerate(piece['shape']):
        for j, cell in enumerate(row):
            if cell:
                pygame.draw.rect(surface, piece['color'], 
                                (GAME_AREA_LEFT + GRID_WIDTH * CELL_SIZE + 20 + j * CELL_SIZE, 
                                 60 + i * CELL_SIZE, 
                                 CELL_SIZE - 1, CELL_SIZE - 1))

def draw_score(surface, score, level, lines):
    font = pygame.font.SysFont(None, 30)
    
    score_text = font.render(f"Score: {score}", True, WHITE)
    level_text = font.render(f"Level: {level}", True, WHITE)
    lines_text = font.render(f"Lines: {lines}", True, WHITE)
    
    surface.blit(score_text, (GAME_AREA_LEFT + GRID_WIDTH * CELL_SIZE + 20, 150))
    surface.blit(level_text, (GAME_AREA_LEFT + GRID_WIDTH * CELL_SIZE + 20, 180))
    surface.blit(lines_text, (GAME_AREA_LEFT + GRID_WIDTH * CELL_SIZE + 20, 210))

def draw_game_over(surface):
    font = pygame.font.SysFont(None, 40)
    text = font.render("GAME OVER", True, (255, 0, 0))
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    surface.blit(text, text_rect)
    
    font = pygame.font.SysFont(None, 30)
    restart_text = font.render("Press R to restart", True, WHITE)
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    surface.blit(restart_text, restart_rect)

def draw_pause(surface):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))
    surface.blit(overlay, (0, 0))
    
    font = pygame.font.SysFont(None, 40)
    text = font.render("PAUSED", True, WHITE)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    surface.blit(text, text_rect)

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tetris")
    clock = pygame.time.Clock()
    
    game = Tetris()
    running = True
    
    while running:
        current_time = time.time()
        
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if not game.game_over and not game.paused:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        game.move(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        game.move(1, 0)
                    elif event.key == pygame.K_DOWN:
                        game.move(0, 1)
                    elif event.key == pygame.K_UP:
                        game.rotate_piece()
                    elif event.key == pygame.K_SPACE:
                        game.drop()
                    elif event.key == pygame.K_p:
                        game.paused = not game.paused
                    elif event.key == pygame.K_g:
                        game.ghost_piece = not game.ghost_piece
            
            if game.game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                game = Tetris()  # Рестарт игры
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                game.paused = not game.paused
        
        # Игровая логика
        if not game.game_over and not game.paused:
            if current_time - game.fall_time > game.fall_speed:
                if not game.move(0, 1):
                    game.lock_piece()
                game.fall_time = current_time
        
        # Отрисовка
        screen.fill(BLACK)
        
        # Рисуем границы игрового поля
        pygame.draw.rect(screen, WHITE, 
                         (GAME_AREA_LEFT - 2, 0, 
                          GRID_WIDTH * CELL_SIZE + 4, GRID_HEIGHT * CELL_SIZE), 2)
        
        draw_grid(screen, game.grid)
        
        if game.ghost_piece and not game.game_over:
            ghost = game.get_ghost_position()
            draw_piece(screen, ghost, ghost=True)
        
        if not game.game_over:
            draw_piece(screen, game.current_piece)
        
        draw_next_piece(screen, game.next_piece)
        draw_score(screen, game.score, game.level, game.lines_cleared)
        
        if game.game_over:
            draw_game_over(screen)
        
        if game.paused:
            draw_pause(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()