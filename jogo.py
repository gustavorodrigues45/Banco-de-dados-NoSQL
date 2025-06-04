import pygame
import time
import random
import sys
import os # Para manipulação de caminhos de arquivo e verificação de existência

pygame.init()
pygame.mixer.init() # Inicializa o mixer para sons

# --- Configurações Visuais ---
COR_FUNDO = (152, 251, 152)
COR_COBRA_CORPO = (0, 128, 0)
COR_COBRA_CONTORNO = (0, 100, 0)
COR_CABECA = (0, 150, 0)
COR_OLHOS = (255, 255, 255)
COR_PUPILAS = (0, 0, 0)
COR_COMIDA_MACA = (255, 0, 0)
COR_COMIDA_CAULE = (139, 69, 19)
COR_TEXTO_PONTUACAO = (50, 50, 50)
COR_TEXTO_GAMEOVER = (200, 0, 0)
COR_TEXTO_MENU = (70, 70, 70)
COR_TEXTO_MENU_SELECIONADO = (0, 0, 200)
COR_TEXTO_PAUSA = (0, 0, 128)
COR_TEXTO_RECORDE = (218, 165, 32) # Dourado

# --- Dimensões e Tela ---
largura_tela = 800
altura_tela = 600
tela = pygame.display.set_mode((largura_tela, altura_tela))
pygame.display.set_caption('Jogo da Cobrinha Super Avançado')

# --- Controle de Jogo ---
relogio = pygame.time.Clock()
tamanho_bloco_cobra = 20
velocidade_base_cobra = 10 # Velocidade inicial
velocidade_atual_cobra = velocidade_base_cobra

# --- Arquivo de Recorde ---
ARQUIVO_RECORDE = "highscore.txt"

# --- Fontes ---
try:
    fonte_titulo_menu = pygame.font.SysFont("bahnschrift", 70)
    fonte_menu = pygame.font.SysFont("bahnschrift", 40)
    fonte_info = pygame.font.SysFont("bahnschrift", 30)
    fonte_score = pygame.font.SysFont("comicsansms", 35)
except pygame.error:
    fonte_titulo_menu = pygame.font.SysFont(None, 80)
    fonte_menu = pygame.font.SysFont(None, 50)
    fonte_info = pygame.font.SysFont(None, 40)
    fonte_score = pygame.font.SysFont(None, 45)

# --- Carregar Sons (coloque seus arquivos .wav ou .ogg na pasta do jogo) ---
som_comer = None
som_game_over = None
try:
    if os.path.exists("eat_sound.wav"):
        som_comer = pygame.mixer.Sound("eat_sound.wav")
    else:
        print("Aviso: Arquivo 'eat_sound.wav' não encontrado.")
    if os.path.exists("game_over_sound.wav"):
        som_game_over = pygame.mixer.Sound("game_over_sound.wav")
    else:
        print("Aviso: Arquivo 'game_over_sound.wav' não encontrado.")
except pygame.error as e:
    print(f"Erro ao carregar sons: {e}")


# --- Constantes de Direção ---
DIR_DIREITA = "DIREITA"
DIR_ESQUERDA = "ESQUERDA"
DIR_CIMA = "CIMA"
DIR_BAIXO = "BAIXO"

# --- Estados do Jogo ---
ESTADO_MENU_PRINCIPAL = "MENU_PRINCIPAL"
ESTADO_JOGANDO = "JOGANDO"
ESTADO_PAUSADO = "PAUSADO"
ESTADO_FIM_DE_JOGO = "FIM_DE_JOGO"
ESTADO_TELA_RECORDE = "TELA_RECORDE"
ESTADO_SAIR = "SAIR"


# --- Funções de Recorde ---
def carregar_recorde():
    try:
        with open(ARQUIVO_RECORDE, 'r') as f:
            return int(f.read())
    except (FileNotFoundError, ValueError):
        return 0

def salvar_recorde(novo_recorde):
    try:
        with open(ARQUIVO_RECORDE, 'w') as f:
            f.write(str(novo_recorde))
    except IOError:
        print("Erro ao salvar recorde!")

recorde_atual = carregar_recorde()

# --- Funções Auxiliares de Desenho ---
def mostrar_texto_centralizado(texto, fonte, cor, y_offset=0, superficie=tela):
    """Exibe texto centralizado na tela com um deslocamento Y opcional."""
    render = fonte.render(texto, True, cor)
    rect = render.get_rect(center=(largura_tela / 2, altura_tela / 2 + y_offset))
    superficie.blit(render, rect)

def mostrar_texto(texto, fonte, cor, x, y, superficie=tela):
    """Exibe texto em uma posição específica."""
    render = fonte.render(texto, True, cor)
    superficie.blit(render, (x, y))

