# client.py
import pygame
import sys
import socket
import threading
import os
from time import sleep

BLACK = (0,0,0)
padWidth = 480  # 게임화면의 가로크기
padHeight = 640 # 게임화면의 세로크기

# OS에 맞게 파일 경로 생성
asset_path = os.path.join(os.path.dirname(__file__), 'asset')
rockImage = [os.path.join(asset_path, f'rock{i}.png') for i in range(1, 11)]

def acceptC():
    global client
    host_ip = input("서버 주소 입력 : ")
    #host_ip = socket.gethostbyname(socket.gethostname()) #개발중 빠른 재기동을 위한 라인
    client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect((host_ip,8080))

    thr=threading.Thread(target=consoles,args=())
    thr.Daemon=True
    thr.start()

#여기에 데이터를 받았을때 해야 할 일을 넣어야함
def consoles():
    global rock_initialized, remainLife, iscrashed, shotCount, fighter1X, client_missiles
    buffer = ""
    while True:
        buffer += client.recv(1024).decode('utf-8')
        messages = buffer.split("\n") # 줄바꿈을 기준으로 메시지 구분
        buffer = messages.pop() # 마지막 남은 덜 완성된 메시지는 버퍼에 남김
        for msg in messages:
            #print(msg)
            if not msg:
                continue # 빈 메시지 건너뛰기
            if msg.startswith("ROCK"):
                _, rock_index, rockx, rocky = msg.split()
                rock_index = int(rock_index)
                rockx = int(rockx)
                rocky = int(rocky)
                createRockFromServer(rock_index, rockx, rocky)
                rock_initialized = True  # 첫 번째 운석이 도착하면 초기화
            elif msg.startswith("passed"):
                _, passed_count = msg.split()
                remainLife = int(passed_count)
            elif msg == "crash":
                iscrashed = True
            elif msg.startswith("explosion"):
                _, exX, exY, shotCount = msg.split()
                drawObject(explosion, int(exX), int(exY)) #운석 폭발 그리기
                pygame.mixer.Sound.play(Explosion_sound)#폭발 효과음 플레이
            elif msg.startswith("fighter1"):
                _, f1X = msg.split()
                fighter1X = int(f1X)
            elif msg.startswith("MISSILES"):
                missile_positions = msg.split()[1:]
                # 클라이언트가 그릴 미사일 좌표 리스트 업데이트
                client_missiles = [(int(x), int(y)) for pos in missile_positions for x, y in [pos.split(",")]]

        pygame.display.update()

# 게임에 등장하는 객체를 드로잉
def drawObject(obj, x, y):
    global gamePad
    gamePad.blit(obj, (x, y))

def initGame():
    global gamePad, clock, background, fighter1, fighter2, missile, explosion
    pygame.init()
    gamePad = pygame.display.set_mode((padWidth, padHeight))
    pygame.display.set_caption("client")  # 게임 이름
    
    background = pygame.image.load(os.path.join(asset_path, 'background.png')) # 배경 그림
    fighter1 = pygame.image.load(os.path.join(asset_path, 'red_fighter.png'))    # 전투기 그림
    fighter1 = pygame.transform.scale(fighter1, (50, 50)) # 전투기 크기를 50x50으로 조정
    fighter2 = pygame.image.load(os.path.join(asset_path, 'blue_fighter.png'))    # 전투기 그림
    fighter2 = pygame.transform.scale(fighter2, (50, 50)) # 전투기 크기를 50x50으로 조정
    missile = pygame.image.load(os.path.join(asset_path, 'missile.png'))    # 미사일 그림
    missile = pygame.transform.scale(missile, (20, 30)) # 미사일 크기를 20x30으로 조정
    explosion = pygame.transform.scale(pygame.image.load(os.path.join(asset_path, 'explosion.png')),(55,55))    # 폭발 그림
    clock = pygame.time.Clock()

    #효과음 추가
    global Shot_sound, Crashed_sound, Explosion_sound, GameOver_sound
    
    Shot_sound = pygame.mixer.Sound(os.path.join(asset_path,'shot.wav'))
    Crashed_sound = pygame.mixer.Sound(os.path.join(asset_path,'fighterCrashed.wav'))
    Explosion_sound = pygame.mixer.Sound(os.path.join(asset_path,'explosion.wav'))
    GameOver_sound = pygame.mixer.Sound(os.path.join(asset_path,'Electric Noise Short.wav'))



