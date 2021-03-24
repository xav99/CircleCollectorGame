import turtle
from tkinter import messagebox
import random
import time
import keyboard
import threading
from pynput import keyboard
from xml.dom import minidom
import xml.etree.cElementTree as ET

lock = threading.Lock()


class Player:
    """
    Create a new player (Turtle)
    """
    def __init__(self, colour="blue", shape="triangle", xpos=0, ypos=0, charSpeed=0, hidden=False):
        self.player = turtle.Turtle()
        self.player.color(colour)
        self.player.shape(shape)
        self.player.penup()  # Don't leave any traces when moving
        self.player.setposition(xpos, ypos)  # Player position
        self.charSpeed = charSpeed  # Amount of speed player has
        self.player.speed(self.charSpeed)  # Player speed
        self.playerMove = True  # Player movement
        self.lives = 3  # Player lives
        self.slowBubbles = 0
        self.MINSPEED = 1
        self.MAXSPEED = 7.4
        self.needsShowing = False   # for boss and slow bubble
        self.needsUnsticking = False
        self.dispNeedsUpdating = False
        if hidden:
            self.player.hideturtle()

    def turnLeft(self):
        """
        Turns player left 30 degrees
        """
        self.player.left(30)

    def turnRight(self):
        """
        Turns player right 30 degrees
        """
        self.player.right(30)

    def rotate(self):
        """
        Rotate player 180 degrees
        """
        self.player.forward(-3)  # less wall glitches
        self.player.left(180)

    def changeSpeed(self, amount, replace=False):
        """
        :param amount: Amount to increase or decrease the speed by/ Amount to change player speed to if replace
        is set to True
        :param replace: Replaces player speed to the specified amount if set to True

        Increases/Decreases speed by specified amount or changes the amount completely to the specified amount if replace
        is set to True
        """
        if not replace:
            self.charSpeed += amount
        else:
            self.charSpeed = amount

    def changeColour(self, colour):
        """
        :param colour: Colour to change player to
        Changes player colour
        """
        self.player.color(colour)

    def playerMoving(self):
        """
        Checks if player can move or not
        """
        if self.playerMove:
            self.player.forward(self.charSpeed)

    def enableMovement(self):
        """
        Allows player movement
        """
        self.playerMove = True

    def disableMovement(self):
        """
        Stops player movement
        """
        self.playerMove = False

    def getPos(self, co):
        """
        :param co: Which coordinate to receive
            options:(x, y, xy (returns both x and y) )

        Retrieve player position
        """
        if co == 'x':
            return self.player.pos()[0]
        elif co == 'y':
            return self.player.pos()[1]
        elif co == 'xy':
            return self.player.pos()

    def changePos(self, x, y):
        """
        :param x: x axis to move to
        :param y: y axis to move to
        Change player position
        """
        self.player.setpos(x, y)

    def chainMove(self):
        """
        Moves in a certain sequence (Used for boss battle after getting hit)
        """
        self.player.forward(-220)
        time.sleep(0.5)
        self.player.forward(220)

    def changeSize(self, x, y):
        """
        Change player size
        """
        self.player.turtlesize(x, y)

    def setLives(self, amount):
        """
        Set the amount of lives player has
        """
        self.lives = amount

    def keyboardThread(self, delay):
        """
        Deals with all keyboard related functions
        """
        time.sleep(delay)

        def on_press(key):
            if key == keyboard.Key.esc:
                self.disableMovement()
            if key == keyboard.Key.space:
                self.enableMovement()
            if key == keyboard.KeyCode(85):
                """
                If the player is stuck, it moves the player to a safe position (func stuckCheck in Class Game),
                sets lives to 3 and disables movement until re-enabled
                """
                self.needsUnsticking = True
                self.lives = 3
                self.disableMovement()
            if key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:  # Use a slow bubble which lowers player speed by 1
                if self.slowBubbles >= 1:
                    if self.charSpeed > self.MINSPEED:
                        self.slowBubbles -= 1
                        self.changeSpeed(-1)
                        self.dispNeedsUpdating = True
        listener = keyboard.Listener(on_press=on_press)
        listener.start()

    def hideTurtle(self):
        """
        Hides the player
        """
        self.player.hideturtle()

    def showTurtle(self):
        """
        Shows the player
        """
        self.player.showturtle()


