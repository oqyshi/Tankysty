import os, pygame, random, uuid

SCREEN_SIZE = [480, 416]


def load_image(name, colorkey=None):
    fullname = os.path.join('pictures/tanki', name)
    image = pygame.image.load(fullname).convert()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


class myRect(pygame.Rect):

    def __init__(self, left, top, width, height, type):
        pygame.Rect.__init__(self, left, top, width, height)
        self.type = type


class Timer(object):
    def __init__(self):
        self.timers = []

    def add(self, interval, f, repeat=-1):
        options = {
            "interval": interval,
            "callback": f,
            "repeat": repeat,
            "times": 0,
            "time": 0,
            "uuid": uuid.uuid4()
        }
        self.timers.append(options)

        return options["uuid"]

    def destroy(self, uuid_nr):
        for timer in self.timers:
            if timer["uuid"] == uuid_nr:
                self.timers.remove(timer)
                return

    def update(self, time_passed):
        for timer in self.timers:
            timer["time"] += time_passed
            if timer["time"] > timer["interval"]:
                timer["time"] -= timer["interval"]
                timer["times"] += 1
                if timer["repeat"] > -1 and timer["times"] == timer["repeat"]:
                    self.timers.remove(timer)
                try:
                    timer["callback"]()
                except:
                    try:
                        self.timers.remove(timer)
                    except:
                        pass


class Bullet:
    (DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT) = range(4)
    (STATE_REMOVED, STATE_ACTIVE) = range(2)
    (OWNER_PLAYER, OWNER_ENEMY) = range(2)

    def __init__(self, level, position, direction, damage=100, speed=5):
        global sprites
        self.level = level
        self.direction = direction
        self.damage = damage
        self.owner = None
        self.owner_class = None
        self.power = 1
        self.image = pygame.Surface([6, 6])
        pygame.draw.circle(self.image, (155, 155, 155), (3, 3), 3)
        if direction == self.DIR_UP:
            self.rect = pygame.Rect(position[0] + 11, position[1] - 8, 6, 8)
        elif direction == self.DIR_RIGHT:
            self.rect = pygame.Rect(position[0] + 26, position[1] + 11, 8, 6)
        elif direction == self.DIR_DOWN:
            self.rect = pygame.Rect(position[0] + 11, position[1] + 26, 6, 8)
        elif direction == self.DIR_LEFT:
            self.rect = pygame.Rect(position[0] - 8, position[1] + 11, 8, 6)
        self.speed = speed
        self.state = self.STATE_ACTIVE

    def draw(self):
        global screen
        if self.state == self.STATE_ACTIVE:
            screen.blit(self.image, self.rect.topleft)

    def update(self):
        global players, bullets
        if self.state != self.STATE_ACTIVE:
            return
        if self.direction == self.DIR_UP:
            self.rect.topleft = [self.rect.left, self.rect.top - self.speed]
            if self.rect.top < 0:
                self.destroy()
                return
        elif self.direction == self.DIR_RIGHT:
            self.rect.topleft = [self.rect.left + self.speed, self.rect.top]
            if self.rect.left > (416 - self.rect.width):
                self.destroy()
                return
        elif self.direction == self.DIR_DOWN:
            self.rect.topleft = [self.rect.left, self.rect.top + self.speed]
            if self.rect.top > (416 - self.rect.height):
                self.destroy()
                return
        elif self.direction == self.DIR_LEFT:
            self.rect.topleft = [self.rect.left - self.speed, self.rect.top]
            if self.rect.left < 0:
                self.destroy()
                return

        has_collided = False

        rects = self.level.obstacle_rects
        collisions = self.rect.collidelistall(rects)
        if collisions != []:
            for i in collisions:
                if self.level.hitTile(rects[i].topleft, self.power, self.owner == self.OWNER_PLAYER):
                    has_collided = True
        if has_collided:
            self.destroy()
            return

        for bullet in bullets:
            if self.state == self.STATE_ACTIVE and bullet.owner != self.owner and bullet != self and self.rect.colliderect(
                    bullet.rect):
                self.destroy()
                return

        for player in players:
            if player.state == player.STATE_ALIVE and self.rect.colliderect(player.rect):
                if player.bulletImpact(self.owner == self.OWNER_PLAYER, self.damage, self.owner_class):
                    self.destroy()
                    return

        for enemy in enemies:
            if enemy.state == enemy.STATE_ALIVE and self.rect.colliderect(enemy.rect):
                if enemy.bulletImpact(self.owner == self.OWNER_ENEMY, self.damage, self.owner_class):
                    self.destroy()
                    return

    def destroy(self):
        self.state = self.STATE_REMOVED