def mostrar_score_hud(score, high_score): # HUD = Heads-Up Display
    """Exibe a pontuação e o recorde durante o jogo."""
    score_val = fonte_score.render("Pontuação: " + str(score), True, COR_TEXTO_PONTUACAO)
    tela.blit(score_val, [10, 10])
    highscore_val = fonte_info.render("Recorde: " + str(high_score), True, COR_TEXTO_RECORDE)
    tela.blit(highscore_val, [10, 45])


def desenhar_comida(x, y):
    raio_maca = int(tamanho_bloco_cobra / 2)
    centro_x_maca = int(x + raio_maca)
    centro_y_maca = int(y + raio_maca)
    pygame.draw.circle(tela, COR_COMIDA_MACA, (centro_x_maca, centro_y_maca), raio_maca)
    pygame.draw.rect(tela, COR_COMIDA_CAULE, [x + raio_maca - 2, y - 3, 4, 6])
    pygame.draw.circle(tela, (255, 255, 200), (int(x + tamanho_bloco_cobra / 1.5), int(y + tamanho_bloco_cobra / 3)), int(tamanho_bloco_cobra / 8))

def desenhar_cobra(lista_cobra, direcao_atual):
    raio_borda = int(tamanho_bloco_cobra / 4)
    for i, (x, y) in enumerate(lista_cobra[:-1]):
        pygame.draw.rect(tela, COR_COBRA_CONTORNO, [x, y, tamanho_bloco_cobra, tamanho_bloco_cobra], border_radius=raio_borda)
        pygame.draw.rect(tela, COR_COBRA_CORPO, [x + 2, y + 2, tamanho_bloco_cobra - 4, tamanho_bloco_cobra - 4], border_radius=max(0, raio_borda - 1))

    if lista_cobra:
        cabeca_x, cabeca_y = lista_cobra[-1]
        pygame.draw.rect(tela, COR_COBRA_CONTORNO, [cabeca_x, cabeca_y, tamanho_bloco_cobra, tamanho_bloco_cobra], border_radius=raio_borda)
        pygame.draw.rect(tela, COR_CABECA, [cabeca_x + 2, cabeca_y + 2, tamanho_bloco_cobra - 4, tamanho_bloco_cobra - 4], border_radius=max(0, raio_borda - 1))

        tamanho_olho = int(tamanho_bloco_cobra / 5)
        tamanho_pupila = int(tamanho_olho / 2)
        offset_base_olho = int(tamanho_bloco_cobra / 4)
        centro_cabeca_x = cabeca_x + tamanho_bloco_cobra / 2
        centro_cabeca_y = cabeca_y + tamanho_bloco_cobra / 2

        offsets_olhos_por_direcao = {
            DIR_DIREITA: ((offset_base_olho / 2, -offset_base_olho), (offset_base_olho / 2, offset_base_olho)),
            DIR_ESQUERDA: ((-offset_base_olho / 2, -offset_base_olho), (-offset_base_olho / 2, offset_base_olho)),
            DIR_CIMA: ((-offset_base_olho, -offset_base_olho / 2), (offset_base_olho, -offset_base_olho / 2)),
            DIR_BAIXO: ((-offset_base_olho, offset_base_olho / 2), (offset_base_olho, offset_base_olho / 2)),
        }
        offset_par_olhos = offsets_olhos_por_direcao.get(direcao_atual, offsets_olhos_por_direcao[DIR_DIREITA])
        olho1_pos_rel, olho2_pos_rel = offset_par_olhos
        olho1_pos = (int(centro_cabeca_x + olho1_pos_rel[0]), int(centro_cabeca_y + olho1_pos_rel[1]))
        olho2_pos = (int(centro_cabeca_x + olho2_pos_rel[0]), int(centro_cabeca_y + olho2_pos_rel[1]))

        pygame.draw.circle(tela, COR_OLHOS, olho1_pos, tamanho_olho)
        pygame.draw.circle(tela, COR_OLHOS, olho2_pos, tamanho_olho)
        pygame.draw.circle(tela, COR_PUPILAS, olho1_pos, tamanho_pupila)
        pygame.draw.circle(tela, COR_PUPILAS, olho2_pos, tamanho_pupila)

# --- Funções de Lógica do Jogo ---
def inicializar_variaveis_jogo():
    global velocidade_atual_cobra # Acessa a variável global para resetá-la
    snake_x = round((largura_tela / 2) / tamanho_bloco_cobra) * tamanho_bloco_cobra
    snake_y = round((altura_tela / 2) / tamanho_bloco_cobra) * tamanho_bloco_cobra
    snake_x_change = 0
    snake_y_change = 0
    direcao_atual = DIR_DIREITA
    lista_cobra = [[snake_x, snake_y]]
    comprimento_cobra = 1
    pontuacao = 0
    velocidade_atual_cobra = velocidade_base_cobra # Reseta a velocidade

    comida_x = round(random.randrange(0, largura_tela - tamanho_bloco_cobra) / float(tamanho_bloco_cobra)) * tamanho_bloco_cobra
    comida_y = round(random.randrange(0, altura_tela - tamanho_bloco_cobra) / float(tamanho_bloco_cobra)) * tamanho_bloco_cobra
    
    return snake_x, snake_y, snake_x_change, snake_y_change, direcao_atual, lista_cobra, comprimento_cobra, comida_x, comida_y, pontuacao