class Game:
    """
    Game rules, initiation and management
    """
    def __init__(self):
        self.setup = turtle.Screen()  # setup screen
        self.setup.bgcolor("white")  # screen colour
        self.border()
        self.boundaryX = -322, 314  # x axis Boundary
        self.boundaryY = -264, 264  # y axis Boundary
        self.player1 = Player()
        self.player1.changeSpeed(1, True)
        self.pointsBubble = Player(xpos=random.randint(self.boundaryX[0], self.boundaryX[1]),
                                   ypos=random.randint(self.boundaryY[0], self.boundaryY[1]), shape="circle", colour="red")
        self.boss = Player(xpos=200, ypos=200, shape="circle", colour="black", hidden=True)
        self.boss.changeSize(4, 4)
        self.boss.setLives(7)
        self.slowBubble = Player(xpos=1000, ypos=1000, shape="circle", colour="pink")
        self.slowBubbleConfigured = False  # slow bubble visibility options
        self.bossConfigured = False  # Avoid constant spawning
        self.bossColourConfigured = False # Avoid constant colour spawning
        self.bossDazzed = False  # Allows boss to be hit by player
        self.points = 0

    def border(self):
        """
        Sets up the border/boundary lines
        """
        myborder = turtle.Turtle()  # Creates new character
        myborder.penup()
        myborder.speed(5)
        myborder.setposition(-335, -275)  # Sets character position to -335 by -275
        myborder.pendown()  # puts pendown and leaves a line marking in its trace
        myborder.pensize(3)  # Sets trace thickness to 3
        myborder.forward(660)
        myborder.left(90)
        myborder.forward(550)
        myborder.left(90)
        myborder.forward(660)
        myborder.left(90)
        myborder.forward(550)
        myborder.hideturtle()  # hides character

    def setPoints(self, points):
        """
        :param points: Amount of points
        Changes points to the specified amount
        """
        time.sleep(0.5)
        self.points = points
        self.player1.changeSpeed(0.2 * points/10)
        self.speedCap()

    def boundaryCheck(self):
        """
        Responsible for boundary collision
        Rotates player and removes a life if player hits the boundary
        """
        if self.player1.getPos('x') > 314 or self.player1.getPos('x') < -322:
            self.player1.rotate()
            self.player1.lives -= 1
            self.eraseSpecificText("lives")
            self.displayText(str(self.player1.lives), -303, -300)  # lives title
        if self.player1.getPos('y') > 264 or self.player1.getPos('y') < -264:
            self.player1.rotate()
            self.player1.lives -= 1
            self.eraseSpecificText("lives")
            self.displayText(str(self.player1.lives), -303, -300)  # lives title

    def stuckCheck(self):
        """
        Checks if player is stuck, and if it is stuck, moves player to a safe position
        """
        if self.player1.needsUnsticking:
            self.player1.changePos(self.boundaryX[0]/2 + self.boundaryX[1]/2, self.boundaryY[0]/2 + self.boundaryY[1]/2)
            self.eraseSpecificText("lives")
            self.displayText(str(self.player1.lives), -303, -300)  # lives title
            self.player1.needsUnsticking = False

    def speedCap(self):
        """
        Speed boundary which doesn't let the player exceed MAXSPEED (7.4) or fall under MINSPEED (1)
        """
        if round(self.player1.charSpeed, 2) >= self.player1.MAXSPEED:
            self.player1.changeSpeed(self.player1.MAXSPEED, True)
        if round(self.player1.charSpeed, 2) <= self.player1.MINSPEED:
            self.player1.changeSpeed(self.player1.MINSPEED, True)

    def livesValidation(self):
        """
        Prompts the user with a messageBox when lives hit 0
            :messageBox options:
                retry: Restarts the game
                abort: Exits the game
                ignore: Allows configuration options to be made (Keys:
                                                                     "U" - [Places player in a safe position,
                                                                            Sets lives to 3,
                                                                            Disables movement]
                                                                     "ESC" - [Disables movement]
                                                                     "SPACE" - [Enables Movement] )
                        should be used if an unfair:exception occurs
                       unfair:exception is in reference with an unfair ending, such as a glitch occurrence,
                        or something in relation of that nature
        """

        if self.player1.lives <= 0:
            self.player1.disableMovement()
            self.player1.changePos(2000, 2000)
            endingNoticeResponse=(messagebox.showinfo("Game Over", "You have ended with " + str(self.points) + " points",
                                  type="abortretryignore"))
            if endingNoticeResponse == "retry":
                self.sendHighScore()
                self.setup.clearscreen()
                import run  # Used for replay button
                x = run.runGame()
                #x = run
            elif endingNoticeResponse == "abort":
                self.setup.bye()
                self.sendHighScore()
            elif endingNoticeResponse == "ignore":
                self.player1.lives = 10000

    def displayText(self, text, x, y, colour="black"):
        """
        :param text: Text to write
        :param x: x axis to place text
        :param y: y axis to place text
        :param colour: Text colour
        Write text on screen
        """
        Text = turtle.Turtle()
        Text.penup()
        Text.hideturtle()
        Text.setposition(x, y)
        if colour != "black":
            Text.color(colour)
        Text.write(text)

    def eraseText(self, x, y, eraseAmount=15):
        """
        :param x: Location x axis of text to erase
        :param y: Location y axis of text to erase
        :param eraseAmount: Length in pixels of how much text to erase
        Erase text
        """
        turtle.hideturtle()
        turtle.penup()
        turtle.setpos(x, y)
        turtle.pendown()
        turtle.speed(10)
        turtle.color(turtle.bgcolor())
        turtle.pensize(25)
        turtle.begin_fill()
        turtle.fd(eraseAmount)

    def eraseSpecificText(self, title):
        """
        Erase text values easily based on their title
        :param title: Which text value to erase (points, lives, speed, slowbubble)
        """
        if title == "points":
            self.eraseText(-293, 293, 20)  # erase points
        elif title == "lives":
            self.eraseText(-295, -298, 20)  # erase lives
        elif title == "speed":
            self.eraseText(34, 293, 20)  # erase speed
        elif title == "slowbubble":
            self.eraseText(340, -297, 20)  # erase speed

    def pointsBubbleCollision(self):
        """
        Sets up collision between pointsBubble and Player
        """
        if self.pointsBubble.getPos('x') - 15 <= self.player1.getPos('x') <= self.pointsBubble.getPos('x') + 15\
                and self.pointsBubble.getPos('y') - 15 <= self.player1.getPos('y') <= self.pointsBubble.getPos('y') + 15:
            self.pointsBubble.changePos(random.randint(self.boundaryX[0], self.boundaryX[1]),
                                        random.randint(self.boundaryY[0], self.boundaryY[1]))
            self.points += 10
            self.player1.changeSpeed(0.2)
            self.eraseSpecificText("points")

            if self.player1.lives < 3:  # Lives reset to 3 when you hit pointsBubble
                self.player1.lives = 3
                self.eraseSpecificText("lives")
                self.displayText(str(self.player1.lives), -303, -300)  # lives title

            if round(self.player1.charSpeed, 2) <= self.player1.MAXSPEED:  # If player at max speed, text stays same
                self.eraseSpecificText("speed")
            self.displayText(self.points, -290, 290)
            if round(self.player1.charSpeed, 2) <= self.player1.MAXSPEED:  # If player at max speed, text stays same
                self.displayText("%.1f" % self.player1.charSpeed, 30, 290)

    def bossSpawn(self):
        """
        Makes boss visible when points hit 100, and changes colours between black (not dazzed) and gold (dazzed)
        """
        if self.points == 100:
            if not self.bossConfigured:
                self.boss.showTurtle()
        if self.points >= 100:
            if self.bossDazzed:
                if not self.bossColourConfigured:
                    self.boss.changeColour("Gold")
                    self.bossColourConfigured = True
            else:
                if not self.bossColourConfigured:
                    self.boss.changeColour("Black")
                    self.bossColourConfigured = True
            self.bossConfigured = True
            self.bossState()
            self.bossCollision()

    def bossCollision(self):
        """
        Sets up collision between player and boss and defines the rules of boss
        """
        if self.boss.getPos('x') - 40 <= self.pointsBubble.getPos('x') <= self.boss.getPos('x') + 40 \
                and self.boss.getPos('y') - 40 <= self.pointsBubble.getPos('y') <= self.boss.getPos('y') + 40:  # if points bubble collides with boss
            self.pointsBubble.changePos(random.randint(self.boundaryX[0], self.boundaryX[1]),
                                        random.randint(self.boundaryY[0], self.boundaryY[1]))

        if self.boss.getPos('x') - 40 <= self.player1.getPos('x') <= self.boss.getPos('x') + 40 \
                and self.boss.getPos('y') - 40 <= self.player1.getPos('y') <= self.boss.getPos('y') + 40:
            if self.bossDazzed:
                self.boss.lives -= 1
                self.boss.chainMove()
                time.sleep(0.5)
                self.player1.changePos(self.boundaryX[0] / 2 + self.boundaryX[1] / 2,
                                       self.boundaryY[0] / 2 + self.boundaryY[1] / 2)
                self.bossColourConfigured = False
                if self.boss.lives >= 1:
                    self.player1.changeSpeed(-0.8)
                    self.points += 25
                else:
                    self.player1.changeSpeed(-1.6)
                    self.points += 250
                    self.boss.changePos(4000, 4000)
                self.eraseSpecificText("points")
                self.eraseSpecificText("speed")
                self.displayText(self.points, -290, 290)
                self.displayText("%.1f" % self.player1.charSpeed, 30, 290)
                self.bossDazzed = False
            else:
                self.player1.lives -= 5

    def bossState(self):
        """
        Changes boss dazzed state at the appropriate point range
        """
        if self.points == 150:
            self.bossDazzed = True
            self.bossColourConfigured = False
        elif self.points == 205:
            self.bossDazzed = True
            self.bossColourConfigured = False
        elif self.points == 300:
            self.bossDazzed = True
            self.bossColourConfigured = False
        elif self.points == 375:
            self.bossDazzed = True
            self.bossColourConfigured = False
        elif self.points == 450:
            self.bossDazzed = True
            self.bossColourConfigured = False
        elif self.points == 555:
            self.bossDazzed = True
            self.bossColourConfigured = False
        elif self.points == 620:
            self.bossDazzed = True
            self.bossColourConfigured = False
        elif self.points > 620 and self.boss.lives > 1:  # If points were gathered without attacking the boss in dazzed state
            if self.points % 50 == 0:
                self.bossDazzed = True
                self.bossColourConfigured = False

    def slowBubbleSpawn(self):
        """
        Spawns the slow bubble every x amount of points and handles the collision
        """
        if self.points >= 560:
            if self.points % 80 == 0 and not self.slowBubbleConfigured:
                self.slowBubble.needsShowing = True
                self.slowBubbleConfigured = True
            if self.slowBubble.getPos('x') - 15 <= self.player1.getPos('x') <= self.slowBubble.getPos('x') + 15 \
                    and self.slowBubble.getPos('y') - 15 <= self.player1.getPos('y') <= self.slowBubble.getPos(
                'y') + 15:
                self.player1.slowBubbles += 1
                self.slowBubble.changePos(1000, 1000)
                self.points += 10
                self.eraseSpecificText("points")
                self.eraseSpecificText("slowbubble")
                self.displayText(self.points, -290, 290)
                self.displayText(str(self.player1.slowBubbles), 335, -300)  # slow bubbles title
                self.slowBubbleConfigured = False

    def slowBubbleVisibility(self):
        """
        Makes the slow bubble visible
        """
        if self.slowBubble.needsShowing:
            self.slowBubble.changePos(random.randint(self.boundaryX[0], self.boundaryX[1]),
                                      random.randint(self.boundaryY[0], self.boundaryY[1]))
            self.slowBubble.needsShowing = False

    def forceDisplayUpdate(self):
        """
        Forces display to update
        """
        if self.player1.dispNeedsUpdating:
            self.eraseSpecificText("speed")
            self.eraseSpecificText("slowbubble")
            self.displayText("%.1f" % self.player1.charSpeed, 30, 290)
            self.displayText(str(self.player1.slowBubbles), 335, -300)  # slow bubbles title
            self.player1.dispNeedsUpdating = False

    def sendHighScore(self):
        """
        Sends the highscore data to xml file
        """
        if self.points > self.getHighScore()[1]:
            name = input("ENTER YOUR NAME: ")
            root = ET.Element("highscore")

            ET.SubElement(root, "name", text=name)
            ET.SubElement(root, "score", text=str(self.points))

            tree = ET.ElementTree(root)
            tree.write("score.xml")

    def getHighScore(self):
        """
        Gets the highscore, and the name of the user with the highscore
        """
        xmldoc = minidom.parse("score.xml")
        highscoreName = xmldoc.getElementsByTagName('name')
        highscoreValue = xmldoc.getElementsByTagName('score')
        highscoreName = highscoreName[0].attributes['text'].value
        highscoreValue = highscoreValue[0].attributes['text'].value
        return highscoreName, int(highscoreValue)

    def achievementColour(self):
        """
        Changes player colour based on high score
            Rewards:
                300- Green
                700- Purple
                1000- Orange
                1500- Gold
                3000- Diamond
        """
        if 300 < self.getHighScore()[1] < 700:
            self.player1.changeColour("green")
        elif 700 <= self.getHighScore()[1] < 1000:
            self.player1.changeColour("purple")
        elif 1000 <= self.getHighScore()[1] < 2000:
            self.player1.changeColour(("orange"))
        elif 1500 <= self.getHighScore()[1] < 3000:
            self.player1.changeColour("gold")
        elif self.getHighScore()[1] >= 3000:
            turtle.colormode(255)
            self.player1.changeColour((185, 242, 255))

    def gamePackage(self):
        """
        Includes all the important game functions in one function
        """
        self.setup.listen()
        self.setup.onkey(self.player1.turnLeft, "Left")
        self.setup.onkey(self.player1.turnRight, "Right")
        self.boundaryCheck()
        self.stuckCheck()
        self.speedCap()
        self.livesValidation()

    def extrasPackage(self):
        """
        Includes game features and less important game functions in one function
        """
        self.slowBubbleSpawn()
        self.pointsBubbleCollision()
        self.slowBubbleVisibility()
        self.bossSpawn()
        self.forceDisplayUpdate()

    def infoDisplay(self):
        """
        Displays in game information on screen
        """
        self.displayText("Points: " + str(self.points), -335, 290)  # Points title
        self.displayText("High Score: " + str(self.getHighScore()[0]) + ": " + str(self.getHighScore()[1]), 240, 290, colour="gold")  # High-score Title
        self.displayText("Current Speed: " + str(self.player1.charSpeed), -50, 290)  # speed title
        self.displayText("Lives: " + str(self.player1.lives), -335, -300)  # lives title
        self.displayText("Slow Bubbles: " + str(self.player1.slowBubbles), 260, -300)  # slow bubbles title

    def start(self):
        """
        Initiate the game
        """
        kbThread = threading.Thread(target=lambda: self.player1.keyboardThread(0))
        kbThread.daemon = True
        kbThread.start()
        kbThread.join()

        #self.setPoints(1320)  # MAX SPEED POINTS 320
        #self.player1.slowBubbles = 12
        self.infoDisplay()
        self.achievementColour()

        while 1:
            if self.player1.playerMove:
                self.player1.playerMoving()
            self.gamePackage()
            self.extrasPackage()