class Level:
    (TILE_EMPTY, TILE_BRICK, TILE_STEEL, TILE_WATER, TILE_GRASS, TILE_SAND) = range(6)
    TILE_SIZE = 16

    def __init__(self, level_nr=None):

        global sprites

        self.max_active_enemies = 4

        self.tile_empty = pygame.Surface((8 * 2, 8 * 2))
        self.tile_brick = game.images['brick']
        self.tile_steel = game.images['steel']
        self.tile_grass = game.images['grass']
        self.tile_water = game.images['water']
        self.tile_sand = game.images['sand']

        level_nr = 1 if level_nr == None else level_nr % 21
        if level_nr == 0:
            level_nr = 21
        self.loadLevel(level_nr)
        self.obstacle_rects = []
        self.SANDS = []
        self.updateObstacleRects()

    def hitTile(self, pos, power=1, sound=False):

        global play_sounds, sounds

        for tile in self.mapr:
            if tile.topleft == pos:
                if tile.type == self.TILE_BRICK:
                    self.mapr.remove(tile)
                    self.updateObstacleRects()
                    return True
                elif tile.type == self.TILE_STEEL:
                    if power == 2:
                        self.mapr.remove(tile)
                        self.updateObstacleRects()
                    return True
                else:
                    return False

    def loadLevel(self, level_nr=1):
        filename = "levels/" + str(level_nr)
        if (not os.path.isfile(filename)):
            return False
        level = []
        f = open(filename, "r")
        data = f.read().split("\n")
        self.mapr = []
        x, y = 0, 0
        for row in data:
            for ch in row:
                if ch == "#":
                    self.mapr.append(myRect(x, y, self.TILE_SIZE, self.TILE_SIZE, self.TILE_BRICK))
                elif ch == "@":
                    self.mapr.append(myRect(x, y, self.TILE_SIZE, self.TILE_SIZE, self.TILE_STEEL))
                elif ch == "~":
                    self.mapr.append(myRect(x, y, self.TILE_SIZE, self.TILE_SIZE, self.TILE_WATER))
                elif ch == "%":
                    self.mapr.append(myRect(x, y, self.TILE_SIZE, self.TILE_SIZE, self.TILE_GRASS))
                elif ch == "-":
                    self.mapr.append(myRect(x, y, self.TILE_SIZE, self.TILE_SIZE, self.TILE_SAND))
                x += self.TILE_SIZE
            x = 0
            y += self.TILE_SIZE
        return True

    def draw(self, tiles=None):
        global screen

        if tiles == None:
            tiles = [self.TILE_BRICK, self.TILE_STEEL, self.TILE_WATER, self.TILE_GRASS, self.TILE_SAND]

        for tile in self.mapr:
            if tile.type in tiles:
                if tile.type == self.TILE_BRICK:
                    screen.blit(self.tile_brick, tile.topleft)
                elif tile.type == self.TILE_STEEL:
                    screen.blit(self.tile_steel, tile.topleft)
                elif tile.type == self.TILE_WATER:
                    screen.blit(self.tile_water, tile.topleft)
                elif tile.type == self.TILE_SAND:
                    screen.blit(self.tile_sand, tile.topleft)
                elif tile.type == self.TILE_GRASS:
                    screen.blit(self.tile_grass, tile.topleft)

    def updateObstacleRects(self):
        self.obstacle_rects = []
        for tile in self.mapr:
            if tile.type in (self.TILE_BRICK, self.TILE_STEEL, self.TILE_WATER):
                self.obstacle_rects.append(tile)
            if tile.type == self.TILE_SAND:
                self.SANDS.append(tile)