def runGame():
    global gamePad, clock, background, fighter1, fighter2, missile, explosion
    global rock, rockX, rockY, rockWidth, rockHeight, rock_initialized
    global remainLife, iscrashed, shotCount, client_missiles
    global fighter1X # 서버에서 조종하는 전투기1 위치

    # 미사일 좌표 초기화
    client_missiles = []

    # 운석 위치 및 크기 초기화 플래기
    rock_initialized = False

    # 전투기크기
    fighterSize = fighter2.get_rect().size
    fighterWidth = fighterSize[0]
    fighterHeight = fighterSize[1]

    # 전투기2 초기위치
    x2 = padWidth * 0.6
    y2 = padHeight * 0.9
    fighter2X = 0

    # 전투기1 초기위치 및 변수
    fighter1X = padWidth * 0.3
    y1 = padHeight * 0.9

    # 전투기,미사일,운석 판정
    shotCount = 0   # 적중횟수
    remainLife = 3  # 남은목숨
    iscrashed = False
    
    moving_left = moving_right = False  # 이동 상태 추적용 플래그

    onGame = False

    while not onGame:
        for event in pygame.event.get():
            if event.type in [pygame.QUIT]: # 게임 프로그램 종료
                client.close()
                pygame.quit()
                sys.exit()
            
            if event.type in [pygame.KEYDOWN]:
                if event.key == pygame.K_LEFT:  # 전투기 왼쪽으로 이동
                    moving_left = True
                    fighter2X -= 5
                
                elif event.key == pygame.K_RIGHT:   # 전투기 오른쪽으로 이동
                    moving_right = True
                    fighter2X += 5
                
                elif event.key == pygame.K_SPACE:   # 미사일 발사 요청
                    client.sendall("missile_request\n".encode('utf-8'))
                    #미사일 발사 효과음 플레이
                    pygame.mixer.Sound.play(Shot_sound)
            
            if event.type in [pygame.KEYUP]:    #방향키를 떼면 전투기 멈춤
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    fighter2X = 0
                    moving_left = False
                    moving_right = False

        drawObject(background, 0, 0) # 배경 화면 그리기

        # 전투기 위치 재조정
        x2 += fighter2X
        if x2<0:
            x2=0
        elif x2 > padWidth - fighterWidth:
            x2 = padWidth - fighterWidth

        # 전투기1 위치 이동 제어
        if fighter1X < 0 :
            fighter1X = 0
        elif fighter1X > padWidth - fighterWidth:
            fighter1X = padWidth - fighterWidth

        drawObject(fighter2, x2, y2)   # 비행기를 게임 화면의 (x, y) 좌표에 그림
        drawObject(fighter1, fighter1X, y1)
        
        # 서버에 전투기2 위치를 전송
        if moving_left or moving_right:
            client.sendall(f"fighter2 {str(int(x2))}\n".encode('utf-8'))
 
        # 운석 정보가 초기화된 이후에만 실행하는 블록
        if rock_initialized:
            # 전투기가 운석과 충돌했는지 체크
            if iscrashed :
                crash()
            # 운석이 지구로 떨어진 경우
            if remainLife == 0:
                gameOver()
            # 모든 미사일 그리기
            for mx, my in client_missiles:
                drawObject(missile, mx, my)
            # 운석 그리기
            drawObject(rock, rockX, rockY)   
        writeScore(shotCount)
        writePassed(remainLife)
        pygame.display.update() # 게임 화면을 다시그림
        clock.tick(60)  # 게임화면의 초당 프레임수를 60으로 설정
    

    pygame.quit()   #pygame 종료

# 서버로부터 받은 운석정보를 바탕으로 운석 생성
def createRockFromServer(rock_index, rockx, rocky):
    global rock, rockWidth, rockHeight, rockX, rockY
    rock = pygame.transform.scale(pygame.image.load(rockImage[rock_index]), (50, 50))
    rockSize = rock.get_rect().size
    rockWidth = rockSize[0]
    rockHeight = rockSize[1]
    rockX = rockx
    rockY = rocky

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
    text = font.render('남은 목숨:' + str(count), True, (255,0,0))
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
    pygame.mixer.Sound.play(Crashed_sound)#전투기와 운석 충돌했을때 효과음 플레이
    writeMessage('전투기 파괴!')

# 게임 오버 메시지 보이기
def gameOver():
    global gamePad
    pygame.mixer.Sound.play(GameOver_sound)
    writeMessage('게임 오버!')

acceptC()
initGame()
runGame()