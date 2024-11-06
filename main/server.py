# server.py
import pygame
import sys
import random
import socket
import threading
from time import sleep

BLACK = (0,0,0)
padWidth = 480  # 게임화면의 가로크기
padHeight = 640 # 게임화면의 세로크기
rockImage = ['asset/rock1.png','asset/rock2.png','asset/rock3.png','asset/rock4.png','asset/rock5.png',
'asset/rock6.png','asset/rock7.png','asset/rock8.png','asset/rock9.png','asset/rock10.png',]

def acceptC():
    global client,server,addr
     # 현재 컴퓨터의 IPv4 주소를 자동으로 얻어오기
    host_ip = socket.gethostbyname(socket.gethostname())
    print(f"클라이언트에서 다음 주소 입력 : {host_ip}")  # 서버의 IP를 출력
    server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.bind((host_ip,8080))
    server.listen()
    client,addr=server.accept()

    #클라이언트로부터 받는 데이터를 관리하기위한 멀티쓰레딩(밑에는 데몬스레드라고 선언 -> c++로 따지면 detach와같습니다)
    thr=threading.Thread(target=consoles,args=())
    thr.Daemon=True
    thr.start()

#여기에 데이터를 받았을때 해야 할 일을 넣어야함
def consoles():
    global fighter2X
    buffer = ""
    while True:
        buffer += client.recv(1024).decode()
        messages = buffer.split("\n") # 줄바꿈을 기준으로 메시지 구분
        buffer = messages.pop()     # 마지막 남은 덜 완성된 메시지는 버퍼에 남김
        for msg in messages:
            print(msg)
            if msg=="quit":
                client.close()
                server.close()
                pygame.quit()
                sys.exit()
            elif msg.startswith("fighter2"):
                _, f2X = msg.split()
                fighter2X = int(f2X)
        pygame.display.update()

# 게임에 등장하는 객체를 드로잉
def drawObject(obj, x, y):
    global gamePad
    gamePad.blit(obj, (x, y))

def initGame():
    global gamePad, clock, background, fighter1, fighter2, missile, explosion
    pygame.init()
    gamePad = pygame.display.set_mode((padWidth, padHeight))
    pygame.display.set_caption("server")  # 게임 이름
    background = pygame.image.load('asset/background.png') # 배경 그림
    fighter1 = pygame.image.load('asset/fighter.png')    # 전투기 그림
    fighter1 = pygame.transform.scale(fighter1, (50, 50)) # 전투기 크기를 50x50으로 조정
    fighter2 = pygame.image.load('asset/fighter.png')    # 전투기 그림
    fighter2 = pygame.transform.scale(fighter2, (50, 50)) # 전투기 크기를 50x50으로 조정
    missile = pygame.image.load('asset/missile.png')    # 미사일 그림
    missile = pygame.transform.scale(missile, (20, 30)) # 미사일 크기를 20x30으로 조정
    explosion = pygame.transform.scale(pygame.image.load('asset/explosion.png'),(55,55))    # 폭발 그림
    clock = pygame.time.Clock()

