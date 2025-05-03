import pygame
import os
import math
import librosa
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import threading
import random
from PIL import Image, ImageSequence

# 初始化 Pygame
pygame.init()
# 初始化音效模块
pygame.mixer.init()

# 加载音效
click_sound = pygame.mixer.Sound(os.path.join('assets', 'click.ogg'))
level_sound = pygame.mixer.Sound(os.path.join('assets', 'level.ogg'))

# 定义常用颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
LIGHT_GREEN = (0, 255, 0, 128)  # 淡绿色，用于按钮悬停遮罩

# 定义屏幕尺寸
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("其实是思道睿大战恶魂？")

# 加载不同用途的字体，缩小部分字体大小
button_font = pygame.font.Font(os.path.join('assets', 'font.ttf'), 30)
title_font = pygame.font.Font(os.path.join('assets', 'font.ttf'), 72)
small_font = pygame.font.Font(os.path.join('assets', 'font.ttf'), 18)
medium_font = pygame.font.Font(os.path.join('assets', 'font.ttf'), 20)
# 提前渲染一些不变的文本
game_over_text_render = title_font.render("游戏结束", True, WHITE)
pause_text_render = title_font.render("游戏暂停", True, WHITE)

# 加载按钮背景图片
button_bg = pygame.image.load(os.path.join('assets', 'BlankPlate.png'))


def load_images():
    """加载游戏所需图片资源并缩放"""
    image_paths = {
        "steve": "Steve.png",
        "fireball": "fireball.png",
        "snowball": "snowball.png",
        "ghost": "Ghost.png",
        "bg": random.choice(["bg1.png", "bg2.png", "bg3.png"]),
        "title": "title.png"
    }
    images = {}
    for key, path in image_paths.items():
        img = pygame.image.load(os.path.join('assets', path))
        if key == "bg":
            img = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        elif key == "title":
            scale_factor = 0.5
            width = int(img.get_width() * scale_factor)
            height = int(img.get_height() * scale_factor)
            img = pygame.transform.scale(img, (width, height))
        elif key == "steve":
            scale_factor = 0.23
            width = int(img.get_width() * scale_factor)
            height = int(img.get_height() * scale_factor)
            img = pygame.transform.scale(img, (width, height))
        elif key == "ghost":
            scale_factor = 0.3
            width = int(img.get_width() * scale_factor)
            height = int(img.get_height() * scale_factor)
            img = pygame.transform.scale(img, (width, height))
        elif key in ["fireball", "snowball"]:
            img = pygame.transform.scale(img, (30, 30))
        images[key] = img
    return images


# 加载图片资源
images = load_images()

# 加载 GIF 动画帧
gif = Image.open(os.path.join('assets', 'happyghost.gif'))
frames = []
for frame in ImageSequence.Iterator(gif):
    frame = frame.convert("RGBA")
    scale_factor = 0.5
    width = int(frame.width * scale_factor)
    height = int(frame.height * scale_factor)
    frame = frame.resize((width, height), Image.LANCZOS)
    pygame_frame = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode)
    frames.append(pygame_frame)

# 定义场地格子宽度，将屏幕分为四列
GRID_WIDTH = SCREEN_WIDTH // 4


class Steve(pygame.sprite.Sprite):
    def __init__(self, x, y, health, is_invincible=False):
        """初始化史蒂夫角色"""
        super().__init__()
        self.image = images["steve"]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.health = health
        self.max_health = health
        self.is_invincible = is_invincible
        self.collision_rect = self.rect.inflate(20, 20)

    def move(self, key):
        """根据按键移动史蒂夫位置"""
        grid_mapping = {
            pygame.K_a: 0,
            pygame.K_s: GRID_WIDTH,
            pygame.K_k: GRID_WIDTH * 2 if self.rect.x >= GRID_WIDTH * 2 else self.rect.x,
            pygame.K_l: GRID_WIDTH * 3 if self.rect.x >= GRID_WIDTH * 2 else self.rect.x
        }
        self.rect.x = grid_mapping.get(key, self.rect.x)
        self.collision_rect.center = self.rect.center

    def draw_health(self, screen):
        """绘制史蒂夫生命值信息"""
        if not self.is_invincible:
            health_text = medium_font.render(f"HP: {self.health}/{self.max_health}", True, WHITE)
            bar_width = 300
            bar_height = 20
            x = (SCREEN_WIDTH - bar_width) // 2
            y = SCREEN_HEIGHT - 50
            screen.blit(health_text, (x, y - 30))