class Tank:
    (DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT) = range(4)
    (STATE_SPAWNING, STATE_DEAD, STATE_ALIVE) = range(3)
    (SIDE_PLAYER, SIDE_ENEMY) = range(2)

    def __init__(self, level, side, position=None, direction=None, filename=None):

        global sprites
        self.health = 100
        self.paralised = False
        self.paused = False
        self.shielded = False
        self.speed = 3
        self.max_active_bullets = 1
        self.side = side
        self.flash = 0
        self.superpowers = 0
        self.bonus = None
        self.controls = [pygame.K_SPACE, pygame.K_UP, pygame.K_RIGHT, pygame.K_DOWN, pygame.K_LEFT]
        self.pressed = [False] * 4
        self.level = level
        if position != None:
            self.rect = pygame.Rect(position, (26, 26))
        else:
            self.rect = pygame.Rect(0, 0, 26, 26)

        if direction == None:
            self.direction = random.choice([self.DIR_RIGHT, self.DIR_DOWN, self.DIR_LEFT])
        else:
            self.direction = direction
        self.state = self.STATE_ALIVE

    def draw(self):
        global screen
        if self.state == self.STATE_ALIVE:
            screen.blit(self.image, self.rect.topleft)

    def fire(self, forced=False):
        global bullets, labels
        if self.state != self.STATE_ALIVE:
            gtimer.destroy(self.timer_uuid_fire)
            return False
        if self.paused:
            return False

        if not forced:
            active_bullets = 0
            for bullet in bullets:
                if bullet.owner_class == self and bullet.state == bullet.STATE_ACTIVE:
                    active_bullets += 1
            if active_bullets >= self.max_active_bullets:
                return False

        bullet = Bullet(self.level, self.rect.topleft, self.direction)
        if self.side == self.SIDE_PLAYER:
            bullet.owner = self.SIDE_PLAYER
        else:
            bullet.owner = self.SIDE_ENEMY
            self.bullet_queued = False
        bullet.owner_class = self
        bullets.append(bullet)
        return True

    def rotate(self, direction, fix_position=True):
        self.direction = direction
        if direction == self.DIR_UP:
            self.image = self.image_up
        elif direction == self.DIR_RIGHT:
            self.image = self.image_right
        elif direction == self.DIR_DOWN:
            self.image = self.image_down
        elif direction == self.DIR_LEFT:
            self.image = self.image_left
        if fix_position:
            new_x = self.nearest(self.rect.left, 8) + 3
            new_y = self.nearest(self.rect.top, 8) + 3
            if (abs(self.rect.left - new_x) < 5):
                self.rect.left = new_x
            if (abs(self.rect.top - new_y) < 5):
                self.rect.top = new_y

    def update(self, time_passed):
        pass

    def nearest(self, num, base):
        return int(round(num / (base * 1.0)) * base)

    def bulletImpact(self, friendly_fire=False, damage=100, tank=None):
        global play_sounds, sounds
        if self.shielded:
            return True

        if not friendly_fire:
            self.health -= damage
            if self.health < 1:
                if self.side == self.SIDE_ENEMY:
                    tank.trophies["enemy" + str(self.type)] += 1
                    points = (self.type + 1) * 100
                    tank.score += points
                self.state = self.STATE_DEAD
            return True

        if self.side == self.SIDE_ENEMY:
            return False
        elif self.side == self.SIDE_PLAYER:
            if not self.paralised:
                self.setParalised(True)
            return True

    def setParalised(self, paralised=True):
        if self.state != self.STATE_ALIVE:
            return
        self.paralised = paralised


