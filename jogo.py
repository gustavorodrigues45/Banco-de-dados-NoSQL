import pygame
import time
import random

pygame.init()

# --- Configurações Visuais Melhoradas ---
COR_FUNDO = (152, 251, 152)  # Verde claro para o fundo (grama)
COR_COBRA_CORPO = (0, 128, 0) # Verde escuro para o corpo
COR_COBRA_CONTORNO = (0, 100, 0) # Contorno um pouco mais escuro
COR_CABECA = (0, 150, 0)      # Verde um pouco mais claro para a cabeça
COR_OLHOS = (255, 255, 255)   # Branco para os olhos
COR_PUPILAS = (0,0,0)         # Preto para as pupilas
COR_COMIDA_MACA = (255, 0, 0)   # Vermelho para a maçã
COR_COMIDA_CAULE = (139, 69, 19) # Marrom para o caule

# Dimensões da Tela
largura_tela = 800 # Aumentei um pouco para melhor visualização
altura_tela = 600

# Criação da Tela
tela = pygame.display.set_mode((largura_tela, altura_tela))
pygame.display.set_caption('Jogo da Cobrinha Mais Realista (por IA)')

# Controle de FPS
relogio = pygame.time.Clock()

# Tamanho do bloco da cobra e velocidade
tamanho_bloco_cobra = 20 # Aumentei o bloco para melhor visualização dos detalhes
velocidade_cobra = 12

# Fonte para mensagens
fonte_estilo = pygame.font.SysFont("bahnschrift", 30)
fonte_score = pygame.font.SysFont("comicsansms", 35)

def mostrar_score(score):
    """Exibe a pontuação na tela."""
    valor = fonte_score.render("Pontuação: " + str(score), True, (50,50,50)) # Cor mais escura para contraste
    tela.blit(valor, [10, 10])

def desenhar_comida(x, y):
    """Desenha a comida (maçã) na tela."""
    # Corpo da maçã
    pygame.draw.circle(tela, COR_COMIDA_MACA, (int(x + tamanho_bloco_cobra / 2), int(y + tamanho_bloco_cobra / 2)), int(tamanho_bloco_cobra / 2))
    # Caule da maçã
    pygame.draw.rect(tela, COR_COMIDA_CAULE, [x + tamanho_bloco_cobra / 2 - 2, y - 3, 4, 6])
    # Pequeno brilho (opcional)
    pygame.draw.circle(tela, (255,255,200), (int(x + tamanho_bloco_cobra / 1.5), int(y + tamanho_bloco_cobra / 3)), int(tamanho_bloco_cobra / 8))


def desenhar_cobra(tamanho_bloco_cobra, lista_cobra, direcao_atual):
    """Desenha a cobra na tela com segmentos arredondados e cabeça distinta."""
    raio_borda = int(tamanho_bloco_cobra / 4) # Raio para arredondar as bordas

    # Desenha o corpo
    for i, (x,y) in enumerate(lista_cobra[:-1]): # Todos menos a cabeça
        # Contorno
        pygame.draw.rect(tela, COR_COBRA_CONTORNO, [x, y, tamanho_bloco_cobra, tamanho_bloco_cobra], border_radius=raio_borda)
        # Preenchimento
        pygame.draw.rect(tela, COR_COBRA_CORPO, [x+2, y+2, tamanho_bloco_cobra-4, tamanho_bloco_cobra-4], border_radius=raio_borda-1 if raio_borda > 1 else 0)

    # Desenha a cabeça
    if lista_cobra:
        cabeca_x, cabeca_y = lista_cobra[-1] # A cabeça é o último elemento adicionado
        # Contorno da cabeça
        pygame.draw.rect(tela, COR_COBRA_CONTORNO, [cabeca_x, cabeca_y, tamanho_bloco_cobra, tamanho_bloco_cobra], border_radius=raio_borda)
        # Preenchimento da cabeça
        pygame.draw.rect(tela, COR_CABECA, [cabeca_x+2, cabeca_y+2, tamanho_bloco_cobra-4, tamanho_bloco_cobra-4], border_radius=raio_borda-1 if raio_borda > 1 else 0)

        # Olhos (simples)
        tamanho_olho = int(tamanho_bloco_cobra / 5)
        tamanho_pupila = int(tamanho_olho / 2)
        offset_olho = int(tamanho_bloco_cobra / 4) # Distância do centro
        centro_cabeca_x = cabeca_x + tamanho_bloco_cobra / 2
        centro_cabeca_y = cabeca_y + tamanho_bloco_cobra / 2

        if direcao_atual == "DIREITA":
            olho1_pos = (int(centro_cabeca_x + offset_olho/2), int(centro_cabeca_y - offset_olho))
            olho2_pos = (int(centro_cabeca_x + offset_olho/2), int(centro_cabeca_y + offset_olho))
        elif direcao_atual == "ESQUERDA":
            olho1_pos = (int(centro_cabeca_x - offset_olho/2), int(centro_cabeca_y - offset_olho))
            olho2_pos = (int(centro_cabeca_x - offset_olho/2), int(centro_cabeca_y + offset_olho))
        elif direcao_atual == "CIMA":
            olho1_pos = (int(centro_cabeca_x - offset_olho), int(centro_cabeca_y - offset_olho/2))
            olho2_pos = (int(centro_cabeca_x + offset_olho), int(centro_cabeca_y - offset_olho/2))
        elif direcao_atual == "BAIXO":
            olho1_pos = (int(centro_cabeca_x - offset_olho), int(centro_cabeca_y + offset_olho/2))
            olho2_pos = (int(centro_cabeca_x + offset_olho), int(centro_cabeca_y + offset_olho/2))
        else: # Posição inicial ou neutra
             olho1_pos = (int(centro_cabeca_x + offset_olho), int(centro_cabeca_y - offset_olho))
             olho2_pos = (int(centro_cabeca_x + offset_olho), int(centro_cabeca_y + offset_olho))


        pygame.draw.circle(tela, COR_OLHOS, olho1_pos, tamanho_olho)
        pygame.draw.circle(tela, COR_OLHOS, olho2_pos, tamanho_olho)
        pygame.draw.circle(tela, COR_PUPILAS, olho1_pos, tamanho_pupila)
        pygame.draw.circle(tela, COR_PUPILAS, olho2_pos, tamanho_pupila)


