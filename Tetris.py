import pygame.event
from pygame import quit
from pygame import image, init, font, display, Surface, time, KEYDOWN, K_p, QUIT, K_SPACE, K_RIGHT, K_LEFT, draw, key, \
    K_DOWN, KEYUP
from numpy import array, zeros, apply_along_axis, vstack, sin
from numpy.random import randint
import sqlite3 as lite
from os.path import join

# initialize
init()
font.init()

# images
pause = image.load(join('images', 'pause.jpg'))
menu = image.load(join('images','menu.jpg'))
task = image.load(join('images','task.jpg'))
failed = image.load(join('images','failed.jpg'))
_reward_1 = image.load(join('images','reward_1.jpg'))
_reward_2 = image.load(join('images','reward_2.jpg'))
_event = image.load(join('images','event.jpg'))


class Game():
    def __init__(self, level):
        self.bgTileColors = [[randint(6, 9) * 3 for _ in range(12)] for _ in range(20)]
        self.isPause = False
        self.win_height = 20 * 30
        self.win_width = 12 * 30 + 120
        self.win = display.set_mode((self.win_width, self.win_height))
        display.set_caption('Tetris')
        self.run = True
        self.isLose = False
        self.stage = 1
        self.FPS = 30
        self.level = level  # 1 ~ 30
        self.colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255), (255, 0, 255),
                       (255, 255, 255)]
        self.moveCount = 30
        self.init_movecount(self.level)
        self.pool = zeros((20 + 4, 12, 3), dtype='int')
        self.bricks = array([[(5, 1, 0), (5, 2, 0), (5, 3, 0), (6, 3, 0)],
                             [(6, 1, 1), (6, 2, 1), (6, 3, 1), (5, 3, 1)],
                             [(4, 2, 2), (5, 2, 2), (6, 2, 2), (7, 2, 2)],
                             [(5, 1, 3), (5, 2, 3), (6, 1, 3), (6, 2, 3)],
                             [(6, 1, 4), (6, 2, 4), (6, 3, 4), (5, 2, 4)],
                             [(5, 1, 5), (5, 2, 5), (6, 2, 5), (6, 3, 5)],
                             [(5, 2, 6), (5, 3, 6), (6, 1, 6), (6, 2, 6)]], dtype='int')  # shape = (7, 4, 3)
        # element: [(x1, y1, colorInd), (x2, y2, colorInd), (x3, y3, colorInd), (x4, y4, colorInd)]
        self.bricksRoll = []
        self.init_roll()
        self.curBrick = self.bricksRoll[0]  # ndarray
        self.init_brick()
        self.isSpeedUp = False
        self.brickStatus = 0
        self.clock = time.Clock()
        self.bg = Surface(self.win.get_size()).convert()
        self.score = 0
        self.credits = []
        self.creditsRoll = [[], [], [], []]
        self.eliminatedRows = []
        self.flashCount = 12
        self.isIntask = False
        self.task = []
        self.INFO_task_Count = 0
        self.INFO_reward_1_Count = 0
        self.INFO_reward_2_Count = 0
        self.INFO_failed = 0
        self.INFO_task_pos = self.win_width
        self.INFO_reward_1_pos = self.win_width
        self.INFO_reward_2_pos = self.win_width
        self.INFO_failed_pos = self.win_width
        self.reward_1 = 0
        self.reward_2 = 0
        self.task_fill = 6.27
        self.levelUpCount = self.win_width
        self.taskOrd = 4
        self.taskFillCount = 30

        # smile event
        self.isInSmile = False
        self.smile_fill = 6.27
        self.INFO_smile_pos = self.win_width
        self.INFO_smile_Count = 0
        self.smileNum = 10

        self.set_speed(self.isSpeedUp)
        # main
        self.main()

    def init_movecount(self, level):
        self.moveCount = int(self.FPS * (31 - level) * 0.1 + 10)

    def set_speed(self, isSpeedUp):
        if isSpeedUp:
            self.speed = 100
        elif self.isInSmile:
            self.speed = 5
        else:
            self.speed = 1

    def init_roll(self):
        self.bricksRoll = [self.bricks[randint(7)] for _ in range(4)]

    def init_brick(self):
        for i in range(4):
            self.pool[self.curBrick[i, 1], self.curBrick[i, 0]] = self.colors[int(self.curBrick[i, 2])]

    def move_down(self):
        curPositions = self.curBrick[:, :2]
        nextBrick = self.curBrick + array([0, 1, 0])
        nextPositions = nextBrick[:, :2]
        tempPool = self.pool.copy()
        for i in range(4):
            tempPool[curPositions[i, 1], curPositions[i, 0]] = array([0, 0, 0])
        isHit = False
        for i in range(4):
            try:
                if list(tempPool[nextPositions[i, 1], nextPositions[i, 0]]) != [0, 0, 0]:
                    isHit = True
                    for j in range(4):
                        if curPositions[j, 1] < 4:
                            self.isLose = True
                            self.stage = 1
                            return
            except IndexError:
                isHit = True
        if isHit:
            self.eliminate()
            self.bricksRoll.pop(0)
            if self.isInSmile:
                # smile stop
                if self.smileNum > 0:
                    self.smileNum -= 1
                    self.bricksRoll = [self.bricks[3] for _ in range(4)]
                else:
                    self.isInSmile = False
                    self.smileNum = 10
                    self.bricksRoll.append(self.bricks[randint(len(self.bricks))])

            elif self.reward_1 > 0:
                self.bricksRoll.append(
                    self.bricks[2 if randint(self.reward_1 + 35) > 30 else randint(len(self.bricks))])
            else:
                self.bricksRoll.append(self.bricks[randint(len(self.bricks))])
            self.curBrick = self.bricksRoll[0]
            self.brickStatus = 0
        else:
            for i in range(4):
                self.pool[curPositions[i, 1], curPositions[i, 0]] = array((0, 0, 0))
            for i in range(4):
                self.pool[nextPositions[i, 1], nextPositions[i, 0]] = self.colors[nextBrick[i, 2]]
            self.curBrick = nextBrick

    def translate(self, key):
        if key == 'l':
            curPositions = self.curBrick[:, :2]
            tempPool = self.pool.copy()
            for i in range(4):
                tempPool[curPositions[i, 1], curPositions[i, 0]] = array([0, 0, 0])
            if apply_along_axis(min, 0, self.curBrick - array([1, 0, 0]))[0] >= 0:
                nextBrick = self.curBrick - array([1, 0, 0])
            else:
                return
            nextPositions = nextBrick[:, :2]
            for i in range(4):
                try:
                    if list(tempPool[nextPositions[i, 1], nextPositions[i, 0]]) != [0, 0, 0]:
                        return
                except IndexError:
                    return
            for i in range(4):
                self.pool[curPositions[i, 1], curPositions[i, 0]] = array((0, 0, 0))
            for i in range(4):
                self.pool[nextPositions[i, 1], nextPositions[i, 0]] = self.colors[nextBrick[i, 2]]
            self.curBrick = nextBrick
        elif key == 'r':
            curPositions = self.curBrick[:, :2]
            tempPool = self.pool.copy()
            for i in range(4):
                tempPool[curPositions[i, 1], curPositions[i, 0]] = array([0, 0, 0])
            if apply_along_axis(max, 0, self.curBrick + array([1, 0, 0]))[0] <= 11:
                nextBrick = self.curBrick + array([1, 0, 0])
            else:
                return
            nextPositions = nextBrick[:, :2]
            for i in range(4):
                try:
                    if list(tempPool[nextPositions[i, 1], nextPositions[i, 0]]) != [0, 0, 0]:
                        return
                except IndexError:
                    return
            for i in range(4):
                self.pool[curPositions[i, 1], curPositions[i, 0]] = array((0, 0, 0))
            for i in range(4):
                self.pool[nextPositions[i, 1], nextPositions[i, 0]] = self.colors[nextBrick[i, 2]]
            self.curBrick = nextBrick

    def transform(self):
        curPositions = self.curBrick[:, :2]
        tempPool = self.pool.copy()
        for i in range(4):
            tempPool[curPositions[i, 1], curPositions[i, 0]] = array([0, 0, 0])
        nextBrick = self.curBrick.copy()
        if self.curBrick[0, 2] == 0:
            if self.brickStatus == 0:
                nextBrick[0] = nextBrick[0] + array([1, 1, 0])
                nextBrick[1] = nextBrick[1] + array([0, 0, 0])
                nextBrick[2] = nextBrick[2] + array([-1, -1, 0])
                nextBrick[3] = nextBrick[3] + array([-2, 0, 0])
            elif self.brickStatus == 1:
                nextBrick[0] = nextBrick[0] + array([-1, 1, 0])
                nextBrick[1] = nextBrick[1] + array([0, 0, 0])
                nextBrick[2] = nextBrick[2] + array([1, -1, 0])
                nextBrick[3] = nextBrick[3] + array([0, -2, 0])
            elif self.brickStatus == 2:
                nextBrick[0] = nextBrick[0] + array([-1, -1, 0])
                nextBrick[1] = nextBrick[1] + array([0, 0, 0])
                nextBrick[2] = nextBrick[2] + array([1, 1, 0])
                nextBrick[3] = nextBrick[3] + array([2, 0, 0])
            elif self.brickStatus == 3:
                nextBrick[0] = nextBrick[0] + array([1, -1, 0])
                nextBrick[1] = nextBrick[1] + array([0, 0, 0])
                nextBrick[2] = nextBrick[2] + array([-1, 1, 0])
                nextBrick[3] = nextBrick[3] + array([0, 2, 0])
        elif self.curBrick[0, 2] == 1:
            if self.brickStatus == 0:
                nextBrick[0] = nextBrick[0] + array([0, 2, 0])
                nextBrick[1] = nextBrick[1] + array([-1, 1, 0])
                nextBrick[2] = nextBrick[2] + array([-2, 0, 0])
                nextBrick[3] = nextBrick[3] + array([-1, -1, 0])
            elif self.brickStatus == 1:
                nextBrick[0] = nextBrick[0] + array([-2, 0, 0])
                nextBrick[1] = nextBrick[1] + array([-1, -1, 0])
                nextBrick[2] = nextBrick[2] + array([0, -2, 0])
                nextBrick[3] = nextBrick[3] + array([1, -1, 0])
            elif self.brickStatus == 2:
                nextBrick[0] = nextBrick[0] + array([0, -1, 0])
                nextBrick[1] = nextBrick[1] + array([1, 0, 0])
                nextBrick[2] = nextBrick[2] + array([2, 1, 0])
                nextBrick[3] = nextBrick[3] + array([1, 2, 0])
            elif self.brickStatus == 3:
                nextBrick[0] = nextBrick[0] + array([2, -1, 0])
                nextBrick[1] = nextBrick[1] + array([1, 0, 0])
                nextBrick[2] = nextBrick[2] + array([0, 1, 0])
                nextBrick[3] = nextBrick[3] + array([-1, 0, 0])
        elif self.curBrick[0, 2] == 2:
            if self.brickStatus == 0:
                nextBrick[0] = nextBrick[0] + array([2, -2, 0])
                nextBrick[1] = nextBrick[1] + array([1, -1, 0])
                nextBrick[2] = nextBrick[2] + array([0, 0, 0])
                nextBrick[3] = nextBrick[3] + array([-1, 1, 0])
            elif self.brickStatus == 1:
                nextBrick[0] = nextBrick[0] + array([-2, 2, 0])
                nextBrick[1] = nextBrick[1] + array([-1, 1, 0])
                nextBrick[2] = nextBrick[2] + array([0, 0, 0])
                nextBrick[3] = nextBrick[3] + array([1, -1, 0])
            elif self.brickStatus == 2:
                self.brickStatus = 0
                nextBrick[0] = nextBrick[0] + array([2, -2, 0])
                nextBrick[1] = nextBrick[1] + array([1, -1, 0])
                nextBrick[2] = nextBrick[2] + array([0, 0, 0])
                nextBrick[3] = nextBrick[3] + array([-1, 1, 0])
            elif self.brickStatus == 3:
                nextBrick[0] = nextBrick[0] + array([-2, 2, 0])
                nextBrick[1] = nextBrick[1] + array([-1, 1, 0])
                nextBrick[2] = nextBrick[2] + array([0, 0, 0])
                nextBrick[3] = nextBrick[3] + array([1, -1, 0])
        elif self.curBrick[0, 2] == 3:
            return
        elif self.curBrick[0, 2] == 4:
            if self.brickStatus == 0:
                nextBrick[0] = nextBrick[0] + array([1, 1, 0])
                nextBrick[1] = nextBrick[1] + array([0, 0, 0])
                nextBrick[2] = nextBrick[2] + array([-1, -1, 0])
                nextBrick[3] = nextBrick[3] + array([1, -1, 0])
            elif self.brickStatus == 1:
                nextBrick[0] = nextBrick[0] + array([-1, 1, 0])
                nextBrick[1] = nextBrick[1] + array([0, 0, 0])
                nextBrick[2] = nextBrick[2] + array([1, -1, 0])
                nextBrick[3] = nextBrick[3] + array([1, 1, 0])
            elif self.brickStatus == 2:
                nextBrick[0] = nextBrick[0] + array([-1, -1, 0])
                nextBrick[1] = nextBrick[1] + array([0, 0, 0])
                nextBrick[2] = nextBrick[2] + array([1, 1, 0])
                nextBrick[3] = nextBrick[3] + array([-1, 1, 0])
            elif self.brickStatus == 3:
                nextBrick[0] = nextBrick[0] + array([1, -1, 0])
                nextBrick[1] = nextBrick[1] + array([0, 0, 0])
                nextBrick[2] = nextBrick[2] + array([-1, 1, 0])
                nextBrick[3] = nextBrick[3] + array([-1, -1, 0])
        elif self.curBrick[0, 2] == 5:
            if self.brickStatus == 0:
                nextBrick[0] = nextBrick[0] + array([2, 1, 0])
                nextBrick[1] = nextBrick[1] + array([1, 0, 0])
                nextBrick[2] = nextBrick[2] + array([0, 1, 0])
                nextBrick[3] = nextBrick[3] + array([-1, 0, 0])
            elif self.brickStatus == 1:
                nextBrick[0] = nextBrick[0] + array([-2, -1, 0])
                nextBrick[1] = nextBrick[1] + array([-1, 0, 0])
                nextBrick[2] = nextBrick[2] + array([0, -1, 0])
                nextBrick[3] = nextBrick[3] + array([1, 0, 0])
            elif self.brickStatus == 2:
                nextBrick[0] = nextBrick[0] + array([2, 1, 0])
                nextBrick[1] = nextBrick[1] + array([1, 0, 0])
                nextBrick[2] = nextBrick[2] + array([0, 1, 0])
                nextBrick[3] = nextBrick[3] + array([-1, 0, 0])
            elif self.brickStatus == 3:
                nextBrick[0] = nextBrick[0] + array([-2, -1, 0])
                nextBrick[1] = nextBrick[1] + array([-1, 0, 0])
                nextBrick[2] = nextBrick[2] + array([0, -1, 0])
                nextBrick[3] = nextBrick[3] + array([1, 0, 0])
        elif self.curBrick[0, 2] == 6:
            if self.brickStatus == 0:
                nextBrick[0] = nextBrick[0] + array([1, 0, 0])
                nextBrick[1] = nextBrick[1] + array([0, -1, 0])
                nextBrick[2] = nextBrick[2] + array([1, 2, 0])
                nextBrick[3] = nextBrick[3] + array([0, 1, 0])
            elif self.brickStatus == 1:
                nextBrick[0] = nextBrick[0] + array([-1, 0, 0])
                nextBrick[1] = nextBrick[1] + array([0, 1, 0])
                nextBrick[2] = nextBrick[2] + array([-1, -2, 0])
                nextBrick[3] = nextBrick[3] + array([0, -1, 0])
            elif self.brickStatus == 2:
                nextBrick[0] = nextBrick[0] + array([1, 0, 0])
                nextBrick[1] = nextBrick[1] + array([0, -1, 0])
                nextBrick[2] = nextBrick[2] + array([1, 2, 0])
                nextBrick[3] = nextBrick[3] + array([0, 1, 0])
            elif self.brickStatus == 3:
                nextBrick[0] = nextBrick[0] + array([-1, 0, 0])
                nextBrick[1] = nextBrick[1] + array([0, 1, 0])
                nextBrick[2] = nextBrick[2] + array([-1, -2, 0])
                nextBrick[3] = nextBrick[3] + array([0, -1, 0])
        nextPositions = nextBrick[:, :2]
        for i in range(4):
            if nextPositions[i, 0] < 0 or nextPositions[i, 0] > 11 or \
                    nextPositions[i, 1] < 0 or nextPositions[i, 1] > self.win_height // 30 + 3:
                return
            if list(tempPool[nextPositions[i, 1], nextPositions[i, 0]]) != [0, 0, 0]:
                return
        for i in range(4):
            self.pool[curPositions[i, 1], curPositions[i, 0]] = array((0, 0, 0))
        for i in range(4):
            self.pool[nextPositions[i, 1], nextPositions[i, 0]] = self.colors[nextBrick[i, 2]]
        self.curBrick = nextBrick
        self.brickStatus = (self.brickStatus + 1) % 4

    def calculate_score(self):
        self.creditsRoll.append(self.credits)
        self.credits = []
        self.creditsRoll.pop(0)
        sums = [0 for _ in range(len(self.creditsRoll))]
        for i in range(len(sums)):
            for credit in self.creditsRoll[i]:
                sums[i] += credit
        if sums[0] + sums[1] + sums[2] > 3000:
            self.score += int(sums[3] * (self.reward_2 / 10 + self.score // 10000 / 10 + 5))
            if sums[3] * 5 > 0 and randint(1) < 1:
                if randint(2) == 0:
                    if not self.isInSmile and not self.isIntask:
                        self._task(self.score, self.isIntask)
                else:
                    if not self.isInSmile and not self.isIntask:
                        self._smile(self.score, self.isInSmile)
        elif sums[0] + sums[1] + sums[2] > 1500:
            self.score += int(sums[3] * (self.reward_2 / 10 + self.score // 10000 / 10 + 3))
            if sums[3] * 3 > 0 and randint(2) < 1:
                if randint(2) == 0:
                    if not self.isInSmile and not self.isIntask:
                        self._task(self.score, self.isIntask)
                else:
                    if not self.isInSmile and not self.isIntask:
                        self._smile(self.score, self.isInSmile)
        elif sums[0] + sums[1] + sums[2] > 1000:
            self.score += int(sums[3] * (self.reward_2 / 10 + self.score // 10000 / 10 + 2))
            if sums[3] * 2 > 0 and randint(5) < 1:
                if randint(2) == 0:
                    if not self.isInSmile and not self.isIntask:
                        self._task(self.score, self.isIntask)
                else:
                    if not self.isInSmile and not self.isIntask:
                        self._smile(self.score, self.isInSmile)
        else:
            self.score += int(sums[3] * (self.reward_2 / 10 + self.score // 10000 / 10 + 1))
            if sums[3] > 0 and randint(10) < 1:
                if randint(2) == 0:
                    if not self.isInSmile and not self.isIntask:
                        self._task(self.score, self.isIntask)
                else:
                    if not self.isInSmile and not self.isIntask:
                        self._smile(self.score, self.isInSmile)

    def eliminate(self):
        for i in range(4, 21):
            fourRowsSum = sum(sum(apply_along_axis(max, -1, self.pool[i: i + 4, :]) / 255))
            if fourRowsSum == 48:
                self.credits.append(int(1000 * 1.1 ** (21 - i)))
                self.eliminatedRows.append((i, 4))
                temp = vstack([zeros((4, 12, 3), dtype='int32'), self.pool[4: i, :]])
                self.pool[i: i + 4, :] = array([0, 0, 0])
                time.delay(50)
                self.pool[4: i + 4, :] = temp
                return self.eliminate()
        for i in range(4, 22):
            threeRowsSum = sum(sum(apply_along_axis(max, -1, self.pool[i: i + 3, :]) / 255))
            if threeRowsSum == 36:
                self.credits.append(int(300 * 1.1 ** (22 - i)))
                self.eliminatedRows.append((i, 3))
                temp = vstack([zeros((3, 12, 3), dtype='int32'), self.pool[4: i, :]])
                self.pool[i: i + 3, :] = array([0, 0, 0])
                time.delay(50)
                self.pool[4: i + 3, :] = temp
                return self.eliminate()
        for i in range(4, 23):
            twoRowsSum = sum(sum(apply_along_axis(max, -1, self.pool[i: i + 2, :]) / 255))
            if twoRowsSum == 24:
                self.credits.append(int(150 * 1.1 ** (23 - i)))
                self.eliminatedRows.append((i, 2))
                temp = vstack([zeros((2, 12, 3), dtype='int32'), self.pool[4: i, :]])
                self.pool[i: i + 2, :] = array([0, 0, 0])
                time.delay(50)
                self.pool[4: i + 2, :] = temp
                return self.eliminate()
        for i in range(4, 24):
            oneRowsSum = sum(sum(apply_along_axis(max, -1, self.pool[i: i + 1, :]) / 255))
            if oneRowsSum == 12:
                self.credits.append(int(50 * 1.1 ** (24 - i)))
                self.eliminatedRows.append((i, 1))
                temp = vstack([zeros((1, 12, 3), dtype='int32'), self.pool[4: i, :]])
                self.pool[i: i + 1, :] = array([0, 0, 0])
                time.delay(50)
                self.pool[4: i + 1, :] = temp
                return self.eliminate()
        self.calculate_score()

    def pause(self, isPause):
        while isPause:
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == K_p:
                        isPause = False
            self.win.blit(pause, (0, 250))
            display.update()

    def init_game(self):
        self.init_movecount(self.level)
        self.level = 1
        self.set_speed(self.isSpeedUp)
        self.pool = zeros((20 + 4, 12, 3), dtype='int')
        self.bricks = array([[(5, 1, 0), (5, 2, 0), (5, 3, 0), (6, 3, 0)],
                             [(6, 1, 1), (6, 2, 1), (6, 3, 1), (5, 3, 1)],
                             [(4, 2, 2), (5, 2, 2), (6, 2, 2), (7, 2, 2)],
                             [(5, 1, 3), (5, 2, 3), (6, 1, 3), (6, 2, 3)],
                             [(6, 1, 4), (6, 2, 4), (6, 3, 4), (5, 2, 4)],
                             [(5, 1, 5), (5, 2, 5), (6, 2, 5), (6, 3, 5)],
                             [(5, 2, 6), (5, 3, 6), (6, 1, 6), (6, 2, 6)]], dtype='int')  # shape = (7, 4, 3)
        # element: [(x1, y1, colorInd), (x2, y2, colorInd), (x3, y3, colorInd), (x4, y4, colorInd)]
        self.bricksRoll = []
        self.init_roll()
        self.curBrick = self.bricksRoll[0]  # ndarray
        self.init_brick()
        self.brickStatus = 0
        self.score = 0
        self.flashCount = 12
        self.isIntask = False
        self.task = []
        self.INFO_task_Count = 0
        self.INFO_reward_1_Count = 0
        self.INFO_reward_2_Count = 0
        self.taskFillCount = 30
        self.reward_1 = 0
        self.reward_2 = 0
        self.levelUpCount = self.win_width
        self.taskOrd = 4
        self.isSpeedUp = False
        self.INFO_failed = 0
        self.INFO_task_pos = self.win_width
        self.INFO_reward_1_pos = self.win_width
        self.INFO_reward_2_pos = self.win_width
        self.INFO_failed_pos = self.win_width
        self.task_fill = 6.27
        # smile event
        self.isInSmile = False
        self.smile_fill = 6.27
        self.INFO_smile_pos = self.win_width
        self.INFO_smile_Count = 0
        self.smileNum = 10

    def menu(self, isLose):
        self.data = list(self.c.execute('SELECT * FROM leaderBoard '))
        if not isLose:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.run = False
                if event.type == KEYDOWN:
                    if event.key == K_SPACE:
                        self.init_game()
                        self.stage = 2

            myFont = font.SysFont('microsoftjhengheimicrosoftjhengheiuilight', 25, bold=True,
                                  italic=True)
            text_score1 = myFont.render(str(self.data[0][1]), True, (240, 240, 240))
            text_score2 = myFont.render(str(self.data[1][1]), True, (240, 240, 240))
            text_score3 = myFont.render(str(self.data[2][1]), True, (240, 240, 240))
            text_score4 = myFont.render(str(self.data[3][1]), True, (240, 240, 240))
            text_score5 = myFont.render(str(self.data[4][1]), True, (240, 240, 240))
            text_score6 = myFont.render(str(self.data[5][1]), True, (240, 240, 240))
            self.win.blit(menu, (0, 0))
            self.win.blit(text_score1, (110, 215))
            self.win.blit(text_score2, (110, 245))
            self.win.blit(text_score3, (110, 275))
            self.win.blit(text_score4, (110, 305))
            self.win.blit(text_score5, (110, 335))
            self.win.blit(text_score6, (110, 365))
            display.update()

        else:
            self.isLose = False
            score_ = [pair[1] for pair in self.data]
            score_.append(self.score)
            score_.sort(reverse=True)
            score_ = score_[:-1]
            for i in range(len(score_)):
                self.c.execute('UPDATE leaderBoard SET score = ? WHERE NO = ?', (score_[i], i + 1))
            self.conn.commit()

    def _task(self, score, isInTask):
        score = score
        isInTask = isInTask
        if not isInTask:
            if score >= 5000:
                self.isIntask = True
                self.INFO_task_Count = 90
                self.task = [randint(1, 5) for _ in range(3)]

    def _smile(self, score, isInSmile):
        score = score
        isInSmile = isInSmile
        if not isInSmile:
            if score >= 8000:
                self.isInSmile = True
                self.INFO_smile_Count = 90


    def main(self):
        global text_curTask
        self.conn = lite.connect('Tetris.db')
        self.c = self.conn.cursor()
        while self.run:
            if self.stage == 2:
                self.clock.tick(self.FPS)
                keys = key.get_pressed()
                for event in pygame.event.get():
                    if event.type == QUIT:
                        self.run = False
                    if event.type == KEYDOWN:
                        if event.key == K_SPACE:
                            self.transform()
                        if event.key == K_p:
                            self.isPause = True
                            self.pause(self.isPause)
                        if event.key == K_DOWN:
                            self.isSpeedUp = True
                            self.set_speed(self.isSpeedUp)
                    if event.type == KEYUP:
                        if event.key == K_DOWN:
                            self.isSpeedUp = False
                            self.set_speed(self.isSpeedUp)
                if keys[K_LEFT] and self.moveCount % 3 == 0:
                    self.translate('l')
                if keys[K_RIGHT] and self.moveCount % 3 == 0:
                    self.translate('r')
                if self.moveCount <= 0:
                    self.move_down()
                    self.init_movecount(self.level)
                else:
                    self.moveCount -= self.speed

                # tile bg
                if self.isIntask:
                    if self.task_fill > 0:
                        self.bg.fill((abs(sin(self.task_fill)) * 120, 10, 0))
                        self.task_fill -= 0.03
                    elif self.task_fill <= 0:
                        self.task_fill = 6.27
                else:
                    self.bg.fill((0, 0, 0))

                # tile smile
                if self.isInSmile:
                    smile_pixels = [(3, 6), (8, 6), (3, 10), (8, 10), (4, 11), (7, 11), (5, 12), (6, 12)]
                    if self.smile_fill > 0:
                        for pixel in smile_pixels:
                            draw.rect(self.bg,
                                      (abs(sin(self.smile_fill)) * 120, abs(sin(self.smile_fill)) * 120, 0),
                                      (pixel[0] * 30, pixel[1] * 30, 30, 30), 0)
                        self.smile_fill -= 0.03
                    elif self.smile_fill <= 0:
                        self.smile_fill = 6.27

                # tile bricks
                for i in range(12):
                    for j in range(self.win_height // 30):
                        if list(self.pool[j + 4, i]) == [0, 0, 0]:
                            draw.rect(self.bg,
                                      (self.bgTileColors[j][i], self.bgTileColors[j][i], self.bgTileColors[j][i]),
                                      (i * 30 + 1, j * 30 + 1, 28, 28), 0)
                        else:
                            draw.rect(self.bg, list(self.pool[j + 4, i]), (i * 30 + 1, j * 30 + 1, 28, 28), 0)

                # gray board
                draw.rect(self.bg, (50, 50, 50), (12 * 30, 0, 124, 20 * 30), 0)
                draw.rect(self.bg, (150, 150, 100), (0, 0, 12 * 30, 20 * 30), 5)
                # holding box
                if not self.isIntask:
                    for i in range(4):
                        if self.curBrick[i, 2] == 3:
                            draw.rect(self.bg, list(array(self.colors)[self.bricks[self.curBrick[i, 2], 0, 2]]),
                                      (self.win_width - 180 + self.bricks[self.curBrick[i, 2], i, 0] * 20 + 1,
                                       90 + self.bricks[self.curBrick[i, 2], i, 1] * 20 + 1, 18, 18), 0)
                        else:
                            draw.rect(self.bg, list(array(self.colors)[self.bricks[self.curBrick[i, 2], 0, 2]]),
                                      (self.win_width - 180 + self.bricks[self.curBrick[i, 2], i, 0] * 20 + 1,
                                       80 + self.bricks[self.curBrick[i, 2], i, 1] * 20 + 1, 18, 18), 0)
                    draw.rect(self.bg, (30, 30, 30), (self.win_width - 108, 82, 90, 90), 3)
                    draw.rect(self.bg, (80, 80, 80), (self.win_width - 106, 84, 90, 90), 4)

                    myFont = font.SysFont('microsoftjhengheimicrosoftjhengheiuilight', 23, bold=True, italic=True)
                    text_hold = myFont.render('HOLD', True, (120, 120, 120))
                else:
                    draw.rect(self.bg, (30, 30, 30), (self.win_width - 108, 82, 90, 90), 3)
                    draw.rect(self.bg, (80, 80, 80), (self.win_width - 106, 84, 90, 90), 4)
                    myFont = font.SysFont('microsoftjhengheimicrosoftjhengheiuilight', 23, bold=True, italic=True)
                    myFont2 = font.SysFont('microsoftjhengheimicrosoftjhengheiuilight', 50, bold=True, italic=False)
                    if len(self.task) > 0:
                        text_curTask = myFont2.render(str(self.task[0]), True, (220, 220, 220))
                    text_hold = myFont.render(' TASK', True, (120, 120, 120))

                # next box
                for k in range(1, 4):
                    for i in range(4):
                        if self.bricksRoll[k][i, 2] == 3:
                            draw.rect(self.bg,
                                      list(array(self.colors)[self.bricks[self.bricksRoll[k][i, 2], 0, 2]]),
                                      (self.win_width - 180 + self.bricks[self.bricksRoll[k][i, 2], i, 0] * 20 + 1,
                                       145 + 80 * k + self.bricks[self.bricksRoll[k][i, 2], i, 1] * 20 + 1, 18, 18),
                                      0)
                        else:
                            draw.rect(self.bg,
                                      list(array(self.colors)[self.bricks[self.bricksRoll[k][i, 2], 0, 2]]),
                                      (self.win_width - 180 + self.bricks[self.bricksRoll[k][i, 2], i, 0] * 20 + 1,
                                       140 + 80 * k + self.bricks[self.bricksRoll[k][i, 2], i, 1] * 20 + 1, 18, 18),
                                      0)
                draw.rect(self.bg, (30, 30, 30), (self.win_width - 108, 222, 90, 250), 3)
                draw.rect(self.bg, (80, 80, 80), (self.win_width - 106, 224, 90, 250), 4)
                draw.rect(self.bg, (150, 150, 100), (0, 0, 12 * 30, 20 * 30), 5)
                myFont = font.SysFont('microsoftjhengheimicrosoftjhengheiuilight', 23, bold=True, italic=True)
                text_next = myFont.render('NEXT', True, (120, 120, 120))

                # score box
                myFont = font.SysFont('microsoftjhengheimicrosoftjhengheiuilight', 23, bold=True, italic=True)
                text_scoreTitle = myFont.render('SCORE', True, (120, 120, 120))
                text_score = myFont.render(str(self.score), True, (240, 240, 240))


                # eliminate flash
                if len(self.eliminatedRows) != 0:
                    for i, rows in self.eliminatedRows:
                        draw.rect(self.bg,
                                  [(self.flashCount // 4 % 2 + 2) * 40, (self.flashCount // 4 % 2 + 2) * 40,
                                   (self.flashCount // 4 % 2 + 2) * 20],
                                  (0, (i - 4) * 30, 12 * 30, rows * 30), 0)
                    # task
                    if self.isIntask and len(self.task) > 0:
                        if len(self.task) == self.taskOrd:
                            _sum = 0
                            for i, rows in self.eliminatedRows:
                                _sum += rows
                                if _sum == self.task[0]:
                                    self.task.pop(0)
                                else:
                                    self.isIntask = False
                                    self.taskOrd = 4
                                    self.INFO_failed = 90

                    elif self.isIntask and len(self.task) == 0:
                        self.isIntask = False
                        self.taskOrd = 4
                        reward_type = randint(1, 3)
                        if reward_type == 1:
                            self.INFO_reward_1_Count = 90
                            self.reward_1 += 1
                        elif reward_type == 2:
                            self.INFO_reward_2_Count = 90
                            self.reward_2 += 1

                    self.flashCount -= 2

                if self.flashCount <= 0:
                    self.flashCount = 12
                    self.eliminatedRows = []
                    if self.isIntask:
                        self.taskOrd -= 1

                # blit
                if self.flashCount > 0:
                    self.win.blit(self.bg, ((-1) ** (self.flashCount // 4 % 2), 0))
                else:
                    self.win.blit(self.bg, (0, 0))
                if self.isIntask:
                    self.win.blit(text_curTask, (self.win_width - 78, 94))
                self.win.blit(text_hold, (self.win_width - 98, 50))
                self.win.blit(text_next, (self.win_width - 94, 190))
                self.win.blit(text_scoreTitle, (self.win_width - 103, 490))
                self.win.blit(text_score, (self.win_width - 96, 520))

                # challenge mode
                for i in range(1, 31):
                    if self.level == i and self.score >= 3000 * i:
                        if self.level <= 29:
                            if self.levelUpCount >= -self.win_width:
                                myFont = font.SysFont('microsoftjhengheimicrosoftjhengheiuilight', 45, bold=True,
                                                      italic=False)
                                random_color_g = randint(100, 255)
                                random_color_b = 255 - random_color_g
                                text_challengeMode = myFont.render('LEVEL %d' % (i + 1), False,
                                                                   (0, random_color_g, random_color_b))

                                self.win.blit(text_challengeMode, (-self.win_width + 2 * self.levelUpCount + 7,
                                                                   80 + randint(1) - randint(2)))
                                self.levelUpCount -= 5
                            else:
                                self.levelUpCount = self.win_width
                                self.level += 1
                                self.init_movecount(self.level)

                # INFO flash
                # smile event
                if self.INFO_smile_Count > 0:
                    if self.INFO_smile_Count >= 60:
                        self.INFO_smile_pos -= 0.0153 * (self.INFO_smile_Count - 60) ** 2
                    if 0 < self.INFO_smile_Count <= 30:
                        self.INFO_smile_pos += 0.0153 * (self.INFO_smile_Count - 30) ** 2
                        self.INFO_smile_pos = self.win_width
                    self.INFO_smile_Count -= 1
                    self.win.blit(_event, (self.INFO_smile_pos, 50))
                else:
                    self.INFO_smile_Count = 0
                    self.INFO_smile_pos = self.win_width

                # task
                if self.INFO_task_Count > 0:
                    if self.INFO_task_Count >= 60:
                        self.INFO_task_pos -= 0.0153 * (self.INFO_task_Count - 60) ** 2
                    if 0 < self.INFO_task_Count <= 30:
                        self.INFO_task_pos += 0.0153 * (self.INFO_task_Count - 30) ** 2
                        self.INFO_task_pos = self.win_width
                    self.INFO_task_Count -= 1
                    self.win.blit(task, (self.INFO_task_pos, 50))
                else:
                    self.INFO_task_Count = 0
                    self.INFO_task_pos = self.win_width

                # failed
                if self.INFO_failed > 0:
                    if self.INFO_failed >= 60:
                        self.INFO_failed_pos -= 0.0153 * (self.INFO_failed - 60) ** 2
                    if 0 < self.INFO_failed <= 30:
                        self.INFO_failed_pos += 0.0153 * (self.INFO_failed - 30) ** 2
                    self.INFO_failed -= 1
                    self.win.blit(failed, (self.INFO_failed_pos, 50))
                else:
                    self.INFO_failed = 0
                    self.INFO_failed_pos = self.win_width

                # reward_1
                if self.INFO_reward_1_Count > 0:
                    if self.INFO_reward_1_Count >= 60:
                        self.INFO_reward_1_pos -= 0.0153 * (self.INFO_reward_1_Count - 60) ** 2
                    if 0 < self.INFO_reward_1_Count <= 30:
                        self.INFO_reward_1_pos += 0.0153 * (self.INFO_reward_1_Count - 30) ** 2
                    self.INFO_reward_1_Count -= 1
                    self.win.blit(_reward_1, (self.INFO_reward_1_pos, 50))
                else:
                    self.INFO_reward_1_Count = 0
                    self.INFO_reward_1_pos = self.win_width

                # reward_2
                if self.INFO_reward_2_Count > 0:
                    if self.INFO_reward_2_Count >= 60:
                        self.INFO_reward_2_pos -= 0.0153 * (self.INFO_reward_2_Count - 60) ** 2
                    if 0 < self.INFO_reward_2_Count <= 30:
                        self.INFO_reward_2_pos += 0.0153 * (self.INFO_reward_2_Count - 30) ** 2
                        self.INFO_reward_2_pos = self.win_width
                    self.INFO_reward_2_Count -= 1
                    self.win.blit(_reward_2, (self.INFO_reward_2_pos, 50))
                else:
                    self.INFO_reward_2_Count = 0
                    self.INFO_reward_2_pos = self.win_width

                # update
                display.update()

            # menu
            if self.stage == 1:
                self.menu(self.isLose)

        self.conn.close()
        quit()


Game(1)  # 1~30
