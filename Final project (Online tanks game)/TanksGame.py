import pygame
import random
import os
import json
from threading import Thread
import uuid
import random
import pika
import sys
import time

#   Проектная работа: Игра "Танчики"
#   Автор: Хамраев Алим Рашидович, студент ФИТ, КБТУ
#
#
#   Навигация по коду:
#
#   -------------
#   Главное меню: - 87 строка
#   -------------
#   Главная функция - 92 строка
#   Класс кнопок - 127 строка
#
#
#   ----------------------
#   Оффлайн игра на двоих: - 159 строка
#   ----------------------
#   Классы танков, еды, стен -  168 строка
#
#   Главная функция работы оффлайн игры - 329 строка
#
#   Вспомогательные функции   
#   (проверка столкновений, еды и тд) - 464 строка
#
#
#   ---------------------------------
#   Мультиплеер (управляется игроком) - 585 строка
#   ---------------------------------
#   Классы RPC и consumer - 597 строка
#
#   Главная функция работы мультиплеера - 762 строка
#
#   Вспомогательные функции - 972 строка
#
#
#   ----------------------------
#   Мультиплеер (управляется AI) - 1070 строка
#   ----------------------------
#   (Класс RPC и consumer такие
#   же как для обычного мультиплеера) - 597 строка
#
#

pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.init()

display_width = 800
display_height = 600

display = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption('Tanks Game')

background_img = pygame.image.load("Icons/background.jpeg").convert()
tank1_img = pygame.image.load("Icons/tank1.jpeg").convert()
tank2_img = pygame.image.load("Icons/tank2.jpeg").convert()
ball_img = pygame.image.load("Icons/ball.jpeg").convert()
explosion_img = pygame.image.load("Icons/explosion.jpeg").convert()
wall_img = pygame.image.load("Icons/wall.jpeg").convert()

tank1_img.set_colorkey((0,0,0))
tank2_img.set_colorkey((0,0,0))
ball_img.set_colorkey((0,0,0))
explosion_img.set_colorkey((255,255,255))

clock = pygame.time.Clock()

direction1 = 1
direction2 = 1

tank_h = 30
tank_w = 30

#===============#=================#==================#
#
#      ГЛАВНОЕ МЕНЮ
#      Вызывает функции для запуска режимов игры или
#      дает возможность выйти из игры
#
#===============#=================#==================#

