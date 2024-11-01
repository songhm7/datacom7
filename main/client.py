# client.py
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
    global client
    host_ip = input("서버 주소 입력 : ")
    # host_ip = socket.gethostbyname(socket.gethostname()) // 개발중 빠른 재기동을 위한 라인
    client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect((host_ip,8080))

    thr=threading.Thread(target=consoles,args=())
    thr.Daemon=True
    thr.start()

def consoles():
    #여기에 데이터를 받았을때 해야 할 일을 넣어야함
    while True:
        msg=client.recv(1024)
        print(msg.decode())

# 게임에 등장하는 객체를 드로잉
def drawObject(obj, x, y):
    global gamePad
    gamePad.blit(obj, (x, y))

def initGame():
    global gamePad, clock, background, fighter, missile, explosion
    pygame.init()
    gamePad = pygame.display.set_mode((padWidth, padHeight))
    pygame.display.set_caption("client")  # 게임 이름
    background = pygame.image.load('asset/background.png') # 배경 그림
    fighter = pygame.image.load('asset/fighter.png')    # 전투기 그림
    fighter = pygame.transform.scale(fighter, (50, 50)) # 전투기 크기를 50x50으로 조정
    missile = pygame.image.load('asset/missile.png')    # 미사일 그림
    missile = pygame.transform.scale(missile, (20, 30)) # 미사일 크기를 20x30으로 조정
    explosion = pygame.transform.scale(pygame.image.load('asset/explosion.png'),(55,55))    # 폭발 그림

    clock = pygame.time.Clock()

def runGame():
    global gamePad, clock, background, fighter, missile, explosion

    # 무기 좌표 리스트
    missileXY = []

    # 운석 랜덤 생성, 초기 위치 설정
    rock, rockWidth, rockHeight, rockX, rockY = createRandomRock()
    rockSpeed = 2



    # 전투기 크기
    fighterSize = fighter.get_rect().size
    fighterWidth = fighterSize[0]
    fighterHeight = fighterSize[1]

    # 전투기 초기 위치 (x, y)
    x = padWidth * 0.45
    y = padHeight * 0.9
    fighterX = 0

    # 전투기,미사일,운석 판정
    isShot = False  # 운석에 미사일 적중
    shotCount = 0   # 적중횟수
    rockPassed = 0  # 격추 실패 횟수

    onGame = False
    while not onGame:
        for event in pygame.event.get():
            if event.type in [pygame.QUIT]: # 게임 프로그램 종료
                pygame.quit()
                sys.exit()
            
            if event.type in [pygame.KEYDOWN]:
                if event.key == pygame.K_LEFT:  # 전투기 왼쪽으로 이동
                    fighterX -= 5
                
                elif event.key == pygame.K_RIGHT:   # 전투기 오른쪽으로 이동
                    fighterX += 5
                
                elif event.key == pygame.K_SPACE:   # 미사일 발사
                    missileX = x + (fighterWidth / 2) - (missile.get_rect().width / 2)
                    missileY = y - fighterHeight
                    missileXY.append([missileX, missileY])
                    msg="클라이언트 미사일 발사"
                    client.sendall(msg.encode()) #서버에게 내가내린명령전송
            
            if event.type in [pygame.KEYUP]:    #방향키를 떼면 전투기 멈춤
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    fighterX = 0

        drawObject(background, 0, 0) # 배경 화면 그리기

        # 전투기 위치 재조정
        x += fighterX
        if x<0:
            x=0
        elif x > padWidth - fighterWidth:
            x = padWidth - fighterWidth
        
        # 전투기가 운석과 충돌했는지 체크
        if y < rockY + rockHeight :
            if(rockX > x and rockX < x + fighterWidth) or \
                (rockX + rockWidth > x and rockX + rockWidth < x + fighterWidth):
                crash()

        drawObject(fighter, x, y)   # 비행기를 게임 화면의 (x, y) 좌표에 그림

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

        # 운석이 지구로 떨어진 경우
        if rockY > padHeight:
            # 새로운 운석 (랜덤)
            rock, rockWidth, rockHeight, rockX, rockY = createRandomRock()
            rockPassed += 1
            if rockPassed == 3:
                gameOver()
        
        # 운석을 맞춘 경우 
        if isShot:
            # 운석 폭발
            drawObject(explosion, rockX, rockY) #운석 폭발 그리기

            # 새로운 운석 (랜덤)
            rock, rockWidth, rockHeight, rockX, rockY = createRandomRock()
            isShot = False

            # 운석 맞추면 속도 증가
            rockSpeed += 0.02
            if rockSpeed >= 10:
                rockSpeed = 10
        
        writeScore(shotCount)
        writePassed(rockPassed)

        drawObject(rock, rockX, rockY)  # 운석 그리기

        pygame.display.update() # 게임 화면을 다시그림
        
        clock.tick(60)  # 게임화면의 초당 프레임수를 60으로 설정
    
    pygame.quit()   #pygame 종료

# 랜덤 운석 생성 함수
# 추후 랜덤위치가 아닌 서버플레이어가 결정하도록 수정할 것
def createRandomRock():
    rock = pygame.transform.scale(pygame.image.load(random.choice(rockImage)), (50, 50))
    rockSize = rock.get_rect().size
    rockWidth = rockSize[0]
    rockHeight = rockSize[1]
    rockX = random.randrange(0, padWidth - rockWidth)
    rockY = 0
    return rock, rockWidth, rockHeight, rockX, rockY

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