def mostrar_mensagem(msg, cor):
    """Exibe uma mensagem no centro da tela."""
    linhas = msg.splitlines()
    altura_total_msg = len(linhas) * fonte_estilo.get_height()
    y_inicial = (altura_tela - altura_total_msg) / 2

    for i, linha in enumerate(linhas):
        mesg = fonte_estilo.render(linha, True, cor)
        text_rect = mesg.get_rect(center=(largura_tela / 2, y_inicial + i * fonte_estilo.get_height()))
        tela.blit(mesg, text_rect)


def gameLoop():
    """Função principal do jogo."""
    game_over = False
    game_close = False

    # Posição inicial da cobra
    x1 = largura_tela / 2
    y1 = altura_tela / 2

    # Mudança de posição inicial
    x1_change = 0
    y1_change = 0
    direcao_atual = "DIREITA" # Direção inicial para os olhos

    # Corpo da cobra e comprimento inicial
    lista_cobra = []
    comprimento_cobra = 1

    # Posição da comida
    # Garante que a comida apareça em posições alinhadas com o grid da cobra
    comida_x = round(random.randrange(0, largura_tela - tamanho_bloco_cobra) / float(tamanho_bloco_cobra)) * tamanho_bloco_cobra
    comida_y = round(random.randrange(0, altura_tela - tamanho_bloco_cobra) / float(tamanho_bloco_cobra)) * tamanho_bloco_cobra

    while not game_over:

        while game_close:
            tela.fill(COR_FUNDO)
            mostrar_mensagem("Você Perdeu!\nPressione Q-Sair ou C-Jogar Novamente", (200,0,0))
            mostrar_score(comprimento_cobra - 1)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_over = True
                    game_close = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over = True
                        game_close = False
                    if event.key == pygame.K_c:
                        gameLoop() # Reinicia o jogo

        # Eventos do teclado
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and direcao_atual != "DIREITA":
                    x1_change = -tamanho_bloco_cobra
                    y1_change = 0
                    direcao_atual = "ESQUERDA"
                elif event.key == pygame.K_RIGHT and direcao_atual != "ESQUERDA":
                    x1_change = tamanho_bloco_cobra
                    y1_change = 0
                    direcao_atual = "DIREITA"
                elif event.key == pygame.K_UP and direcao_atual != "BAIXO":
                    y1_change = -tamanho_bloco_cobra
                    x1_change = 0
                    direcao_atual = "CIMA"
                elif event.key == pygame.K_DOWN and direcao_atual != "CIMA":
                    y1_change = tamanho_bloco_cobra
                    x1_change = 0
                    direcao_atual = "BAIXO"

        # Verifica se a cobra bateu nas bordas
        if x1 >= largura_tela or x1 < 0 or y1 >= altura_tela or y1 < 0:
            game_close = True

        # Atualiza a posição da cobra
        x1 += x1_change
        y1 += y1_change
        tela.fill(COR_FUNDO) # Cor de fundo

        # Desenha a comida
        desenhar_comida(comida_x, comida_y)

        # Lógica do corpo da cobra
        cabeca_cobra = []
        cabeca_cobra.append(x1)
        cabeca_cobra.append(y1)
        lista_cobra.append(cabeca_cobra) # Adiciona nova cabeça ao final da lista

        if len(lista_cobra) > comprimento_cobra:
            del lista_cobra[0] # Remove a cauda (o primeiro elemento) se não comeu

        # Verifica se a cobra bateu em si mesma
        # Verifica todos os segmentos exceto a cabeça (o último elemento)
        for segmento in lista_cobra[:-1]:
            if segmento == cabeca_cobra:
                game_close = True

        # Desenha a cobra
        desenhar_cobra(tamanho_bloco_cobra, lista_cobra, direcao_atual)
        # Mostra o score
        mostrar_score(comprimento_cobra - 1)

        pygame.display.update()

        # Se a cobra comeu a comida
        if x1 == comida_x and y1 == comida_y:
            comida_x = round(random.randrange(0, largura_tela - tamanho_bloco_cobra) / float(tamanho_bloco_cobra)) * tamanho_bloco_cobra
            comida_y = round(random.randrange(0, altura_tela - tamanho_bloco_cobra) / float(tamanho_bloco_cobra)) * tamanho_bloco_cobra
            comprimento_cobra += 1
            # Aumentar velocidade (opcional)
            # if velocidade_cobra < 30 :
            #     velocidade_cobra += 0.5


        relogio.tick(velocidade_cobra)

    pygame.quit()
    quit()

# Inicia o jogo
gameLoop()