def show_menu():


    show = True

    single_mode_btn = Button(200, 30)
    multiplayer_mode_btn = Button(280, 30)
    AI_multiplayer_mode_btn = Button(310, 30)
    quit_btn = Button(100, 30)

    while show:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

        display.blit(background_img, (0,0))
        single_mode_btn.draw(display_width//2-100, display_height//2-100, 'Single game', start_single_game)
        multiplayer_mode_btn.draw(display_width//2-140, display_height//2-50, 'Multiplayer game', start_multiplayer_game)
        AI_multiplayer_mode_btn.draw(display_width//2-155, display_height//2, 'AI multiplayer game', start_AI_multiplayer_game)
        quit_game = quit_btn.draw(display_width//2-50, display_height//2+50, 'Quit', "True")

        if quit_game:
            return False

        pygame.draw.rect(display, (255, 0, 0),(display_width//2-235,display_height//2+150, 470, 25))
        
        print_text("Press ESC or QUIT to close the game", display_width//2-225,display_height//2+150, (255,255,255), 25)
        
        pygame.display.update()
        clock.tick(60)

#-----------------------------------------
# Класс для создания кнопок главного меню
#------------------------------------------
class Button():
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def draw(self, x, y, message, action):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        pygame.draw.rect(display, (0,0,255), (x, y, self.width, self.height))

        if (x < mouse[0] < x + self.width) and (y < mouse[1] < y + self.height):
            
            if click[0] == 1:
                if action is not None:
                    if action == quit:
                        pygame.quit()
                        quit()
                        return False
                    elif action == "True":
                        return True
                    else:
                        action()

        print_text(message, x+20, y, (255, 255, 255), 30)

        

#################################################################################
#################################################################################
#
#      ОФФЛАЙН ИГРА ДЛЯ ДВОИХ.
#
#      Классы для создания танков, стен, 
#      еды, а также их внутренние функции
#
#################################################################################
#################################################################################

#----------------------------------
# Класс создания танка и его функции
#----------------------------------
class Tank():
    global tank_h, tank_w, display_height, display_width

    def __init__(self, x, y, color, image):
        self.tank_x = x
        self.tank_y = y
        self.tank_color = color
        
        self.dx = 100
        self.dy = 100
        
        self.bullets = []
        self.bullets_num = 0

        self.make_shoot = False
        self.shooting = False

        self.bullet_x = -500
        self.bullet_x = -500

        self.cooldown = 0
        self.lifes = 3
        self.food = 0

        self.image = image
        self.direction = 1
        
    def moving(self, seconds):

        if (self.food > 0):
            self.dx = 200
            self.dy = 200
            self.food -= 1
        else:
            self.dx = 100
            self.dy = 100
            
        
        if self.direction == 1:
            self.dy = -self.dy
            self.dx = 0
            self.tank_y += self.dy * seconds
            if (self.tank_y < -tank_h):
                self.tank_y = display_height + tank_h
            rot = pygame.transform.rotate(self.image, 90)
            display.blit(rot,(self.tank_x, self.tank_y, tank_w, tank_h))

        if self.direction == 2:
            self.dy = self.dy
            self.dx = 0
            self.tank_y += self.dy * seconds
            if (self.tank_y - display_height) > tank_h:
                self.tank_y = -tank_h
            rot = pygame.transform.rotate(self.image, 270)
            display.blit(rot,(self.tank_x, self.tank_y, tank_w, tank_h))
            

        if self.direction == 3:
            self.dy = 0
            self.dx = self.dx
            self.tank_x += self.dx * seconds
            if (self.tank_x - display_width ) > tank_w:
                self.tank_x = -tank_w
            display.blit(self.image,(self.tank_x, self.tank_y, tank_w, tank_h))

        if self.direction == 4:
            self.dy = 0
            self.dx = -self.dx
            self.tank_x += self.dx * seconds
            if (self.tank_x < -tank_w):
                self.tank_x = display_width+tank_w
            flip = pygame.transform.flip(self.image, 1, 0)
            display.blit(flip,(self.tank_x, self.tank_y, tank_w, tank_h))

    def create_bullets(self):
        
        self.bullets_num = 0
        self.bullets.clear()

        self.bullet_x = self.tank_x + 10
        self.bullet_y = self.tank_y + 10
        
        for i in range (50):
            self.bullet_x += (self.dx)//5
            self.bullet_y += (self.dy)//5
            self.bullets.append(self.bullet_x)
            self.bullets.append(self.bullet_y)


        pygame.mixer.music.load('Sounds/shoot.mp3')
        pygame.mixer.music.play(0)
        
        self.make_shoot = False
        self.shooting = True

    def show_bullets(self):

        if self.bullets_num < 100:
            self.bullet_x = self.bullets[self.bullets_num]
            self.bullet_y = self.bullets[self.bullets_num+1]
            display.blit(ball_img,(self.bullet_x,self.bullet_y))
            self.bullets_num +=2
        else:
            self.bullet_x = -500
            self.bullet_y = -500
            self.bullets_num = 0
            self.bullets.clear()
            self.shooting = False



#----------------------------------
# Класс создания стен
#----------------------------------   
class Walls():
    def __init__(self):
        self.x = random.randint(0, display_width - 50)
        self.y = random.randint(100, display_height - 50)
        self.dx = 50
        self.dy = 50
        self.color = (0,0,255)

        self.image = wall_img

    def show_walls(self):
        display.blit(self.image,(self.x, self.y, self.dx, self.dy))



#----------------------------------
# Класс создания и управления едой
#----------------------------------
class Food():
    def __init__(self):
        self.x = random.randint(0, display_width - 50)
        self.y = random.randint(100, display_height - 50)
        self.dx = 10
        self.dy = 10
        self.color = (255,255,0)
        self.cooldown = 0
        
    def show_food(self):
        if (self.cooldown == 0):
            pygame.draw.rect(display, self.color, (self.x, self.y,self.dx, self.dy))
        elif (self.cooldown > 0):
            self.cooldown -= 1
            if (self.cooldown == 1):
                self.x = random.randint(0, display_width - 50)
                self.y = random.randint(100, display_height - 50)



#=============#================#================#===========#
#
#      ОФФЛАЙН ИГРА
#      Главная функция работы оффлайн игры
#      
#=============#================#================#===========#
  
def run_single_game():

    global direction1, direction2
    
    game = True

    milliseconds = clock.tick(60)
    seconds = milliseconds / 1000.0

    tank1 = Tank(100,100,(255,0,0), tank1_img)
    tank2 = Tank(display_width - 200, display_height - 200, (0,255,0), tank2_img)

    walls = [Walls(), Walls(), Walls()]
    food = Food()
       
    while game:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:            
                if event.key == pygame.K_ESCAPE:
                    return False
                
                if event.key == pygame.K_UP:
                    tank1.direction = 1
                elif event.key == pygame.K_DOWN:
                    tank1.direction = 2
                elif event.key == pygame.K_RIGHT:
                    tank1.direction = 3
                elif event.key == pygame.K_LEFT:
                    tank1.direction = 4
                    
                elif event.key == pygame.K_w:
                    tank2.direction = 1
                elif event.key == pygame.K_s:
                    tank2.direction = 2
                elif event.key == pygame.K_d:
                    tank2.direction = 3
                elif event.key == pygame.K_a:
                    tank2.direction = 4
                    
                elif event.key == pygame.K_RETURN:
                    tank1.make_shoot = True
                elif event.key == pygame.K_SPACE:
                    tank2.make_shoot = True


        # Отображение стен и еды (еда появляется в рандомное время,
        # это прописано в функциях)
        display.blit(background_img, (0,0))
    
        for wall in walls:
            wall.show_walls()

        food.show_food()

        
        # Изменение движения танка
        tank1.moving(seconds)
        tank2.moving(seconds)


        # Проверка съедания еды танком
        eating_food(tank1, food)
        eating_food(tank2, food)


        # Проверка столкновения со стеной либо танка, либо снаряда
        check_collision_with_wall(tank1, walls)
        check_collision_with_wall(tank2, walls)


        # Создание выстрела (то есть создание массива снарядов)
        if tank1.make_shoot:
            if (tank1.cooldown == 0):
                tank1.create_bullets()
                tank1.cooldown = 60
        if tank2.make_shoot:
            if (tank2.cooldown == 0):
                tank2.create_bullets()
                tank2.cooldown = 60

                
        # Кулдаун танка (сейчас установлено 60 фрэймов, то есть 1 секунда)
        if tank1.cooldown > 0:
            tank1.cooldown -= 1
        if tank2.cooldown > 0:
            tank2.cooldown -= 1

       
        # Отображение полета снаряда
        if tank1.shooting:
            tank1.show_bullets()
            check_collision(tank1, tank2)
        if tank2.shooting:
            tank2.show_bullets()
            check_collision(tank2, tank1)


        # Проверка количества жизней и вывод побеного сообщения
        if tank1.lifes == 0:
            pygame.draw.rect(display, (0,0,255),(display_width//2-360,display_height//2, 730, 30))
            print_text('Player 2 win. Press restart or quit to main menu',
                       display_width//2-350, display_height//2, (255,255,255), 30)
            game = False
        elif tank2.lifes == 0:
            pygame.draw.rect(display, (0,0,255), (display_width//2-360,display_height//2, 730, 30))
            print_text('Player 1 win. Press restart or quit to main menu',
                       display_width//2-350, display_height//2, (255,255,255), 30)
            game = False

            
        # Строки состояния такнов игроков (отображаются в углах экрана)
        print_text('Player 1, lifes: {}'.format(tank1.lifes),10, 10, (255, 0, 0), 22)
        print_text('Player 2, lifes: {}'.format(tank2.lifes),display_width-200, 10,(0, 255, 0), 22)

        print_text('Cooldown: {}'.format(int(tank1.cooldown/10)),10, 30, (255, 0, 0), 22)
        print_text('Cooldown: {}'.format(int(tank2.cooldown/10)),display_width-200, 30,(0, 255, 0), 22)

        
        pygame.display.update()
        clock.tick(60)


    # Когда кто-то победит, то эта функция промежуточного меню
    # дает возможность сыграть заново или выйти обратно в главное меню 
    return single_game_pause()





#===============#=================#==================#================#=============#
#
#      ОФФЛАЙН ИГРА
#      Вспомогательные функции проверок столкновений со стенами, попадания снарядов 
#      в вражеские танки, а также съедание еды (еда это желтые квадратики)
#
#===============#=================#==================#================#=============#

#---------------------------
# Проверка попадания снаряда
#---------------------------
def check_collision(tank_a, tank_b):

    
    if ((tank_a.bullet_x + 5 > tank_b.tank_x) and (tank_a.bullet_x + 5 < (tank_b.tank_x + 30)) and
        (tank_a.bullet_y + 5> tank_b.tank_y) and (tank_a.bullet_y + 5 < (tank_b.tank_y + 30))):

        pygame.mixer.music.load('Sounds/target.mp3')
        pygame.mixer.music.play(0)

        tank_b.lifes -=1
        tank_a.bullets_num = 200
        for i in range (100):
            display.blit(explosion_img, (tank_b.tank_x-10,tank_b.tank_y-10))        

#------------------------------------------
# Столкновение танка или снаряда со стеной
#------------------------------------------
def check_collision_with_wall(tank, walls):

    try:
        wall_delete = []
        for wall in walls:
            if ((tank.bullet_x + 5 > wall.x) and (tank.bullet_x + 5 < (wall.x + 50)) and
                (tank.bullet_y + 5 > wall.y) and (tank.bullet_y + 5 < (wall.y + 50))):

                tank.bullets_num = 100
                wall_delete.append(wall)

        for wall in wall_delete:
            walls.remove(wall)
            walls.append(Walls())
            
    finally:
        wall_delete = []
        for wall in walls:
            if ((wall.x - 30 < tank.tank_x) and (wall.x + 80 > (tank.tank_x + 30)) and
                (wall.y - 30 < tank.tank_y) and (wall.y + 80 > (tank.tank_y + 30))):
                tank.lifes -=1
                
                wall_delete.append(wall)

        for wall in wall_delete:
            walls.remove(wall)
            walls.append(Walls())

#--------------------
# Съедание еды
#--------------------
def eating_food(tank, food):

    if ((food.x - 30 < tank.tank_x) and (food.x + 40 > (tank.tank_x + 30)) and
        (food.y - 30 < tank.tank_y) and (food.y + 40 > (tank.tank_y + 30))):

        tank.food = 300

        food.cooldown = random.randint(200, 600)
        food.x = -500
        food.y = -500

#-----------------------------------------        
# Функция для отрисовки текста на экране       
#-----------------------------------------
def print_text(message,x, y, font_color, font_size):
    font_type = 'Fonts/PingPong.ttf'
    font_type = pygame.font.Font(font_type, font_size)
    text = font_type.render(message, True, font_color)
    display.blit(text, (x,y))

#------------------------------------------------------------------------
# Функция промежуточного меню при окончании однопользовательской игры
#------------------------------------------------------------------------
def single_game_pause():
    restart_singleplayer_btn = Button(220,30)
    quit_singleplayer_btn = Button(100,30)
    
    stopped = True
    while stopped:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_TAB]:
            return True
        if keys[pygame.K_ESCAPE]:
            return False

        restart = restart_singleplayer_btn.draw(display_width//2-110, display_height//2+100, 'Restart game', "True")
        quit_singleplayer = quit_singleplayer_btn.draw(display_width//2-50, display_height//2+150, 'Quit', "True")
        if restart:
            return True
        if quit_singleplayer:
            return False
        
        pygame.display.update()
        clock.tick(15)

#-----------------------------------------------------------
# Функция запуска однопользовательской игры
# вызывается нажатием кнокпи в главном меню
#-----------------------------------------------------------
def start_single_game():
    
    while run_single_game():
        pass





####################################################################################
####################################################################################
#
#      МУЛЬТИПЛЕЕР (управляемый игроком)
#      
####################################################################################
####################################################################################

IP = 'some ip'
PORT = 1234
LOGIN = VPORT = 'some login'
PASSWORD = 'some password'


#-------------------------------------------------------------        
# Класс создания RPC клиента, чтобы отправлять запросы серверу       
#-------------------------------------------------------------
class Tank_RPC_Client():

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host = IP,
                port = PORT,
                virtual_host = VPORT,
                credentials = pika.PlainCredentials(
                    username = LOGIN,
                    password = PASSWORD
                    )          
                )
            )

        self.channel = self.connection.channel()
        queue = self.channel.queue_declare(queue = '',
                                           auto_delete = True,
                                           exclusive = True)
        
        self.callback_queue = queue.method.queue
        self.channel.queue_bind(
            exchange = "X:routing.topic",
            queue = self.callback_queue
            )

        self.channel.basic_consume(
            queue = self.callback_queue,
            on_message_callback = self.on_response,
            auto_ack = True
            )

        self.response = None
        self.corr_id = None
        self.token = None
        self.tank_id = None
        self.room_id = None
        
    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = json.loads(body)
            print(self.response)
        
    def call(self, key, message={}):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        
        self.channel.basic_publish(
            exchange = 'X:routing.topic',
            routing_key = key,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
                ),
            body=json.dumps(message)
            )
        
        while self.response is None:
            self.connection.process_data_events()


    def server_status(self):
        self.call('tank.request.healthcheck')
        return self.response["status"] == '200'


    def register(self, room_id):
        message = {
            'roomId': room_id
            }
        self.call('tank.request.register', message)
        
        if self.response:
            self.token = self.response["token"]
            self.tank_id = self.response["tankId"]
            self.room_id = self.response["roomId"]
            return True
        
    def turn_tank(self, token, direction):
        message = {
            'token': token,
            'direction': direction
            }
        self.call('tank.request.turn', message)

    def make_shoot(self, token):
        message = {
            'token': token,
            }
        self.call('tank.request.fire', message)



#-------------------------------------------------------        
# Класс Consumer клиента для получения данных с сервера      
#-------------------------------------------------------
class Tank_Consumer_Client(Thread):

    def __init__(self, room_id):
        super().__init__()
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host = IP,
                port = PORT,
                virtual_host = VPORT,
                credentials = pika.PlainCredentials(
                    username = LOGIN,
                    password = PASSWORD
                    )          
                )
            )

        self.channel = self.connection.channel()
        queue = self.channel.queue_declare(queue = '',
                                           auto_delete = True,
                                           exclusive = True)

        event_listener = queue.method.queue
        self.channel.queue_bind(
            exchange = 'X:routing.topic',
            queue = event_listener,
            routing_key = 'event.state.'+room_id
            )

        self.channel.basic_consume(
            queue = event_listener,
            on_message_callback = self.on_response,
            auto_ack = True
            )

        self.response = None
        
    def on_response(self, ch, method, props, body):
        global new_data_from_server
        self.response = json.loads(body)
        
        # Если получил обновленные данные с сервера, то присваиваю true
        # переменной new_data_from_server, чтобы потом в функции игры отрисовывать
        # игровое поле по новым данным 
        new_data_from_server = True

    def run(self):
        self.channel.start_consuming()


#-----------------------------------------        
# Это нужно, чтобы легче было отправлять 
# нужные запросы серверу на поворот танка
#-----------------------------------------
UP = 'UP'
DOWN = 'DOWN'
RIGHT = 'RIGHT'
LEFT = 'LEFT'

MOVE_KEYS = {
    pygame.K_w: UP,
    pygame.K_s: DOWN,
    pygame.K_a: LEFT,
    pygame.K_d: RIGHT,
}

#=============#================#================#===========#
#
#      МУЛЬТИПЛЕЕР
#      Главная функция работы мультиплеера
#      
#=============#================#================#===========#
def run_multiplayer_game():
    global new_data_from_server
    
    game = True
    new_data_from_server = None
    
    # Регистрация танчика в незаполненной комнате
    client = Tank_RPC_Client()

    client.server_status()
    loading = True
    room_num = 1
    while loading:
        connection_status = client.register('room-'+str(room_num))
        if connection_status:
            loading = False
            event_client = Tank_Consumer_Client('room-'+str(room_num))
        else:
            room_num +=1
    event_client.start()

    
    # Начало игры
    while game:
        display.fill((0,0,0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game = False
                if event.key in MOVE_KEYS:
                    client.turn_tank(client.token, MOVE_KEYS[event.key])
                if event.key == pygame.K_SPACE:
                    client.make_shoot(client.token)
                    pygame.mixer.music.load('Sounds/shoot.mp3')
                    pygame.mixer.music.play(0)
        
        try:
            
            # Чтобы меньше зависало и цикл по несколько раз не рисовал одни и те же данные,
            # проверяю переменную, которая дает информацию о наличии новых данных с сервера.
            # Она меняет свое значение на True в функции on_response класса Tank_Consumer_Client

            if new_data_from_server:

                new_data_from_server = False
                
                # Обработка данных с сервера
                time = event_client.response['remainingTime']
                bullets = event_client.response['gameField']['bullets']
                tanks = event_client.response['gameField']['tanks']
                winners = event_client.response['winners']
                kicked = event_client.response['kicked']
                losers = event_client.response['losers']

                # Вывод результатов игры на экран (выиграл или проиграл)
                if len(winners) != 0:
                    for winner in winners:
                        if winner['tankId'] == client.tank_id:
                            print_text('You win! Score: {}'.format(winner['score']),
                                       display_width//2 - 120, display_height//2 - 100, (255,255,255), 30)
                            print_text('Press R or click "Restart" to play again',
                                       display_width//2 - 300, display_height//2 - 50, (255,255,255), 30)
                            game = False
                         
                if len(losers) != 0:
                    for lose in losers:
                        if lose['tankId'] == client.tank_id:
                            print_text('You lost. Score {}'.format(lose["score"]),
                                       display_width//2 - 120, display_height//2 - 100, (255,255,255), 30)
                            print_text('Press R or click "Restart" to play again',
                                       display_width//2 - 300, display_height//2 - 50, (255,255,255), 30)
                            game = False
                
                # Если буду кикнут, то выведется сообщение на экран
                if len(kicked) != 0:
                    for kick in kicked:
                        if kick['tankId'] == client.tank_id:
                            print_text('You were kicked from game. Score: {}'.format(kick['score']),
                                       display_width//2 - 270, display_height//2 - 100, (255,255,255), 30)
                            print_text('Press R or click "Restart" to play again',
                                       display_width//2 - 300, display_height//2 - 50, (255,255,255), 30)
                            game = False

                
                # Отрисовка каждого танка, а также запоминание score, health, id
                # чтобы потом создать таблицу рейтингов
                side_bar_info = []
                my_tank_in_game = False
                
                for tank in tanks:
                    draw_multiplayer_tank(client, **tank)
                    
                    side_bar_info.append({
                        "health":tank["health"],
                        "score":tank["score"],
                        "id":tank["id"],

                        # Создал свою дополнительную систему подсчета баллов
                        # 1 health = 0.5 балла, 1 score = 2 балла
                        # У всех получаются уникальные баллы
                        # В итоге можно быстро и легко сортировать таблицу рейтинга
                        # по тем условиям, которые написаны в документации DAR-tanks
                        "new_score_count": int(tank["score"])*2 + int(tank["health"])*0.5
                        })

                    # Это регулярная дополнительная проверка на наличие моего танка в игре
                    if tank["id"] == client.tank_id:
                        my_tank_in_game = True
                        my_tank_score = tank["score"]


                # Если моего танка нет в игре, а она еще идет, то проиграл
                # (сервер иногда зависает и не присылает нужные значения)
                if (my_tank_in_game == False) and (game == True):
                    print_text('You lost. Score {}'.format(my_tank_score),
                               display_width//2 - 120, display_height//2 - 100, (255,255,255), 30)
                    print_text('Press R or click "Restart" to play again',
                               display_width//2 - 300, display_height//2 - 50, (255,255,255), 30)
                    game = False    
                

                
                # Отрисовка снарядов  
                for bullet in bullets:
                    draw_multiplayer_bullets(client, **bullet)


                # Отрисовка бокового меню (рейтинг, время, комната)
                side_bar_info = sorted(side_bar_info, key=lambda i: i["new_score_count"], reverse=True)
                
                print_text('ID:', display_width - 190, 120, (255,255,255),15)
                print_text('Score:', display_width - 140, 120, (255,255,255), 15)
                print_text('Health:', display_width - 80, 120, (255,255,255), 15)
                
                table_player_y = 140
                
                for info_line in side_bar_info:
                    if str(info_line["id"]) == client.tank_id:
                        print_text("You", display_width - 195, table_player_y , (0,255,0), 15)
                    else:
                        print_text(str(info_line["id"]), display_width - 205, table_player_y , (255,0,0), 15)
                    print_text(str(info_line["score"]), display_width - 120, table_player_y , (255,255,255), 15)
                    print_text(str(info_line["health"]), display_width - 60, table_player_y , (255,255,255), 15)
                    table_player_y += 25

                print_text('Time: {}'.format(time), display_width - 165, 70, (255,255,255), 30)
                print_text('{}'.format(client.room_id), display_width - 140, 50, (255,255,255), 15)

                pygame.display.update()
                
            else:
                pass
            
        except:

            # Если в игре останется только мой танк или еще несколько других,
            # а время игры уже закончится, то автоматически выявится победитель
            # на основании рейтинговой таблицы счета и здоровья игроков
            # (Сервер почему-то в конце не присылает победителей, поэтому
            # реализовал эту функция у себя в коде)
            side_bar_info = sorted(side_bar_info, key=lambda i: i["new_score_count"], reverse=True)
            
            num = 1
            my_num = 0
            my_score = 0
            for side_line in side_bar_info:
                print(side_line)
                if side_line["id"] == client.tank_id:
                    my_score = side_line["score"]
                    if num == 1:
                        my_num = 1
                else:
                    num +=1

            # Если время закончилось, а есть еще живые танки
            # Вывод информации о победе или поражении на основании выявления победителя
            # Также показывается счет, набранный за всю игру 
            if (game == True) and my_num == 1:
                print_text('Time is out',
                           display_width//2 - 80, display_height//2 - 150, (255,255,255), 30)
                print_text('You win! Score: {}'.format(my_score),
                           display_width//2 - 120, display_height//2 - 100, (255,255,255), 30)
                print_text('Press R or click "Restart" to play again',
                           display_width//2 - 300, display_height//2 - 50, (255,255,255), 30)
                game = False
            else:
                print_text('Time is out',
                           display_width//2 - 80, display_height//2 - 150, (255,255,255), 30)
                print_text('You lost. Score: {}'.format(my_score),
                           display_width//2 - 120, display_height//2 - 100, (255,255,255), 30)
                print_text('Press R or click "Restart" to play again',
                           display_width//2 - 300, display_height//2 - 50, (255,255,255), 30)
                game = False

            pygame.display.update()
        
    # Функция промежуточного меню, дает возможность переиграть
    # или выйти в главное меню
    return game_multiplayer_pause()


#===============#=================#==================#================#=============#
#
#      МУЛЬТИПЛЕЕР
#      Вспомогательные функции отрисовки танков, снарядов, текста на экране
#      + функция промежуточного меню, что переиграть или выйти в главное меню
#
#===============#=================#==================#================#=============#


#-----------------------------------------        
# Функция для отрисовки текста на экране       
#-----------------------------------------
def print_text(message,x, y, font_color, font_size):
    font_type = 'Fonts/PingPong.ttf'
    font_type = pygame.font.Font(font_type, font_size)
    text = font_type.render(message, True, font_color)
    display.blit(text, (x,y))


#-----------------------------------------        
# Функция для отрисовки всех танков на экране     
#-----------------------------------------
def draw_multiplayer_tank(client, x, y, width, height, direction, id, **kwards):
    tank_c = (x + int(width/2), y + int(width/2))
    if id == client.tank_id:
        color = (0,255,0)
        if direction == "UP":
            rot_tank = pygame.transform.rotate(tank2_img, 90)
            display.blit(rot_tank, (x, y, width, width))
        elif direction == "LEFT":
            rot_tank = pygame.transform.rotate(tank2_img, 180)
            display.blit(rot_tank, (x, y, width, width))
        elif direction == "DOWN":
            rot_tank = pygame.transform.rotate(tank2_img, 270)
            display.blit(rot_tank, (x, y, width, width))
        else:
            display.blit(tank2_img, (x, y, width, width))
    else:
        # Так как сильно зависает, решил рисовать врагов как простые прямоугольники
        color = (255,0,0)
        pygame.draw.rect(display, color, (x, y, width, width))
        


#-----------------------------------------        
# Функция для отрисовки всех снарядов      
#-----------------------------------------
def draw_multiplayer_bullets(client, x, y, width, height, direction, owner, **kwards):
    if owner == client.tank_id:
        color = (0,255,0)
    else:
        color = (255,0,0)
    pygame.draw.rect(display, color, (x, y, width, height))


    
#-----------------------------------------        
# Функция промежуточного меню для мультиплеера
# Дает возможность переиграть, то есть заново регистрирует
# Или можно выйти на главное меню
#-----------------------------------------
def game_multiplayer_pause():
    restart_multiplayer_btn = Button(220, 30)
    quit_multiplayer_btn = Button(100, 30)
    
    stopped = True
    while stopped:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            return True
        if keys[pygame.K_ESCAPE]:
            return False
        
        restart = restart_multiplayer_btn.draw(display_width//2-110, display_height//2+100, 'Restart game', "True")
        quit_multiplayer = quit_multiplayer_btn.draw(display_width//2-50, display_height//2+150, 'Quit', "True")
        if restart:
            return True
        if quit_multiplayer:
            return False
        
        pygame.display.update()
        clock.tick(15)

#-----------------------------------------        
# Функция запуска мультиплеерной игры
# вызывается кнопкой в главном меню
#-----------------------------------------
def start_multiplayer_game():
    while run_multiplayer_game():
        pass


####################################################################################
####################################################################################
#
#      МУЛЬТИПЛЕЕР (Искуственный интеллект)
#
#      Главная функция игры с использованием ИИ, его логика и отрисовка игры в целом
#      Другие функции (отрисовка танков, пуль, промежуточного меню) такие же как и у
#      обычного мультиплеера, поэтому я их также использую
#      
####################################################################################
####################################################################################



def run_AI_multiplayer_game():
    global new_data_from_server
    
    game = True
    new_data_from_server = None
    
    # Регистрация танчика в незаполненной комнате
    client = Tank_RPC_Client()

    client.server_status()
    loading = True
    room_num = 1
    while loading:
        connection_status = client.register('room-'+str(room_num))
        if connection_status:
            loading = False
            event_client = Tank_Consumer_Client('room-'+str(room_num))
        else:
            room_num +=1
    event_client.start()

    not_to_be_afk = 0
    tank_cooldown = 0
    
    # Начало игры
    while game:
        display.fill((0,0,0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game = False
        
        try:
            
            # Чтобы меньше зависало и цикл по несколько раз не рисовал одни и те же данные,
            # проверяю переменную, которая дает информацию о наличии новых данных с сервера.
            # Она меняет свое значение на True в функции on_response класса Tank_Consumer_Client

            if new_data_from_server:

                new_data_from_server = False

                
                # Обработка данных с сервера
                time = event_client.response['remainingTime']
                bullets = event_client.response['gameField']['bullets']
                tanks = event_client.response['gameField']['tanks']
                winners = event_client.response['winners']
                kicked = event_client.response['kicked']
                losers = event_client.response['losers']


                # Вывод результатов игры на экран (выиграл или проиграл)
                if len(winners) != 0:
                    for winner in winners:
                        if winner['tankId'] == client.tank_id:
                            print_text('You win! Score: {}'.format(winner['score']),
                                       display_width//2 - 120, display_height//2 - 100, (255,255,255), 30)
                            print_text('Press R or click "Restart" to play again',
                                       display_width//2 - 300, display_height//2 - 50, (255,255,255), 30)
                            game = False
                         
                if len(losers) != 0:
                    for lose in losers:
                        if lose['tankId'] == client.tank_id:
                            print_text('You lost. Score {}'.format(lose["score"]),
                                       display_width//2 - 120, display_height//2 - 100, (255,255,255), 30)
                            print_text('Press R or click "Restart" to play again',
                                       display_width//2 - 300, display_height//2 - 50, (255,255,255), 30)
                            game = False
                
                # Если буду кикнут, то выведется сообщение на экран
                if len(kicked) != 0:
                    for kick in kicked:
                        if kick['tankId'] == client.tank_id:
                            print_text('You were kicked from game. Score: {}'.format(kick['score']),
                                       display_width//2 - 270, display_height//2 - 100, (255,255,255), 30)
                            print_text('Press R or click "Restart" to play again',
                                       display_width//2 - 300, display_height//2 - 50, (255,255,255), 30)
                            game = False

                
                # Отрисовка каждого танка, а также запоминание score, health, id
                # чтобы потом создать таблицу рейтингов
                side_bar_info = []
                my_tank_in_game = False

                # Это необходимые элементы для выстроения логики ИИ
                danger_directions = []
                my_current_x = 0
                my_current_y = 0
                my_current_direction = None
                
                for tank in tanks:
                    draw_multiplayer_tank(client, **tank)
                    
                    side_bar_info.append({
                        "health":tank["health"],
                        "score":tank["score"],
                        "id":tank["id"],

                        # Создал свою дополнительную систему подсчета баллов
                        # 1 health = 0.5 балла, 1 score = 2 балла
                        # У всех получаются уникальные баллы
                        # В итоге можно быстро и легко сортировать таблицу рейтинга
                        # по тем условиям, которые написаны в документации DAR-tanks
                        "new_score_count": int(tank["score"])*2 + int(tank["health"])*0.5
                        })


                    # Это регулярная дополнительная проверка на наличие моего танка в игре
                    if tank["id"] == client.tank_id:
                        my_tank_in_game = True
                        my_tank_score = tank["score"]

                        # Запоминаю мои текущие данные, чтобы на их основе ИИ принимал решения
                        my_current_x = tank["x"]
                        my_current_y = tank["y"]
                        my_current_direction = tank["direction"]


                # Если моего танка нет в игре, а она еще идет, то проиграл
                # (сервер иногда зависает и не присылает нужные значения)
                if (my_tank_in_game == False) and (game == True):
                    print_text('You lost. Score {}'.format(my_tank_score),
                               display_width//2 - 120, display_height//2 - 100, (255,255,255), 30)
                    print_text('Press R or click "Restart" to play again',
                               display_width//2 - 300, display_height//2 - 50, (255,255,255), 30)
                    game = False    


                # Анализ данных относительно танков врага и частичное принятие решений
                for tank in tanks:


                    # Если танк находится очень близко к моему танку, то чтобы избежать
                    # столкновения мой танк принимает решения о смене направления на безопасное
                    if ((tank["x"] >= my_current_x - 150) and (tank["x"] <= my_current_x + 150)
                          and (tank["y"] >= my_current_y - 150) and (tank["y"] <= my_current_y + 150)
                          and tank["id"] != client.tank_id):
                        
                        if (tank["x"] <= (my_current_x + 15)):
                            danger_directions.append("LEFT") 
                            
                        elif (tank["x"] >= (my_current_x + 16)):
                            danger_directions.append("RIGHT")
                                
                        if (tank["y"] <= (my_current_y + 15)):
                            danger_directions.append("UP")
                                
                        elif (tank["y"] >= (my_current_y + 16)):
                            danger_directions.append("DOWN")
                            
                        if (tank["direction"] == my_current_direction):
                            danger_directions.append(my_current_direction)

                            
                    # Если мой танк находит вражеский танк в "кресте", в котором он сам является центром,
                    # то он поворачивается в его сторону и производит выстрел
                    # Также учитывается время перезарядки для выстрела
                    else:    
                        if ((tank["y"]+31 >= my_current_y+20) and (tank["y"] <= my_current_y+10)
                            and (tank["x"] <= my_current_x - 50) and (tank_cooldown <= 0)):
                            turn_decision = "LEFT"
                            client.turn_tank(client.token, turn_decision)        
                            client.make_shoot(client.token)
                            pygame.mixer.music.load('Sounds/shoot.mp3')
                            pygame.mixer.music.play(0)
                            tank_cooldown = 25
                        
                        elif ((tank["y"]+31 >= my_current_y+20) and (tank["y"] <= my_current_y+10)
                              and (tank["x"] >= my_current_x + 81) and (tank_cooldown <= 0)):
                            turn_decision = "RIGHT"
                            client.turn_tank(client.token, turn_decision)                        
                            client.make_shoot(client.token)
                            pygame.mixer.music.load('Sounds/shoot.mp3')
                            pygame.mixer.music.play(0)
                            tank_cooldown = 25
                                
                        elif ((tank["x"]+31 >= my_current_x+20) and (tank["x"] <= my_current_x+10)
                              and (tank["y"] <= my_current_y - 50) and (tank_cooldown <= 0)):
                            turn_decision = "UP"
                            client.turn_tank(client.token, turn_decision)         
                            client.make_shoot(client.token)
                            pygame.mixer.music.load('Sounds/shoot.mp3')
                            pygame.mixer.music.play(0)
                            tank_cooldown = 25
                                
                        elif ((tank["x"]+31 >= my_current_x+20) and (tank["x"] <= my_current_x+10)
                              and (tank["y"] >= my_current_y + 81) and (tank_cooldown <= 0)):
                            turn_decision = "DOWN"
                            client.turn_tank(client.token, turn_decision)                      
                            client.make_shoot(client.token)
                            pygame.mixer.music.load('Sounds/shoot.mp3')
                            pygame.mixer.music.play(0)
                            tank_cooldown = 25


                               
                # Отрисовка снарядов  
                for bullet in bullets:
                    draw_multiplayer_bullets(client, **bullet)

                    if bullet["owner"] == client.tank_id:
                        pass


                    # Если мой танк находится под угрозой попадания снаряда,
                    # то он запоминает опасное направление, чтобы потом принять решение
                    # в какую безопасную сторону нужно повернуть, чтобы не попасть под пулю
                    else:
                        if ((bullet["x"] >= my_current_x - 150) and (bullet["x"] <= my_current_x + 150)
                            and (bullet["y"] >= my_current_y - 150) and (bullet["y"] <= my_current_y + 150)):
                            
                            if (bullet["x"] >= my_current_x) and (bullet["x"] <= my_current_x+31) and (bullet["y"] <= my_current_y):
                                if ((my_current_y - bullet["y"] <= 70) or (bullet["direction"] == "DOWN")):
                                    danger_directions.append("UP")
                                if (bullet["direction"] == my_current_direction):
                                    danger_directions.append(my_current_direction)
                                    
                            elif (bullet["x"] >= my_current_x) and (bullet["x"] <= my_current_x+31) and (bullet["y"] >= my_current_y+31):
                                if ((bullet["y"] - my_current_y <= 70) or (bullet["direction"] == "UP")):
                                    danger_directions.append("DOWN")
                                if (bullet["direction"] == my_current_direction):
                                    danger_directions.append(my_current_direction)
                                    
                            elif (bullet["y"] >= my_current_y) and (bullet["y"] <= my_current_y+31) and (bullet["x"] <= my_current_x):
                                if ((my_current_x - bullet["x"] <= 70) or (bullet["direction"] == "RIGHT")):
                                    danger_directions.append("LEFT")
                                if (tank["direction"] == my_current_direction):
                                    danger_directions.append(my_current_direction)
                                    
                            elif (bullet["y"] >= my_current_y) and (bullet["y"] <= my_current_y+31) and (bullet["x"] >= my_current_x+31):
                                if ((bullet["x"] - my_current_x <= 70) or (bullet["direction"] == "LEFT")):
                                    danger_directions.append("RIGHT")
                                if (tank["direction"] == my_current_direction):
                                        danger_directions.append(my_current_direction)


                # Этот блок отвечает за принятие решений по повороту в безопасную сторону
                normal_directions = ["UP","DOWN","RIGHT","LEFT"]
                safe_directions = list(set(normal_directions)-set(danger_directions))
                safe_directions.sort()
                
                
                # Идет учитывание показателя времени AFK и длины массива опасных направлений
                # Далее ИИ на основе всех полученных данных принимает стратегически верное решение
                not_to_be_afk +=1
                if (not_to_be_afk >= 100) or (len(danger_directions)>0):
                    try:
                        if (len(danger_directions)>0):
                            turn_decision = safe_directions[0]
                            client.turn_tank(client.token, turn_decision)
                        elif (not_to_be_afk >= 100):
                            turn_decision = random.choice(safe_directions)
                            client.turn_tank(client.token, turn_decision)
                    except:
                        pass

                    not_to_be_afk = 0


                # Необходимая функциональная часть  
                tank_cooldown -=1        
                danger_directions.clear()

        
                # Отрисовка бокового меню (рейтинг, время, комната)
                side_bar_info = sorted(side_bar_info, key=lambda i: i["new_score_count"], reverse=True)
                
                print_text('ID:', display_width - 190, 120, (255,255,255),15)
                print_text('Score:', display_width - 140, 120, (255,255,255), 15)
                print_text('Health:', display_width - 80, 120, (255,255,255), 15)
                
                table_player_y = 140
                
                for info_line in side_bar_info:
                    if str(info_line["id"]) == client.tank_id:
                        print_text("You", display_width - 195, table_player_y , (0,255,0), 15)
                    else:
                        print_text(str(info_line["id"]), display_width - 205, table_player_y , (255,0,0), 15)
                    print_text(str(info_line["score"]), display_width - 120, table_player_y , (255,255,255), 15)
                    print_text(str(info_line["health"]), display_width - 60, table_player_y , (255,255,255), 15)
                    table_player_y += 25

                print_text('Time: {}'.format(time), display_width - 165, 70, (255,255,255), 30)
                print_text('{}'.format(client.room_id), display_width - 140, 50, (255,255,255), 15)

                pygame.display.update()
                
            else:
                pass
            
        except:

            # Если в игре останется только мой танк или еще несколько других,
            # а время игры уже закончится, то автоматически выявится победитель
            # на основании рейтинговой таблицы счета и здоровья игроков
            # (Сервер почему-то в конце не присылает победителей, поэтому
            # реализовал эту функция у себя в коде)
            side_bar_info = sorted(side_bar_info, key=lambda i: i["new_score_count"], reverse=True)
            
            num = 1
            my_num = 0
            my_score = 0
            for side_line in side_bar_info:
                print(side_line)
                if side_line["id"] == client.tank_id:
                    my_score = side_line["score"]
                    if num == 1:
                        my_num = 1
                else:
                    num +=1

            # Если время закончилось, а есть еще живые танки
            # Вывод информации о победе или поражении на основании выявления победителя
            # Также показывается счет, набранный за всю игру 
            if (game == True) and my_num == 1:
                print_text('Time is out',
                           display_width//2 - 80, display_height//2 - 150, (255,255,255), 30)
                print_text('You win! Score: {}'.format(my_score),
                           display_width//2 - 120, display_height//2 - 100, (255,255,255), 30)
                print_text('Press R or click "Restart" to play again',
                           display_width//2 - 300, display_height//2 - 50, (255,255,255), 30)
                game = False
            else:
                print_text('Time is out',
                           display_width//2 - 80, display_height//2 - 150, (255,255,255), 30)
                print_text('You lost. Score: {}'.format(my_score),
                           display_width//2 - 120, display_height//2 - 100, (255,255,255), 30)
                print_text('Press R or click "Restart" to play again',
                           display_width//2 - 300, display_height//2 - 50, (255,255,255), 30)
                game = False

            pygame.display.update()
        
    # Функция промежуточного меню, дает возможность переиграть
    # или выйти в главное меню
    return game_multiplayer_pause()

#-----------------------------------------        
# Функция запуска мультиплеерной игры
# с использованием ИИ, вызывается кнопкой в главном меню
#-----------------------------------------
def start_AI_multiplayer_game():
    while run_AI_multiplayer_game():
        pass


###################################
#
#   ОТОБРАЖЕНИЕ ГЛАВНОГО МЕНЮ
#
###################################
show_menu()

pygame.quit()