class Fireball(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y):
        """初始化火球对象"""
        super().__init__()
        self.image = images["fireball"]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.start_x = x
        self.start_y = y
        self.target_x = target_x
        self.target_y = target_y
        self.speed = 1.75
        dx = target_x - x
        dy = target_y - y
        distance = math.hypot(dx, dy)
        self.dx = dx / distance * self.speed if distance > 0 else 0
        self.dy = dy / distance * self.speed if distance > 0 else 0

    def update(self):
        """更新火球位置"""
        self.rect.x += self.dx
        self.rect.y += self.dy


class Snowball(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y):
        """初始化雪球对象"""
        super().__init__()
        self.image = images["snowball"]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.target_x = target_x
        self.target_y = target_y
        self.speed = 8
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        self.dx = dx / distance * self.speed if distance > 0 else 0
        self.dy = dy / distance * self.speed if distance > 0 else 0

    def update(self):
        """更新雪球位置"""
        self.rect.x += self.dx
        self.rect.y += self.dy


class Ghost(pygame.sprite.Sprite):
    def __init__(self, x, y, health):
        """初始化恶魂对象"""
        super().__init__()
        self.image = images["ghost"]
        self.original_image = images["ghost"].copy()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.health = health
        self.max_health = health
        self.hit_timer = 0

    def draw_health_bar(self, screen):
        """绘制恶魂生命值条"""
        bar_width = 200
        bar_height = 20
        x = (SCREEN_WIDTH - bar_width) // 2
        y = 20
        pygame.draw.rect(screen, BLACK, (x, y, bar_width, bar_height))
        fill_width = (self.health / self.max_health) * bar_width
        pygame.draw.rect(screen, RED, (x, y, fill_width, bar_height))

    def draw_health_percentage(self, screen):
        """绘制恶魂生命值百分比"""
        percentage = (self.health / self.max_health) * 100
        percentage_text = medium_font.render(f"恶魂血量: {percentage:.2f}%", True, WHITE)
        screen.blit(percentage_text, (SCREEN_WIDTH - percentage_text.get_width() - 10, 10))

    def take_hit(self):
        """恶魂受击处理"""
        self.health -= 1
        self.hit_timer = 10
        red_surface = pygame.Surface(self.image.get_size())
        red_surface.fill((255, 0, 0, 128))
        self.image = self.original_image.copy()
        self.image.blit(red_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def update(self):
        """更新恶魂状态"""
        if self.hit_timer > 0:
            self.hit_timer -= 1
            if self.hit_timer == 0:
                self.image = self.original_image.copy()


def generate_fireballs(beat_times, ghost_x, ghost_y, steve_y, steve_height):
    """根据鼓点生成火球弹幕列表"""
    fireballs = []
    for t in beat_times:
        target_grid = random.randint(0, 3)
        target_x = target_grid * GRID_WIDTH + images["steve"].get_width() // 2
        target_y = steve_y + steve_height // 2
        x = ghost_x + images["ghost"].get_width() // 2
        y = ghost_y + images["ghost"].get_height() // 2
        fireball = Fireball(x, y, target_x, target_y)
        fireballs.append((t * 1000, fireball))
    return fireballs


def play_opening_animation():
    """播放游戏开场动画"""
    cap = cv2.VideoCapture(os.path.join('assets', 'open.mp4'))
    clock = pygame.time.Clock()
    while cap.isOpened():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                cap.release()
                return
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)
            frame = pygame.surfarray.make_surface(frame)
            frame = pygame.transform.flip(frame, True, False)
            frame = pygame.transform.scale(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
            screen.blit(frame, (0, 0))
            pygame.display.flip()
            clock.tick(30)
        else:
            break
    cap.release()


def process_audio(file_path):
    """处理音频文件，提取鼓点信息"""
    try:
        y, sr = librosa.load(file_path)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        return y, sr, tempo, beat_frames, beat_times
    except Exception as e:
        print(f"音频处理出错: {e}")
        return None


def show_audio_processing_text(file_path):
    """显示音频处理提示信息并后台处理音频"""
    base_text = "处理中，请稍后"
    dots = ""
    dot_count = 0
    clock = pygame.time.Clock()
    while True:
        processing_text = button_font.render(base_text + dots, True, WHITE)
        screen.blit(images["bg"], (0, 0))
        screen.blit(processing_text, (SCREEN_WIDTH // 2 - processing_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()

        result = None

        def audio_processing():
            nonlocal result
            result = process_audio(file_path)

        audio_thread = threading.Thread(target=audio_processing)
        audio_thread.start()
        while audio_thread.is_alive():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
            dot_count = (dot_count + 1) % 4
            dots = "." * dot_count
            processing_text = button_font.render(base_text + dots, True, WHITE)
            screen.blit(images["bg"], (0, 0))
            screen.blit(processing_text, (SCREEN_WIDTH // 2 - processing_text.get_width() // 2, SCREEN_HEIGHT // 2))
            pygame.display.flip()
            clock.tick(1)

        if result is not None:
            return result


def show_play_instructions():
    """显示游戏玩法说明"""
    try:
        with open(os.path.join('assets', 'wanfa.txt'), 'r', encoding='utf-8') as file:
            instructions = file.read()
        messagebox.showinfo("玩法说明", instructions)
    except FileNotFoundError:
        messagebox.showerror("错误", "未找到玩法说明文件 wanfa.txt")


def show_made_by_text():
    """显示开发者信息"""
    made_by_text = small_font.render("Made in JohnWong", True, WHITE)
    screen.blit(made_by_text, (SCREEN_WIDTH - made_by_text.get_width() - 10,
                               SCREEN_HEIGHT - made_by_text.get_height() - 10))


def draw_button_with_bg(text, x, y):
    """绘制带背景按钮并处理鼠标悬停效果"""
    text_surface = button_font.render(text, True, WHITE)
    text_width, text_height = text_surface.get_size()
    bg_width = text_width + 20
    bg_height = text_height + 10
    scaled_bg = pygame.transform.scale(button_bg, (bg_width, bg_height))
    mouse_x, mouse_y = pygame.mouse.get_pos()
    if x - 10 <= mouse_x <= x - 10 + bg_width and y - 5 <= mouse_y <= y - 5 + bg_height:
        mask = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
        mask.fill(LIGHT_GREEN)
        screen.blit(scaled_bg, (x - 10, y - 5))
        screen.blit(mask, (x - 10, y - 5))
    else:
        screen.blit(scaled_bg, (x - 10, y - 5))
    screen.blit(text_surface, (x, y))
    return pygame.Rect(x - 10, y - 5, bg_width, bg_height)


def main_menu():
    """显示游戏主菜单"""
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                click_sound.play()
                mouse_x, mouse_y = event.pos
                if start_game_button.collidepoint(mouse_x, mouse_y):
                    select_difficulty()
                elif play_instructions_button.collidepoint(mouse_x, mouse_y):
                    show_play_instructions()
                elif exit_game_button.collidepoint(mouse_x, mouse_y):
                    pygame.quit()
                    quit()
        screen.blit(images["bg"], (0, 0))
        shake_x = math.sin(pygame.time.get_ticks() / 100) * 5
        shake_y = math.cos(pygame.time.get_ticks() / 100) * 5
        screen.blit(images["title"], (SCREEN_WIDTH // 2 - images["title"].get_width() // 2 + shake_x,
                                      50 + shake_y))
        start_game_button = draw_button_with_bg("开始游戏", 300, 250)
        play_instructions_button = draw_button_with_bg("玩法说明", 300, 350)
        exit_game_button = draw_button_with_bg("退出游戏", 300, 450)
        show_made_by_text()
        pygame.display.flip()
        clock.tick(60)


def select_difficulty():
    """显示难度选择界面"""
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                click_sound.play()
                mouse_x, mouse_y = event.pos
                if easy_button.collidepoint(mouse_x, mouse_y):
                    start_game(50, False)
                elif normal_button.collidepoint(mouse_x, mouse_y):
                    start_game(30, False)
                elif hard_button.collidepoint(mouse_x, mouse_y):
                    start_game(10, False)
                elif casual_button.collidepoint(mouse_x, mouse_y):
                    start_game(100, True)
                elif back_button.collidepoint(mouse_x, mouse_y):
                    main_menu()
        screen.blit(images["bg"], (0, 0))
        easy_button = draw_button_with_bg("简单", 300, 200)
        normal_button = draw_button_with_bg("普通", 300, 300)
        hard_button = draw_button_with_bg("困难", 300, 400)
        casual_button = draw_button_with_bg("休闲", 300, 500)
        back_button = draw_button_with_bg("返回", 10, SCREEN_HEIGHT - 50)
        show_made_by_text()
        pygame.display.flip()
        clock.tick(60)


def start_game(steve_health, is_invincible):
    """开始游戏主逻辑"""
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("MP3 Files", "*.mp3")])
    if not file_path:
        return
    result = show_audio_processing_text(file_path)
    if result is None:
        return
    y, sr, tempo, beat_frames, beat_times = result
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    steve1 = Steve(0, SCREEN_HEIGHT - images["steve"].get_height(), steve_health, is_invincible)
    steve2 = Steve(GRID_WIDTH * 3, SCREEN_HEIGHT - images["steve"].get_height(), steve_health, is_invincible)
    ghost = Ghost(SCREEN_WIDTH // 2 - images["ghost"].get_width() // 2, 50, len(beat_times))
    music_duration = librosa.get_duration(y=y, sr=sr) * 1000
    fireballs_with_times = generate_fireballs(
        beat_times, ghost.rect.x, ghost.rect.y,
        steve1.rect.y, images["steve"].get_height()
    )
    snowballs = pygame.sprite.Group()
    clock = pygame.time.Clock()
    music_start_time = pygame.time.get_ticks()
    current_fireball_index = 0
    paused = False

    def retry_game():
        """重试游戏，不重新选择歌曲"""
        nonlocal steve1, steve2, ghost, fireballs_with_times, snowballs, music_start_time, current_fireball_index, paused
        steve1 = Steve(0, SCREEN_HEIGHT - images["steve"].get_height(), steve_health, is_invincible)
        steve2 = Steve(GRID_WIDTH * 3, SCREEN_HEIGHT - images["steve"].get_height(), steve_health, is_invincible)
        ghost = Ghost(SCREEN_WIDTH // 2 - images["ghost"].get_width() // 2, 50, len(beat_times))
        fireballs_with_times = generate_fireballs(
            beat_times, ghost.rect.x, ghost.rect.y,
            steve1.rect.y, images["steve"].get_height()
        )
        snowballs = pygame.sprite.Group()
        music_start_time = pygame.time.get_ticks()
        current_fireball_index = 0
        paused = False
        pygame.mixer.music.play()

    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.mixer.music.stop()
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_a, pygame.K_s]:
                    steve1.move(event.key)
                elif event.key in [pygame.K_k, pygame.K_l]:
                    steve2.move(event.key)
                if event.key == pygame.K_ESCAPE:
                    paused = not paused
                    if paused:
                        pygame.mixer.music.pause()
                    else:
                        pygame.mixer.music.unpause()
                        music_start_time = pygame.time.get_ticks() - (pygame.time.get_ticks() - music_start_time)
            if event.type == pygame.MOUSEBUTTONDOWN:
                click_sound.play()

        if paused:
            screen.blit(images["bg"], (0, 0))
            screen.blit(pause_text_render, (SCREEN_WIDTH // 2 - pause_text_render.get_width() // 2, 100))
            resume_button = draw_button_with_bg("返回", 300, 200)
            retry_button = draw_button_with_bg("再来一次", 300, 300)
            back_to_menu_button = draw_button_with_bg("回到主菜单", 300, 400)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    click_sound.play()
                    mouse_x, mouse_y = event.pos
                    if resume_button.collidepoint(mouse_x, mouse_y):
                        paused = False
                        pygame.mixer.music.unpause()
                        music_start_time = pygame.time.get_ticks() - (pygame.time.get_ticks() - music_start_time)
                    elif retry_button.collidepoint(mouse_x, mouse_y):
                        retry_game()
                    elif back_to_menu_button.collidepoint(mouse_x, mouse_y):
                        pygame.mixer.music.stop()
                        main_menu()
        else:
            screen.blit(images["bg"], (0, 0))
            elapsed_time = pygame.time.get_ticks() - music_start_time
            while current_fireball_index < len(fireballs_with_times) and elapsed_time >= \
                    fireballs_with_times[current_fireball_index][0]:
                fireball = fireballs_with_times[current_fireball_index][1]
                current_fireball_index += 1
            for fireball in [fb[1] for fb in fireballs_with_times[:current_fireball_index]]:
                fireball.update()
                if fireball.rect.y >= SCREEN_HEIGHT - images["steve"].get_height():
                    if not steve1.is_invincible:
                        steve1.health -= 1
                        steve2.health -= 1
                    fireballs_with_times = [fb for fb in fireballs_with_times if fb[1] != fireball]
                if pygame.Rect.colliderect(steve1.collision_rect, fireball.rect) or pygame.Rect.colliderect(
                        steve2.collision_rect, fireball.rect):
                    target_x = ghost.rect.x + images["ghost"].get_width() // 2
                    target_y = ghost.rect.y + images["ghost"].get_height() // 2
                    snowball = Snowball(fireball.rect.x, fireball.rect.y, target_x, target_y)
                    snowballs.add(snowball)
                    fireballs_with_times = [fb for fb in fireballs_with_times if fb[1] != fireball]
            for snowball in snowballs:
                snowball.update()
                if pygame.sprite.collide_rect(ghost, snowball):
                    ghost.take_hit()
                    snowballs.remove(snowball)
            ghost.update()
            screen.blit(ghost.image, ghost.rect)
            ghost.draw_health_bar(screen)
            ghost.draw_health_percentage(screen)
            for fireball in [fb[1] for fb in fireballs_with_times[:current_fireball_index]]:
                screen.blit(fireball.image, fireball.rect)
            for snowball in snowballs:
                screen.blit(snowball.image, snowball.rect)
            screen.blit(steve1.image, steve1.rect)
            screen.blit(steve2.image, steve2.rect)
            steve1.draw_health(screen)
            progress = elapsed_time / music_duration
            bar_width = 220
            bar_height = 20
            x = 10
            y = 10
            pygame.draw.rect(screen, BLACK, (x, y, bar_width, bar_height))
            fill_width = progress * bar_width
            pygame.draw.rect(screen, GREEN, (x, y, fill_width, bar_height))
            elapsed_minutes = int(elapsed_time // 60000)
            elapsed_seconds = int((elapsed_time % 60000) // 1000)
            total_minutes = int(music_duration // 60000)
            total_seconds = int((music_duration % 60000) // 1000)
            time_text = medium_font.render(
                f"{elapsed_minutes:02d}:{elapsed_seconds:02d}---{total_minutes:02d}:{total_seconds:02d}", True, WHITE)
            screen.blit(time_text, (x, y + bar_height + 5))
            if not steve1.is_invincible and steve1.health <= 0:
                pygame.mixer.music.stop()
                game_over(ghost)
            if ghost.health <= 0:
                pygame.mixer.music.stop()
                game_win(ghost)
            if elapsed_time >= music_duration:
                pygame.mixer.music.stop()
                if steve1.health > 0:
                    game_win(ghost)
                else:
                    game_over(ghost)
        show_made_by_text()
        pygame.display.flip()
        clock.tick(60)


def game_over(ghost):
    """显示游戏结束界面"""
    level_sound.play()
    clock = pygame.time.Clock()
    percentage = (ghost.health / ghost.max_health) * 100
    frame_index = 0
    button_y_start = 350
    button_gap = 100
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                click_sound.play()
                mouse_x, mouse_y = event.pos
                if retry_button.collidepoint(mouse_x, mouse_y):
                    select_difficulty()
                elif back_to_menu_button.collidepoint(mouse_x, mouse_y):
                    main_menu()
        screen.blit(images["bg"], (0, 0))
        screen.blit(game_over_text_render, (SCREEN_WIDTH // 2 - game_over_text_render.get_width() // 2, 95))
        screen.blit(frames[frame_index], (SCREEN_WIDTH // 2 - frames[frame_index].get_width() // 2, 150))
        frame_index = (frame_index + 1) % len(frames)
        percentage_text = button_font.render(f"恶魂剩余血量: {percentage:.2f}%", True, BLACK)
        screen.blit(percentage_text, (SCREEN_WIDTH // 2 - percentage_text.get_width() // 2, 250))
        retry_button = draw_button_with_bg("再来一次", 300, button_y_start)
        back_to_menu_button = draw_button_with_bg("回到主菜单", 300, button_y_start + button_gap)
        show_made_by_text()
        pygame.display.flip()
        clock.tick(10)


def game_win(ghost):
    """显示游戏胜利界面，改为游戏结束"""
    level_sound.play()
    clock = pygame.time.Clock()
    percentage = (ghost.health / ghost.max_health) * 100
    frame_index = 0
    button_y_start = 350
    button_gap = 100
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                click_sound.play()
                mouse_x, mouse_y = event.pos
                if retry_button.collidepoint(mouse_x, mouse_y):
                    select_difficulty()
                elif back_to_menu_button.collidepoint(mouse_x, mouse_y):
                    main_menu()
        screen.blit(images["bg"], (0, 0))
        screen.blit(game_over_text_render, (SCREEN_WIDTH // 2 - game_over_text_render.get_width() // 2, 95))
        screen.blit(frames[frame_index], (SCREEN_WIDTH // 2 - frames[frame_index].get_width() // 2, 150))
        frame_index = (frame_index + 1) % len(frames)
        percentage_text = button_font.render(f"恶魂剩余血量: {percentage:.2f}%", True, BLACK)
        screen.blit(percentage_text, (SCREEN_WIDTH // 2 - percentage_text.get_width() // 2, 250))
        retry_button = draw_button_with_bg("再来一次", 300, button_y_start)
        back_to_menu_button = draw_button_with_bg("回到主菜单", 300, button_y_start + button_gap)
        show_made_by_text()
        pygame.display.flip()
        clock.tick(10)


if __name__ == "__main__":
    play_opening_animation()
    main_menu()