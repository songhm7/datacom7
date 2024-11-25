import pygame

# 초기화
pygame.init()
pygame.display.set_mode((1, 1))

# 이미지 로드
fighter_image = pygame.image.load('main/asset/fighter.png').convert_alpha()

# 색 변경 함수
def tint_image(image, color):
    # 이미지의 복사본 생성
    tinted_image = image.copy()
    tinted_image.fill(color, special_flags=pygame.BLEND_MULT)
    return tinted_image

# 빨간색과 파란색 이미지 생성
red_fighter = tint_image(fighter_image, (187,0,0))
blue_fighter = tint_image(fighter_image, (0,191,255))

# 이미지를 PNG 파일로 저장
pygame.image.save(red_fighter, "main/asset/red_fighter.png")
pygame.image.save(blue_fighter, "main/asset/blue_fighter.png")

print("Images saved as 'red_fighter.png' and 'blue_fighter.png'.")

screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((255, 255, 255))
    screen.blit(red_fighter, (100, 100))  # 빨간색 전투기
    screen.blit(blue_fighter, (300, 100))  # 파란색 전투기
    pygame.display.flip()
    clock.tick(30)

pygame.quit()