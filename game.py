import random
import pgzrun
from pgzero.builtins import Actor, Rect, keyboard, keys, mouse

# Configs
WIDTH = 800
HEIGHT = 600
GRAVITY = 0.6
JUMP_STRENGTH = -12
PLAYER_SPEED = 5
ENEMY_SPEED = 2.5
SCROLL_THRESHOLD = 400
BG_WIDTH = 768

# States
MENU = 0
PLAYING = 1
GAME_OVER = 2


class Platform:
    """Plataforma do jogo."""
    def __init__(self, x, y, width, height):
        self.rect = Rect(x, y, width, height)

    def draw(self, scroll_x):
        """Desenha a plataforma."""
        image_x = self.rect.x - scroll_x
        image_y = self.rect.y

        if self.rect.width >= 800:
            screen.blit("floor/botton", (image_x, image_y))
        else:
            screen.blit("floor/top", (image_x, image_y))


class Game:
    """Classe principal do jogo."""
    def __init__(self):
        """Inicializa o jogo."""
        self.game_state = MENU
        self.music_playing = True
        self.music_button = Rect(300, 450, 200, 50)
        self.played_game_over_sound = False
        self.scroll_x = 0
        self.bg_scroll = 0
        self.score = 0
        self.enemy_spawn_timer = 0

        self.player = Actor('player/stand', (100, 400))
        self.player.vy = 0
        self.player.on_ground = True
        self.player.direction = 1
        self.player.width = 30
        self.player.height = 50
        self.player.walk_frame = 0

        self.enemies = []

        self.platforms = [
            Platform(0, 550, 800, 50),
            Platform(250, 450, 200, 20),
            Platform(450, 350, 200, 20),
            Platform(650, 450, 200, 20),
            Platform(850, 350, 200, 20)
        ]

        # Faz o jogo já iniciar tocando a musica de fundo
        if self.music_playing:
            music.play('background')

    def reset_game(self):
        """Reinicia o jogo."""
        self.score = 0
        self.played_game_over_sound = False
        self.player.pos = (100, 400)
        self.player.vy = 0
        self.player.on_ground = True
        self.scroll_x = 0
        self.enemies = []

        self.platforms = [
            Platform(0, 550, 800, 50),
            Platform(250, 450, 200, 20),
            Platform(450, 350, 200, 20),
            Platform(650, 450, 200, 20),
            Platform(850, 350, 200, 20)
        ]

        self.game_state = PLAYING

        if self.music_playing:
            music.play('background')

    def spawn_enemy(self):
        """Cria um novo inimigo."""
        spawn_x = self.scroll_x + WIDTH + 50
        spawn_y = HEIGHT - 100

        for plat in self.platforms:
            rect = plat.rect
            if rect.x <= spawn_x <= rect.x + rect.width:
                spawn_y = rect.y - 30
                break

        enemy_type = random.choice(['enemy1', 'enemy2', 'enemy3', 'enemy4', 'enemy5'])
        enemy = Actor(f'{enemy_type}/enemy_walk1', (spawn_x, spawn_y))
        enemy.type = enemy_type
        enemy.speed = ENEMY_SPEED
        enemy.walk_frame = 0
        enemy.width = 40
        enemy.height = 60
        self.enemies.append(enemy)

    def update_player(self):
        """Atualiza o jogador."""
        if keyboard.left or keyboard.a:
            self.player.x -= PLAYER_SPEED
            self.player.direction = -1
            self.player.walk_frame += 0.2
            frame = int(self.player.walk_frame) % 10 + 1
            self.player.image = f'player/walk{frame}_left'
        elif keyboard.right or keyboard.d:
            self.player.x += PLAYER_SPEED
            self.player.direction = 1
            self.player.walk_frame += 0.2
            frame = int(self.player.walk_frame) % 10 + 1
            self.player.image = f'player/walk{frame}'
        else:
            if self.player.on_ground:
                self.player.walk_frame += 0.1
                frame = int(self.player.walk_frame) % 2 + 3
                self.player.image = f'player/walk{frame}' if self.player.direction == 1 else f'player/walk{frame}_left'
            else:
                self.player.image = 'player/jump' if self.player.direction == 1 else 'player/jump_left'

        self.player.vy += GRAVITY
        self.player.y += self.player.vy
        self.player.on_ground = False

        for plat in self.platforms:
            platform = plat.rect
            plat_x = platform.x - self.scroll_x
            if (self.player.x > plat_x and
                self.player.x < plat_x + platform.width and
                self.player.bottom < platform.y + platform.height and
                self.player.bottom + self.player.vy > platform.y):
                self.player.bottom = platform.y
                self.player.vy = 0
                self.player.on_ground = True

        if (keyboard.up or keyboard.w or keyboard.space) and self.player.on_ground:
            self.player.vy = JUMP_STRENGTH
            self.player.on_ground = False
            self.player.image = 'player/jump'
            if self.music_playing:
                sounds.jump.play()

    def update_enemies(self):
        """Atualiza os inimigos."""
        for enemy in self.enemies[:]:
            enemy.x -= enemy.speed
            enemy.walk_frame += 0.2
            enemy.image = f'{enemy.type}/enemy_walk{int(enemy.walk_frame) % 3 + 1}'
            enemy_rect = Rect(enemy.x - self.scroll_x, enemy.y, enemy.width, enemy.height)

            if Rect(self.player.x, self.player.y, self.player.width, self.player.height).colliderect(enemy_rect):
                if self.player.vy > 0 and self.player.bottom < enemy.y + 20:
                    self.enemies.remove(enemy)
                    self.player.vy = JUMP_STRENGTH / 2
                    if self.music_playing:
                        sounds.point.play()
                    self.score += 1
                else:
                    self.game_state = GAME_OVER

            if enemy.x < self.scroll_x - 50:
                self.enemies.remove(enemy)

    def update_scroll(self):
        """Atualiza o scroll da câmera."""
        if self.player.x > SCROLL_THRESHOLD:
            self.scroll_x += self.player.x - SCROLL_THRESHOLD
            self.player.x = SCROLL_THRESHOLD

    def update_platforms(self):
        """Atualiza as plataformas."""
        last_plat = self.platforms[-1].rect
        if last_plat.x - self.scroll_x < WIDTH:
            new_x = last_plat.x + random.randint(200, 300)
            new_y = random.choice([350, 400, 450])
            if abs(new_y - last_plat.y) > 100:
                new_x = last_plat.x + 200
            self.platforms.append(Platform(new_x, new_y, 200, 20))

        if len(self.platforms) > 5 and self.platforms[0].rect.x + self.platforms[0].rect.width < self.scroll_x:
            self.platforms.pop(0)

    def update(self):
        """Atualiza o estado geral do jogo."""
        if self.game_state == MENU:
            self.bg_scroll += 1
        elif self.game_state == PLAYING:
            self.bg_scroll = self.scroll_x

        if self.game_state != PLAYING:
            return

        self.update_player()
        self.update_scroll()
        self.update_platforms()
        self.update_enemies()

        self.enemy_spawn_timer += 1
        if self.enemy_spawn_timer >= 90 and random.random() < 0.7:
            self.spawn_enemy()
            self.enemy_spawn_timer = 0

        if self.player.top > HEIGHT:
            self.game_state = GAME_OVER

    def draw_background(self):
        """Desenha o fundo do jogo."""
        self.bg_scroll = self.bg_scroll % BG_WIDTH
        screen.blit("background/ocean", (-self.bg_scroll, 0))
        screen.blit("background/ocean", (-self.bg_scroll + BG_WIDTH, 0))

    def draw_menu(self):
        """Desenha o menu principal."""
        screen.clear()
        self.draw_background()
        screen.draw.text("Profundezas do Mar", center=(WIDTH / 2, 150), fontsize=70, color="white")
        start_btn = Rect(300, 250, 200, 50)
        quit_btn = Rect(300, 350, 200, 50)
        screen.draw.filled_rect(start_btn, (0, 200, 0))
        screen.draw.text("INICIAR", center=start_btn.center, fontsize=40, color="white")
        screen.draw.filled_rect(quit_btn, (200, 0, 0))
        screen.draw.text("SAIR", center=quit_btn.center, fontsize=40, color="white")
        screen.draw.filled_rect(self.music_button, (0, 0, 200))
        label = "MUSICA: ON" if self.music_playing else "MUSICA: OFF"
        screen.draw.text(label, center=self.music_button.center, fontsize=30, color="white")
        screen.draw.text("By Adalmando Araújo", center=(WIDTH / 2, 570), fontsize=30, color="white")

    def draw_game(self):
        """Desenha a tela do jogo."""
        screen.clear()
        self.draw_background()
        screen.draw.text(f"Pontuação: {self.score}", topright=(WIDTH - 10, 10), fontsize=40, color="black")

        for platform in self.platforms:
            platform.draw(self.scroll_x)

        for enemy in self.enemies:
            enemy.x -= self.scroll_x
            enemy.draw()
            enemy.x += self.scroll_x

        self.player.draw()
        menu_btn = Rect(10, 10, 120, 40)
        screen.draw.filled_rect(menu_btn, (0, 0, 200))
        screen.draw.text("MENU", center=menu_btn.center, fontsize=30, color="white")

    def draw_game_over(self):
        """Desenha a tela de game over."""
        screen.draw.text("GAME OVER", center=(WIDTH / 2, 250), fontsize=70, color="white")
        screen.draw.text("Pressione qualquer tecla para reiniciar", center=(WIDTH / 2, 350), fontsize=30, color="white")

        if self.music_playing and not self.played_game_over_sound:
            sounds.game_over.play()
            sounds.game_over.set_volume(0.5)
            self.played_game_over_sound = True

    def toggle_music(self):
        """Liga/desliga a música."""
        self.music_playing = not self.music_playing
        if self.music_playing:
            music.play('background')
        else:
            music.stop()

game = Game()

def update():
    """Função update do Pygame Zero."""
    game.update()

def draw():
    """Função draw do Pygame Zero."""
    if game.game_state == MENU:
        game.draw_menu()
    elif game.game_state == PLAYING:
        game.draw_game()
    elif game.game_state == GAME_OVER:
        game.draw_game()
        game.draw_game_over()

def on_key_down(key):
    """Gerencia eventos de tecla."""
    if game.game_state == PLAYING and key == keys.UP and game.player.on_ground:
        game.player.vy = JUMP_STRENGTH
        game.player.on_ground = False
    elif game.game_state == GAME_OVER:
        game.reset_game()

def on_mouse_down(pos):
    """Gerencia eventos de clique do mouse."""
    if game.game_state == MENU:
        start_btn = Rect(300, 250, 200, 50)
        quit_btn = Rect(300, 350, 200, 50)
        if start_btn.collidepoint(pos):
            game.reset_game()
        elif quit_btn.collidepoint(pos):
            quit()
        elif game.music_button.collidepoint(pos):
            game.toggle_music()
    elif game.game_state == PLAYING:
        menu_btn = Rect(10, 10, 120, 40)
        if menu_btn.collidepoint(pos):
            game.game_state = MENU

pgzrun.go()