def runGame():
    global gamePad, clock, background, fighter1, fighter2, missile, explosion
    global fighter2X #클라이언트에서 제어하는 전투기2의 x좌표

    # 무기 좌표 리스트
    missileXY = []

    # 운석 랜덤 생성, 초기 위치 설정
    rock, rockWidth, rockHeight, rockX, rockY, rock_index = createRandomRock()
    rockSpeed = 2

    # 전투기 크기
    fighterSize = fighter1.get_rect().size
    fighterWidth = fighterSize[0]
    fighterHeight = fighterSize[1]

    # 전투기1 초기 위치 (x, y)
    x1 = padWidth * 0.3
    y1 = padHeight * 0.9
    fighter1X = 0

    # 전투기 2 초기 위치 및 변수
    fighter2X = padWidth * 0.6
    y2 = padHeight * 0.9

    # 전투기,미사일,운석 판정
    isShot = False  # 운석에 미사일 적중
    shotCount = 0   # 적중횟수
    rockPassed = 0  # 격추 실패 횟수

    moving_left = moving_right = False  # 이동 상태 추적용 플래그

    onGame = False

    while not onGame:
        for event in pygame.event.get():
            if event.type in [pygame.QUIT]: # 게임 프로그램 종료
                client.close()
                server.close()
                pygame.quit()
                sys.exit()
            
            if event.type in [pygame.KEYDOWN]:
                if event.key == pygame.K_LEFT:  # 전투기 왼쪽으로 이동
                    moving_left = True
                    fighter1X -= 5
                elif event.key == pygame.K_RIGHT:   # 전투기 오른쪽으로 이동
                    moving_right = True
                    fighter1X += 5
                elif event.key == pygame.K_SPACE:   # 미사일 발사
                    missileX = x1 + (fighterWidth / 2) - (missile.get_rect().width / 2)
                    missileY = y1 - fighterHeight
                    missileXY.append([missileX, missileY])
                    msg="서버 미사일 발사\n"
                    client.sendall(msg.encode()) #클라이언트에게 내가내린명령전송
            
            if event.type in [pygame.KEYUP]:    #방향키를 떼면 전투기 멈춤
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    fighter1X = 0
                    moving_right = False
                    moving_left = False

        drawObject(background, 0, 0) # 배경 화면 그리기

        # 전투기 위치 재조정
        x1 += fighter1X
        if x1<0:
            x1=0
        elif x1 > padWidth - fighterWidth:
            x1 = padWidth - fighterWidth
        
        # 전투기2 위치 이동 제어
        if fighter2X < 0 :
            fighter2X = 0
        elif fighter2X > padWidth - fighterWidth:
            fighter2X = padWidth - fighterWidth

        # 전투기가 운석과 충돌했는지 체크
        if y1 < rockY + rockHeight :
            if(rockX > x1 and rockX < x1 + fighterWidth) or \
                (rockX + rockWidth > x1 and rockX + rockWidth < x1 + fighterWidth):
                client.sendall("crash\n".encode())
                crash()

        # 비행기를 게임 화면의 (x, y) 좌표에 그림
        drawObject(fighter1, x1, y1)   
        drawObject(fighter2, fighter2X, y2)

        # 서버에 전투기1 위치를 전송
        if moving_left or moving_right:
            client.sendall(f"fighter1 {str(int(x1))}\n".encode())

        # 미사일 발사 화면에 그리기
        if len(missileXY) != 0:
            for i, bxy in enumerate(missileXY): # 미사일 요소에 대해 반복함
                bxy[1] -= 10    # 총알의 y좌표 -10 (위로 이동)
                missileXY[i][1] = bxy[1]

                # 미사일이 운석을 맞추었을 경우
                if bxy[1] < rockY:
                    if bxy[0] > rockX and bxy[0] < rockX + rockWidth:
                        missileXY.remove(bxy)
                        isShot = True
                        shotCount += 1

                if bxy[1] <= 0: # 미사일이 화면 밖을 벗어나면
                    try:
                        missileXY.remove(bxy)   # 미사일 제거
                    except:
                        pass
        if len(missileXY) != 0:
            for bx, by in missileXY:
                drawObject(missile, bx, by)

        rockY += rockSpeed  # 운석 아래로 움직임
        rock_info = f"ROCK {rock_index} {rockX} {int(rockY)}\n"
        client.sendall(rock_info.encode())

        
        # 운석이 지구로 떨어진 경우
        if rockY > padHeight:
            # 새로운 운석 (랜덤)
            rock, rockWidth, rockHeight, rockX, rockY, rock_index = createRandomRock()
            rockPassed += 1
            client.sendall(f"passed {rockPassed}\n".encode())
            if rockPassed == 3:
                gameOver()
                
        
        # 운석을 맞춘 경우 
        if isShot:
            # 운석 폭발
            drawObject(explosion, rockX, rockY) #운석 폭발 그리기
            client.sendall(f"explosion {int(rockX)} {int(rockY)} {shotCount}\n".encode())
            # 새로운 운석 (랜덤)
            rock, rockWidth, rockHeight, rockX, rockY, rock_index = createRandomRock()
            isShot = False

            # 운석 맞추면 속도 증가
            rockSpeed += 0.1
            if rockSpeed >= 10:
                rockSpeed = 10
        
        writeScore(shotCount)
        writePassed(rockPassed)

        drawObject(rock, rockX, rockY)  # 운석 그리기

        pygame.display.update() # 게임 화면을 다시그림
        
        clock.tick(60)  # 게임화면의 초당 프레임수를 60으로 설정
    
    pygame.quit()   #pygame 종료

# 랜덤 운석 생성 함수
def createRandomRock():
    rock_index = random.randint(0, len(rockImage) - 1)
    rock = pygame.transform.scale(pygame.image.load(rockImage[rock_index]), (50, 50))
    rockSize = rock.get_rect().size
    rockWidth = rockSize[0]
    rockHeight = rockSize[1]
    rockX = random.randrange(0, padWidth - rockWidth)
    rockY = 0
    rock_info = f"ROCK {rock_index} {rockX} {rockY}"
    return rock, rockWidth, rockHeight, rockX, rockY, rock_index

# 운석 맞춘 개수 표시
def writeScore(count):
    global gamePad
    font = pygame.font.Font('asset/NanumGothic.ttf', 20)
    text = font.render('파괴한 운석 수:' + str(count), True, (255,255,255))
    gamePad.blit(text,(10,0))

# 격추 실패 횟수 표시
def writePassed(count):
    global gamePad
    font = pygame.font.Font('asset/NanumGothic.ttf', 20)
    text = font.render('놓친 운석:' + str(count), True, (255,0,0))
    gamePad.blit(text,(360,0))

# 게임 메시지 출력
def writeMessage(text):
    global gamePad
    textfont = pygame.font.Font('asset/NanumGothic.ttf', 80)
    text = textfont.render(text, True, (255,0,0))
    textpos = text.get_rect()
    textpos.center = (padWidth/2, padHeight/2)
    gamePad.blit(text,textpos)
    pygame.display.update()
    sleep(2)
    runGame()

# 전투기가 운석과 충돌했을 때 메시지 출력
def crash():
    global gamePad
    writeMessage('전투기 파괴!')

# 게임 오버 메시지 보이기
def gameOver():
    global gamePad
    writeMessage('게임 오버!')

acceptC()
initGame()
runGame()