class Enemy(Tank):
    (TYPE_BASIC, TYPE_FAST, TYPE_POWER, TYPE_ARMOR) = range(4)

    def __init__(self, level, type, position=None, direction=None, filename=None):

        Tank.__init__(self, level, type, position=None, direction=None, filename=None)

        global enemies, sprites

        self.bullet_queued = False

        if len(level.enemies_left) > 0:
            self.type = level.enemies_left.pop()
        else:
            self.state = self.STATE_DEAD
            return

        if self.type == self.TYPE_BASIC:
            self.speed = 2
        elif self.type == self.TYPE_FAST:
            self.speed = 4
        elif self.type == self.TYPE_POWER:
            self.superpowers = 1
        elif self.type == self.TYPE_ARMOR:
            self.health = 400

        self.image = game.images['enemy']
        self.image_up = self.image
        self.image_left = pygame.transform.rotate(self.image, 90)
        self.image_down = pygame.transform.rotate(self.image, 180)
        self.image_right = pygame.transform.rotate(self.image, 270)

        self.rotate(self.direction, False)

        if position == None:
            self.rect.topleft = self.getFreeSpawningPosition()
            if not self.rect.topleft:
                self.state = self.STATE_DEAD
                return

        self.path = self.generatePath(self.direction)
        self.timer_uuid_fire = gtimer.add(1000, lambda: self.fire())

    def getFreeSpawningPosition(self):

        global players, enemies

        available_positions = [
            [(self.level.TILE_SIZE * 2 - self.rect.width) / 2, (self.level.TILE_SIZE * 2 - self.rect.height) / 2],
            [12 * self.level.TILE_SIZE + (self.level.TILE_SIZE * 2 - self.rect.width) / 2,
             (self.level.TILE_SIZE * 2 - self.rect.height) / 2],
            [24 * self.level.TILE_SIZE + (self.level.TILE_SIZE * 2 - self.rect.width) / 2,
             (self.level.TILE_SIZE * 2 - self.rect.height) / 2]
        ]

        random.shuffle(available_positions)

        for pos in available_positions:

            enemy_rect = pygame.Rect(pos, [26, 26])

            collision = False
            for enemy in enemies:
                if enemy_rect.colliderect(enemy.rect):
                    collision = True
                    continue

            if collision:
                continue

            collision = False
            for player in players:
                if enemy_rect.colliderect(player.rect):
                    collision = True
                    continue

            if collision:
                continue

            return pos
        return False

    def move(self):

        global players, enemies

        if self.state != self.STATE_ALIVE or self.paused or self.paralised:
            return

        if self.path == []:
            self.path = self.generatePath(None, True)

        new_position = self.path.pop(0)

        if self.direction == self.DIR_UP:
            if new_position[1] < 0:
                self.path = self.generatePath(self.direction, True)
                return
        elif self.direction == self.DIR_RIGHT:
            if new_position[0] > 390:
                self.path = self.generatePath(self.direction, True)
                return
        elif self.direction == self.DIR_DOWN:
            if new_position[1] > 390:
                self.path = self.generatePath(self.direction, True)
                return
        elif self.direction == self.DIR_LEFT:
            if new_position[0] < 0:
                self.path = self.generatePath(self.direction, True)
                return

        new_rect = pygame.Rect(new_position, [26, 26])

        if new_rect.collidelist(self.level.obstacle_rects) != -1:
            self.path = self.generatePath(self.direction, True)
            return

        for enemy in enemies:
            if enemy != self and new_rect.colliderect(enemy.rect):
                self.turnBack()
                self.path = self.generatePath(self.direction)
                return

        for player in players:
            if new_rect.colliderect(player.rect):
                self.turnBack()
                self.path = self.generatePath(self.direction)
                return

        self.rect.topleft = new_rect.topleft

    def update(self, time_passed):
        Tank.update(self, time_passed)
        if self.state == self.STATE_ALIVE and not self.paused:
            self.move()

    def turnBack(self):
        if self.direction in (self.DIR_UP, self.DIR_RIGHT):
            self.rotate(self.direction + 2, False)
        else:
            self.rotate(self.direction - 2, False)

    def generatePath(self, direction=None, fix_direction=False):

        all_directions = [self.DIR_UP, self.DIR_RIGHT, self.DIR_DOWN, self.DIR_LEFT]

        if direction == None:
            if self.direction in [self.DIR_UP, self.DIR_RIGHT]:
                opposite_direction = self.direction + 2
            else:
                opposite_direction = self.direction - 2
            directions = all_directions
            random.shuffle(directions)
            directions.remove(opposite_direction)
            directions.append(opposite_direction)
        else:
            if direction in [self.DIR_UP, self.DIR_RIGHT]:
                opposite_direction = direction + 2
            else:
                opposite_direction = direction - 2
            directions = all_directions
            random.shuffle(directions)
            directions.remove(opposite_direction)
            directions.remove(direction)
            directions.insert(0, direction)
            directions.append(opposite_direction)

        x = int(round(self.rect.left / 16))
        y = int(round(self.rect.top / 16))

        new_direction = None

        for direction in directions:
            if direction == self.DIR_UP and y > 1:
                new_pos_rect = self.rect.move(0, -8)
                if new_pos_rect.collidelist(self.level.obstacle_rects) == -1:
                    new_direction = direction
                    break
            elif direction == self.DIR_RIGHT and x < 24:
                new_pos_rect = self.rect.move(8, 0)
                if new_pos_rect.collidelist(self.level.obstacle_rects) == -1:
                    new_direction = direction
                    break
            elif direction == self.DIR_DOWN and y < 24:
                new_pos_rect = self.rect.move(0, 8)
                if new_pos_rect.collidelist(self.level.obstacle_rects) == -1:
                    new_direction = direction
                    break
            elif direction == self.DIR_LEFT and x > 1:
                new_pos_rect = self.rect.move(-8, 0)
                if new_pos_rect.collidelist(self.level.obstacle_rects) == -1:
                    new_direction = direction
                    break

        if new_direction == None:
            new_direction = opposite_direction

        if fix_direction and new_direction == self.direction:
            fix_direction = False

        self.rotate(new_direction, fix_direction)

        positions = []

        x = self.rect.left
        y = self.rect.top

        axis_fix = 0

        pixels = self.nearest(random.randint(1, 12) * 32, 32) + axis_fix + 3

        if self.rect.collidelist(game.level.SANDS) != -1:
            self.speed = 1
        else:
            if self.type == self.TYPE_FAST:
                self.speed = 4
            else:
                self.speed = 2

        if new_direction == self.DIR_UP:
            for px in range(0, pixels, self.speed):
                positions.append([x, y - px])
        elif new_direction == self.DIR_RIGHT:
            for px in range(0, pixels, self.speed):
                positions.append([x + px, y])
        elif new_direction == self.DIR_DOWN:
            for px in range(0, pixels, self.speed):
                positions.append([x, y + px])
        elif new_direction == self.DIR_LEFT:
            for px in range(0, pixels, self.speed):
                positions.append([x - px, y])

        return positions