# --- Loop Principal e Gerenciador de Estados ---
def main():
    global recorde_atual # Para atualizar o recorde globalmente
    global velocidade_atual_cobra

    estado_atual = ESTADO_MENU_PRINCIPAL
    rodando = True

    # Variáveis do jogo (serão inicializadas quando o jogo começar)
    snake_x, snake_y, snake_x_change, snake_y_change = 0,0,0,0
    direcao_atual, lista_cobra, comida_x, comida_y = DIR_DIREITA, [], 0, 0
    comprimento_cobra, pontuacao = 1, 0

    # Controle do menu
    opcoes_menu = ["Iniciar Jogo", "Recorde", "Sair"]
    opcao_selecionada_menu = 0

    while rodando:
        eventos = pygame.event.get()
        for event in eventos:
            if event.type == pygame.QUIT:
                rodando = False
                estado_atual = ESTADO_SAIR # Garante que saia do loop principal
            
            if estado_atual == ESTADO_MENU_PRINCIPAL:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        opcao_selecionada_menu = (opcao_selecionada_menu - 1) % len(opcoes_menu)
                    elif event.key == pygame.K_DOWN:
                        opcao_selecionada_menu = (opcao_selecionada_menu + 1) % len(opcoes_menu)
                    elif event.key == pygame.K_RETURN:
                        if opcao_selecionada_menu == 0: # Iniciar Jogo
                            (snake_x, snake_y, snake_x_change, snake_y_change,
                             direcao_atual, lista_cobra, comprimento_cobra,
                             comida_x, comida_y, pontuacao) = inicializar_variaveis_jogo()
                            estado_atual = ESTADO_JOGANDO
                        elif opcao_selecionada_menu == 1: # Recorde
                            estado_atual = ESTADO_TELA_RECORDE
                        elif opcao_selecionada_menu == 2: # Sair
                            rodando = False
                            estado_atual = ESTADO_SAIR
            
            elif estado_atual == ESTADO_TELA_RECORDE:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                        estado_atual = ESTADO_MENU_PRINCIPAL

            elif estado_atual == ESTADO_JOGANDO:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        estado_atual = ESTADO_PAUSADO
                    # Movimentação (não alterada da versão anterior)
                    elif event.key == pygame.K_LEFT and direcao_atual != DIR_DIREITA:
                        snake_x_change = -tamanho_bloco_cobra; snake_y_change = 0; direcao_atual = DIR_ESQUERDA
                    elif event.key == pygame.K_RIGHT and direcao_atual != DIR_ESQUERDA:
                        snake_x_change = tamanho_bloco_cobra; snake_y_change = 0; direcao_atual = DIR_DIREITA
                    elif event.key == pygame.K_UP and direcao_atual != DIR_BAIXO:
                        snake_y_change = -tamanho_bloco_cobra; snake_x_change = 0; direcao_atual = DIR_CIMA
                    elif event.key == pygame.K_DOWN and direcao_atual != DIR_CIMA:
                        snake_y_change = tamanho_bloco_cobra; snake_x_change = 0; direcao_atual = DIR_BAIXO
            
            elif estado_atual == ESTADO_PAUSADO:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                        estado_atual = ESTADO_JOGANDO
            
            elif estado_atual == ESTADO_FIM_DE_JOGO:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q: # Sair para o menu
                        estado_atual = ESTADO_MENU_PRINCIPAL
                    if event.key == pygame.K_c: # Jogar Novamente
                        (snake_x, snake_y, snake_x_change, snake_y_change,
                         direcao_atual, lista_cobra, comprimento_cobra,
                         comida_x, comida_y, pontuacao) = inicializar_variaveis_jogo()
                        estado_atual = ESTADO_JOGANDO
        
        # --- Lógica de Atualização de Estados ---
        if estado_atual == ESTADO_JOGANDO:
            if not (snake_x_change == 0 and snake_y_change == 0):
                 snake_x += snake_x_change
                 snake_y += snake_y_change

            if snake_x >= largura_tela or snake_x < 0 or snake_y >= altura_tela or snake_y < 0:
                if som_game_over: pygame.mixer.Sound.play(som_game_over)
                if pontuacao > recorde_atual:
                    recorde_atual = pontuacao
                    salvar_recorde(recorde_atual)
                estado_atual = ESTADO_FIM_DE_JOGO
            
            cabeca_cobra = [snake_x, snake_y]
            lista_cobra.append(cabeca_cobra)

            if len(lista_cobra) > comprimento_cobra:
                del lista_cobra[0]

            if not (snake_x_change == 0 and snake_y_change == 0): # Evita game over se estiver parado
                for segmento in lista_cobra[:-1]:
                    if segmento == cabeca_cobra:
                        if som_game_over: pygame.mixer.Sound.play(som_game_over)
                        if pontuacao > recorde_atual:
                            recorde_atual = pontuacao
                            salvar_recorde(recorde_atual)
                        estado_atual = ESTADO_FIM_DE_JOGO
                        break 
            
            if snake_x == comida_x and snake_y == comida_y:
                if som_comer: pygame.mixer.Sound.play(som_comer)
                comida_x = round(random.randrange(0, largura_tela - tamanho_bloco_cobra) / float(tamanho_bloco_cobra)) * tamanho_bloco_cobra
                comida_y = round(random.randrange(0, altura_tela - tamanho_bloco_cobra) / float(tamanho_bloco_cobra)) * tamanho_bloco_cobra
                comprimento_cobra += 1
                pontuacao += 1
                # Aumenta a velocidade a cada 5 pontos, até um limite
                if pontuacao % 3 == 0 and velocidade_atual_cobra < velocidade_base_cobra * 2.5:
                    velocidade_atual_cobra += 1


        # --- Desenho na Tela (baseado no estado) ---
        tela.fill(COR_FUNDO)

        if estado_atual == ESTADO_MENU_PRINCIPAL:
            mostrar_texto_centralizado("Jogo da Cobrinha", fonte_titulo_menu, COR_TEXTO_MENU, -150)
            for i, opcao_texto in enumerate(opcoes_menu):
                cor = COR_TEXTO_MENU_SELECIONADO if i == opcao_selecionada_menu else COR_TEXTO_MENU
                mostrar_texto_centralizado(opcao_texto, fonte_menu, cor, -50 + i * 60)
            mostrar_texto("Use ↑ ↓ e ENTER", fonte_info, (100,100,100), 10, altura_tela - 40)

        elif estado_atual == ESTADO_TELA_RECORDE:
            mostrar_texto_centralizado("Maior Pontuação", fonte_titulo_menu, COR_TEXTO_RECORDE, -100)
            mostrar_texto_centralizado(str(recorde_atual), fonte_titulo_menu, COR_TEXTO_RECORDE, 0)
            mostrar_texto_centralizado("Pressione ENTER ou ESC para voltar", fonte_info, COR_TEXTO_MENU, 150)
        
        elif estado_atual == ESTADO_JOGANDO:
            desenhar_comida(comida_x, comida_y)
            desenhar_cobra(lista_cobra, direcao_atual)
            mostrar_score_hud(pontuacao, recorde_atual)
        
        elif estado_atual == ESTADO_PAUSADO:
            # Mantém a tela do jogo, mas adiciona a mensagem de pausa
            desenhar_comida(comida_x, comida_y)
            desenhar_cobra(lista_cobra, direcao_atual)
            mostrar_score_hud(pontuacao, recorde_atual)
            # Overlay semi-transparente para escurecer a tela
            s = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA) # por pixel alpha
            s.fill((0,0,0,128)) # preto com 50% de transparência
            tela.blit(s, (0,0))
            mostrar_texto_centralizado("PAUSADO", fonte_titulo_menu, COR_TEXTO_PAUSA, -50)
            mostrar_texto_centralizado("Pressione P ou ESC para continuar", fonte_info, COR_TEXTO_PAUSA, 50)

        elif estado_atual == ESTADO_FIM_DE_JOGO:
            mostrar_texto_centralizado("Você Perdeu!", fonte_titulo_menu, COR_TEXTO_GAMEOVER, -100)
            mostrar_texto_centralizado(f"Pontuação Final: {pontuacao}", fonte_menu, COR_TEXTO_PONTUACAO, 0)
            if pontuacao >= recorde_atual and pontuacao > 0 : # Se for um novo recorde (e não 0)
                 mostrar_texto_centralizado("NOVO RECORDE!", fonte_menu, COR_TEXTO_RECORDE, 50)
            else:
                 mostrar_texto_centralizado(f"Recorde Atual: {recorde_atual}", fonte_info, COR_TEXTO_RECORDE, 50)
            mostrar_texto_centralizado("C-Jogar Novamente  |  Q-Menu Principal", fonte_info, COR_TEXTO_MENU, 150)
        
        if estado_atual != ESTADO_SAIR: # Evita chamar tick e update se já estiver saindo
            pygame.display.update()
            relogio.tick(velocidade_atual_cobra if estado_atual == ESTADO_JOGANDO else 15) # FPS mais baixo para menus/pausa

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()