class Player(Tank):

    def __init__(self, level, type, position=None, direction=None, filename=None):

        Tank.__init__(self, level, type, position=None, direction=None, filename=None)

        global sprites

        self.start_position = position
        self.start_direction = direction

        self.lives = 3
        self.score = 0

        self.trophies = {
            "bonus": 0,
            "enemy0": 0,
            "enemy1": 0,
            "enemy2": 0,
            "enemy3": 0
        }
        self.image = filename
        self.image_up = self.image
        self.image_left = pygame.transform.rotate(self.image, 90)
        self.image_down = pygame.transform.rotate(self.image, 180)
        self.image_right = pygame.transform.rotate(self.image, 270)

        if direction == None:
            self.rotate(self.DIR_UP, False)
        else:
            self.rotate(direction, False)

    def move(self, direction):
        global players, enemies

        if self.state != self.STATE_ALIVE:
            return
        if self.direction != direction:
            self.rotate(direction)

        if self.rect.collidelist(game.level.SANDS) != -1:
            self.speed = 1
        else:
            self.speed = 3

        if direction == self.DIR_UP:

            new_position = [self.rect.left, self.rect.top - self.speed]
            if new_position[1] < 0:
                return
        elif direction == self.DIR_RIGHT:
            new_position = [self.rect.left + self.speed, self.rect.top]
            if new_position[0] > 390:
                return
        elif direction == self.DIR_DOWN:
            new_position = [self.rect.left, self.rect.top + self.speed]
            if new_position[1] > 390:
                return
        elif direction == self.DIR_LEFT:
            new_position = [self.rect.left - self.speed, self.rect.top]
            if new_position[0] < 0:
                return

        player_rect = pygame.Rect(new_position, [26, 26])

        if player_rect.collidelist(self.level.obstacle_rects) != -1:
            return

        for player in players:
            if player != self and player.state == player.STATE_ALIVE and player_rect.colliderect(player.rect) == True:
                return
        for enemy in enemies:
            if player_rect.colliderect(enemy.rect) == True:
                return

        self.rect.topleft = (new_position[0], new_position[1])

    def reset(self):
        self.rotate(self.start_direction, False)
        self.rect.topleft = self.start_position
        self.superpowers = 0
        self.max_active_bullets = 1
        self.health = 100
        self.paralised = False
        self.paused = False
        self.pressed = [False] * 4
        self.state = self.STATE_ALIVE


class Game:
    (DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT) = range(4)

    TILE_SIZE = 16

    def __init__(self):

        global screen, sprites, play_sounds, sounds

        if play_sounds:
            pygame.mixer.pre_init(44100, -16, 1, 512)

        pygame.init()

        pygame.display.set_caption("Танкисты")

        size = 480, 416

        screen = pygame.display.set_mode(size)

        self.clock = pygame.time.Clock()
        self.images = {
            'player': pygame.transform.scale(load_image('tank.png', -1), (26, 26)),
            'player2': pygame.transform.scale(load_image('tank2.png', -1), (26, 26)),
            'enemy': pygame.transform.scale(load_image('enemy.png', -1), (26, 26)),
            'brick': pygame.transform.scale(load_image('bricks.png', -1), (16, 16)),
            'steel': pygame.transform.scale(load_image('steel.png', -1), (16, 16)),
            'grass': pygame.transform.scale(load_image('grass.png', -1), (16, 16)),
            'water': pygame.transform.scale(load_image('water.png', -1), (16, 16)),
            'sand': pygame.transform.scale(load_image('sand.png', -1), (16, 16)),

        }
        pygame.display.set_icon(self.images['player'])

        self.player_image = pygame.transform.rotate(self.images['player'], 270)

        self.timefreeze = False

        self.im_game_over = pygame.Surface((64, 40))
        self.im_game_over.set_colorkey((0, 0, 0))
        self.im_game_over.blit(pygame.font.Font(None, 50).render("Потрачено", False, (127, 64, 64)), [0, 0])
        self.game_over_y = 456

        self.nr_of_players = 1

        del players[:]
        del enemies[:]
        del bullets[:]

    def spawnEnemy(self):

        global enemies

        if len(enemies) >= self.level.max_active_enemies:
            return
        if len(self.level.enemies_left) < 1 or self.timefreeze:
            return
        enemy = Enemy(self.level, 1)
        enemies.append(enemy)

    def respawnPlayer(self, player, clear_scores=False):
        player.reset()
        if clear_scores:
            player.trophies = {
                "bonus": 0, "enemy0": 0, "enemy1": 0, "enemy2": 0, "enemy3": 0
            }

    def gameOver(self):
        pygame.mixer.music.load('music/lose.mp3')
        pygame.mixer.music.play()
        self.game_over_y = 456

        self.game_over = True
        gtimer.add(3000, lambda: self.showScores(), 1)

    def gameOverScreen(self):
        global screen
        self.running = False
        screen.fill([0, 0, 0])
        screen.blit(pygame.font.Font(None, 50).render("Потрачено", 1, (100, 255, 100)), (165, 210))
        pygame.display.flip()
        while 1:
            self.clock.tick(50)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.showMenu()
                        return

    def showMenu(self):
        global players, screen
        self.running = False
        del gtimer.timers[:]
        self.stage = 0
        main_loop = True
        self.drawIntroScreen()
        while main_loop:
            self.clock.tick(50)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        quit()
                    elif event.key == pygame.K_UP:
                        if self.nr_of_players == 2:
                            self.nr_of_players = 1
                            self.drawIntroScreen()
                    elif event.key == pygame.K_DOWN:
                        if self.nr_of_players == 1:
                            self.nr_of_players = 2
                            self.drawIntroScreen()
                    elif event.key == pygame.K_RETURN:
                        main_loop = False
        del players[:]
        self.nextLevel()

    def reloadPlayers(self):
        global players

        if len(players) == 0:
            x = 8 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2
            y = 24 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2
            player = Player(
                self.level, 0, [x, y], self.DIR_UP, self.images['player']
            )
            player.controls = [102, 119, 100, 115, 97]
            players.append(player)

            if self.nr_of_players == 2:
                x = 16 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2
                y = 24 * self.TILE_SIZE + (self.TILE_SIZE * 2 - 26) / 2
                player = Player(
                    self.level, 0, [x, y], self.DIR_UP, self.images['player2']
                )

                players.append(player)

        for player in players:
            player.level = self.level
            self.respawnPlayer(player, True)

    def showScores(self):

        global screen, players
        self.running = False
        screen.fill([0, 0, 0])

        hiscore = self.loadHiscore()
        self.saveHiscore(players[0].score)
        if self.nr_of_players == 2:
            self.saveHiscore(players[1].score)

        screen.blit(pygame.font.Font(None, 50).render("Топ-скор", False, (127, 64, 64)), [105, 35])
        screen.blit(pygame.font.Font(None, 50).render(str(max(hiscore)), False, (191, 160, 128)), [295, 35])

        screen.blit(pygame.font.Font(None, 50).render("Уровень" + str(self.stage).rjust(3), False, (255, 255, 255)),
                    [170, 65])

        screen.blit(pygame.font.Font(None, 50).render("Игрок 1", False, (127, 64, 64)), [25, 95])
        screen.blit(pygame.font.Font(None, 50).render(str(players[0].score).rjust(8), False, (191, 160, 128)),
                    [25, 125])

        if self.nr_of_players == 2:
            screen.blit(pygame.font.Font(None, 50).render("Игрок 2", False, (127, 64, 64)), [310, 95])
            screen.blit(pygame.font.Font(None, 50).render(str(players[1].score).rjust(8), False, (191, 160, 128)),
                        [325, 125])

        pygame.display.flip()
        self.clock.tick(2)
        interval = 5
        for i in range(4):
            tanks = players[0].trophies["enemy" + str(i)]

            for n in range(tanks + 1):
                screen.blit(pygame.font.Font(None, 50).render(str(n - 1).rjust(2), False, (0, 0, 0)),
                            [170, 168 + (i * 45)])
                screen.blit(pygame.font.Font(None, 50).render(str(n).rjust(2), False, (255, 255, 255)),
                            [170, 168 + (i * 45)])
                screen.blit(
                    pygame.font.Font(None, 50).render(str((n - 1) * (i + 1) * 100).rjust(4) + " Очки", False, (0, 0, 0)),
                    [25, 168 + (i * 45)])
                screen.blit(
                    pygame.font.Font(None, 50).render(str(n * (i + 1) * 100).rjust(4) + " Очки", False,
                                                      (255, 255, 255)),
                    [25, 168 + (i * 45)])
                pygame.display.flip()
                self.clock.tick(interval)

            if self.nr_of_players == 2:
                tanks = players[1].trophies["enemy" + str(i)]

                for n in range(tanks + 1):
                    screen.blit(pygame.font.Font(None, 50).render(str(n - 1).rjust(2), False, (0, 0, 0)),
                                [277, 168 + (i * 45)])
                    screen.blit(pygame.font.Font(None, 50).render(str(n).rjust(2), False, (255, 255, 255)),
                                [277, 168 + (i * 45)])

                    screen.blit(
                        pygame.font.Font(None, 50).render(str((n - 1) * (i + 1) * 100).rjust(4) + " Очки", False,
                                                          (0, 0, 0)),
                        [325, 168 + (i * 45)])
                    screen.blit(
                        pygame.font.Font(None, 50).render(str(n * (i + 1) * 100).rjust(4) + " Очки", False,
                                                          (255, 255, 255)),
                        [325, 168 + (i * 45)])

                    pygame.display.flip()
                    self.clock.tick(interval)

            self.clock.tick(interval)
        tanks = sum([i for i in players[0].trophies.values()])
        screen.blit(pygame.font.Font(None, 50).render(str(tanks).rjust(2), False, (255, 255, 255)), [170, 335])
        if self.nr_of_players == 2:
            tanks = sum([i for i in players[1].trophies.values()])
            screen.blit(pygame.font.Font(None, 50).render(str(tanks).rjust(2), False, (255, 255, 255)), [277, 335])

        pygame.display.flip()

        while 1:
            if self.paused:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        quit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            self.running = True
                            return False
            else:
                self.clock.tick(50)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        quit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            if self.game_over:
                                self.gameOverScreen()
                            else:
                                self.nextLevel()
                            return

    def draw(self):
        global screen, players, enemies, bullets

        screen.fill([0, 0, 0])

        self.level.draw([self.level.TILE_EMPTY, self.level.TILE_BRICK, self.level.TILE_STEEL, self.level.TILE_SAND,
                         self.level.TILE_WATER])

        for enemy in enemies:
            enemy.draw()

        for player in players:
            player.draw()

        for bullet in bullets:
            bullet.draw()

        self.level.draw([self.level.TILE_GRASS])

        self.drawSidebar()

        pygame.display.flip()

    def drawSidebar(self):

        global screen, players, enemies

        x = 416
        y = 0
        screen.fill([150, 150, 150], pygame.Rect([416, 0], [64, 416]))

        text = str(len(self.level.enemies_left) + len(enemies))
        screen.blit(pygame.font.Font(None, 50).render(text, 1, (0, 0, 0)), [x + 15, y + 40])
        screen.blit(self.images['enemy'], [x + 20, y + 5])

        if pygame.font.get_init():
            for n in range(len(players)):
                if n == 0:
                    screen.blit(pygame.font.Font(None, 50).render('P' + str(n + 1), False, (0, 0, 0)),
                                [x + 10, y + 150])
                    screen.blit(pygame.font.Font(None, 50).render('X' + str(players[n].lives), False, (0, 0, 0)),
                                [x + 10, y + 180])
                    screen.blit(self.images['player'], [x + 17, y + 215])
                else:
                    screen.blit(pygame.font.Font(None, 50).render('P' + str(n + 1), False, (0, 0, 0)),
                                [x + 10, y + 250])
                    screen.blit(pygame.font.Font(None, 50).render('X' + str(players[n].lives), False, (0, 0, 0)),
                                [x + 10, y + 280])
                    screen.blit(self.images['player2'], [x + 17, y + 315])

            screen.blit(pygame.font.Font(None, 50).render(str(self.stage), False, (0, 0, 0)), [x + 30, y + 380])

    def drawIntroScreen(self, put_on_surface=True):

        global screen

        screen.fill([0, 0, 0])

        hiscore = self.loadHiscore()

        screen.blit(pygame.font.Font(None, 50).render("Топ 5", 1, (100, 255, 100)), [200, 10])
        for i in range(5):
            screen.blit(pygame.font.Font(None, 40)
                        .render(str(i + 1) + ' ' + str(hiscore[i]), 1, (100, 255, 100)),
                        (165, i * 30 + 50))
        screen.blit(pygame.font.Font(None, 50).render("Танкисты", 1, (100, 255, 100)), (165, 210))

        screen.blit(pygame.font.Font(None, 40).render("1 игрок", 1, (100, 255, 100)), [185, 250])
        screen.blit(pygame.font.Font(None, 40).render("2 игрока", 1, (100, 255, 100)), [185, 280])

        if self.nr_of_players == 1:
            screen.blit(self.player_image, [155, 250])
        elif self.nr_of_players == 2:
            screen.blit(self.player_image, [155, 280])

        if put_on_surface:
            pygame.display.flip()

    def loadHiscore(self):
        f = open("scores.txt", "r")
        hiscore = list(map(int, f.read().splitlines()))

        return sorted(hiscore, reverse=True)[:5]

    def saveHiscore(self, hiscore):
        f = open("scores.txt", "a")
        f.write('\n' + str(hiscore))
        f.close()
        return True

    def finishLevel(self):

        self.active = False
        gtimer.add(3000, lambda: self.showScores(), 1)

    def nextLevel(self):

        global players, bullets
        pygame.mixer.music.load('music/default.mp3')
        pygame.mixer.music.play()

        del bullets[:]
        del enemies[:]
        del gtimer.timers[:]

        self.stage += 1
        self.level = Level(self.stage)
        self.timefreeze = False

        levels_enemies = (
            (18, 2, 0, 0), (14, 4, 0, 2), (14, 4, 0, 2), (2, 5, 10, 3), (8, 5, 5, 2),
            (9, 2, 7, 2), (7, 4, 6, 3), (7, 4, 7, 2), (6, 4, 7, 3), (12, 2, 4, 2),
            (5, 5, 4, 6), (0, 6, 8, 6), (0, 8, 8, 4), (0, 4, 10, 6), (0, 2, 10, 8),
            (16, 2, 0, 2), (8, 2, 8, 2), (2, 8, 6, 4), (4, 4, 4, 8), (2, 8, 2, 8),
            (6, 2, 8, 4), (6, 8, 2, 4), (0, 10, 4, 6), (10, 4, 4, 2), (0, 8, 2, 10),
            (4, 6, 4, 6), (2, 8, 2, 8), (15, 2, 2, 1), (0, 4, 10, 6), (4, 8, 4, 4),
            (3, 8, 3, 6), (6, 4, 2, 8), (4, 4, 4, 8), (0, 10, 4, 6), (0, 6, 4, 10)
        )

        if self.stage <= 21:
            enemies_l = levels_enemies[self.stage - 1]
        else:
            enemies_l = levels_enemies[20]

        self.level.enemies_left = [0] * enemies_l[0] + [1] * enemies_l[1] + [2] * enemies_l[2] + [3] * enemies_l[3]

        random.shuffle(self.level.enemies_left)
        self.reloadPlayers()
        gtimer.add(3000, lambda: self.spawnEnemy())
        self.game_over = False
        self.running = True
        self.active = True
        self.paused = False

        self.draw()

        while self.running:
            time_passed = self.clock.tick(50)
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pass
                elif event.type == pygame.QUIT:
                    quit()
                elif event.type == pygame.KEYDOWN and not self.game_over and self.active:
                    if event.key == pygame.K_q:
                        quit()
                    if event.key == pygame.K_ESCAPE:
                        self.paused = True

                        self.paused = self.showScores()
                    if event.key == pygame.K_u:
                        self.finishLevel()
                    for player in players:
                        if player.state == player.STATE_ALIVE:
                            try:
                                index = player.controls.index(event.key)
                            except:
                                pass
                            else:
                                if index == 0:
                                    player.fire()
                                elif index == 1:
                                    player.pressed[0] = True
                                elif index == 2:
                                    player.pressed[1] = True
                                elif index == 3:
                                    player.pressed[2] = True
                                elif index == 4:
                                    player.pressed[3] = True
                elif event.type == pygame.KEYUP and not self.game_over and self.active:
                    for player in players:
                        if player.state == player.STATE_ALIVE:
                            try:
                                index = player.controls.index(event.key)
                            except:
                                pass
                            else:
                                if index == 1:
                                    player.pressed[0] = False
                                elif index == 2:
                                    player.pressed[1] = False
                                elif index == 3:
                                    player.pressed[2] = False
                                elif index == 4:
                                    player.pressed[3] = False

            for player in players:
                if player.state == player.STATE_ALIVE and not self.game_over and self.active:
                    if player.pressed[0] == True:
                        player.move(self.DIR_UP);
                    elif player.pressed[1] == True:
                        player.move(self.DIR_RIGHT);
                    elif player.pressed[2] == True:
                        player.move(self.DIR_DOWN);
                    elif player.pressed[3] == True:
                        player.move(self.DIR_LEFT);
                player.update(time_passed)

            for enemy in enemies:
                if enemy.state == enemy.STATE_DEAD and not self.game_over and self.active:
                    enemies.remove(enemy)
                    if len(self.level.enemies_left) == 0 and len(enemies) == 0:
                        self.finishLevel()
                else:
                    enemy.update(time_passed)

            if not self.game_over and self.active:
                for player in players:
                    if player.state == player.STATE_ALIVE:
                        if player.bonus != None and player.side == player.SIDE_PLAYER:
                            player.bonus = None
                    elif player.state == player.STATE_DEAD:
                        self.superpowers = 0
                        player.lives -= 1
                        if player.lives > 0:
                            self.respawnPlayer(player)
                        else:
                            self.gameOver()

            for bullet in bullets:
                if bullet.state == bullet.STATE_REMOVED:
                    bullets.remove(bullet)
                else:
                    bullet.update()

            gtimer.update(time_passed)
            self.draw()


if __name__ == "__main__":
    gtimer = Timer()

    sprites = None
    screen = None
    players = []
    enemies = []
    bullets = []
    bonuses = []
    labels = []

    play_sounds = True
    sounds = {}

    game = Game()
    game.showMenu()
