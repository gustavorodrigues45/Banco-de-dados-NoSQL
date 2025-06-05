import pygame
import time
import random
import sys
import os
from collections import deque # Para a fila do BFS

pygame.init()
pygame.mixer.init()

# --- Configurações Visuais (mantidas da versão anterior) ---
COR_FUNDO = (152, 251, 152)
COR_COBRA_CORPO = (0, 128, 0)
COR_COBRA_CONTORNO = (0, 100, 0)
COR_CABECA = (0, 150, 0)
COR_OLHOS = (255, 255, 255)
COR_PUPILAS = (0, 0, 0)
COR_COMIDA_MACA = (255, 0, 0)
COR_COMIDA_CAULE = (139, 69, 19)
COR_OBSTACULO = (100, 100, 100)
COR_POWERUP_SLOW = (0, 0, 255)
COR_POWERUP_BONUS = (255, 215, 0)
COR_TEXTO_PONTUACAO = (50, 50, 50)
COR_TEXTO_GAMEOVER = (200, 0, 0)
COR_TEXTO_MENU = (70, 70, 70)
COR_TEXTO_MENU_SELECIONADO = (0, 0, 200)
COR_TEXTO_PAUSA = (0, 0, 128)
COR_TEXTO_RECORDE = (218, 165, 32)
COR_TEXTO_AI_STATUS = (200, 100, 0) # Laranja para status da IA

# --- Dimensões e Tela ---
largura_tela = 800
altura_tela = 600
tela = pygame.display.set_mode((largura_tela, altura_tela))
pygame.display.set_caption('Jogo da Cobrinha com IA Autônoma')

# --- Controle de Jogo ---
relogio = pygame.time.Clock()
tamanho_bloco = 20
velocidade_base_cobra = 10

# --- Configurações de Obstáculos e Power-ups (mantidas) ---
NUM_OBSTACULOS = 7
PONTOS_PARA_GERAR_POWERUP = 3
DURACAO_POWERUP_SLOW = 7000
PONTOS_DO_POWERUP_BONUS = 25

# --- Arquivo de Recorde (mantido) ---
ARQUIVO_RECORDE = "highscore.txt"

# --- Fontes (mantidas) ---
try:
    fonte_titulo_menu = pygame.font.SysFont("bahnschrift", 70)
    fonte_menu = pygame.font.SysFont("bahnschrift", 40)
    fonte_info = pygame.font.SysFont("bahnschrift", 30) # Usada para AI status também
    fonte_score = pygame.font.SysFont("comicsansms", 35)
except pygame.error: # Fallback
    fonte_titulo_menu = pygame.font.SysFont(None, 80)
    fonte_menu = pygame.font.SysFont(None, 50)
    fonte_info = pygame.font.SysFont(None, 40)
    fonte_score = pygame.font.SysFont(None, 45)

# --- Carregar Sons (mantido) ---
som_comer, som_game_over, som_powerup = None, None, None
try:
    if os.path.exists("eat_sound.wav"): som_comer = pygame.mixer.Sound("eat_sound.wav")
    else: print("Aviso: 'eat_sound.wav' não encontrado.")
    if os.path.exists("game_over_sound.wav"): som_game_over = pygame.mixer.Sound("game_over_sound.wav")
    else: print("Aviso: 'game_over_sound.wav' não encontrado.")
    if os.path.exists("powerup_sound.wav"): som_powerup = pygame.mixer.Sound("powerup_sound.wav")
    else: print("Aviso: 'powerup_sound.wav' não encontrado.")
except pygame.error as e: print(f"Erro ao carregar sons: {e}")


# --- Constantes de Direção ---
DIR_DIREITA = "DIREITA"; DIR_ESQUERDA = "ESQUERDA"; DIR_CIMA = "CIMA"; DIR_BAIXO = "BAIXO"
MOVIMENTOS_POSSIVEIS = { # dx, dy, nome_direcao
    DIR_CIMA: (0, -tamanho_bloco, DIR_CIMA),
    DIR_BAIXO: (0, tamanho_bloco, DIR_BAIXO),
    DIR_ESQUERDA: (-tamanho_bloco, 0, DIR_ESQUERDA),
    DIR_DIREITA: (tamanho_bloco, 0, DIR_DIREITA),
}
OPPOSTOS = {DIR_CIMA: DIR_BAIXO, DIR_BAIXO: DIR_CIMA, DIR_ESQUERDA: DIR_DIREITA, DIR_DIREITA: DIR_ESQUERDA}


# --- Tipos de Power-up (mantido) ---
POWERUP_NONE = "NONE"; POWERUP_SLOW_SNAKE = "SLOW_SNAKE"; POWERUP_BONUS_POINTS = "BONUS_POINTS"

# --- Estados do Jogo (mantido) ---
ESTADO_MENU_PRINCIPAL = "MENU_PRINCIPAL"; ESTADO_JOGANDO = "JOGANDO"; ESTADO_PAUSADO = "PAUSADO"
ESTADO_FIM_DE_JOGO = "FIM_DE_JOGO"; ESTADO_TELA_RECORDE = "TELA_RECORDE"; ESTADO_SAIR = "SAIR"

# --- Variáveis Globais de Estado do Jogo ---
powerup_ativo_lentidao = False
tempo_fim_lentidao = 0
comidas_normais_coletadas = 0
velocidade_atual_cobra = velocidade_base_cobra
ai_controle_ativo = False # Nova variável para controle da IA

# --- Funções de Recorde (mantidas) ---
def carregar_recorde():
    try:
        with open(ARQUIVO_RECORDE, 'r') as f: return int(f.read())
    except (FileNotFoundError, ValueError): return 0
def salvar_recorde(novo_recorde):
    try:
        with open(ARQUIVO_RECORDE, 'w') as f: f.write(str(novo_recorde))
    except IOError: print("Erro ao salvar recorde!")
recorde_atual = carregar_recorde()

# --- Funções Auxiliares de Desenho e Lógica (maioria mantida, algumas adaptadas) ---
def mostrar_texto_centralizado(texto, fonte, cor, y_offset=0, superficie=tela):
    render = fonte.render(texto, True, cor)
    rect = render.get_rect(center=(largura_tela / 2, altura_tela / 2 + y_offset))
    superficie.blit(render, rect)

def mostrar_texto(texto, fonte, cor, x, y, superficie=tela):
    render = fonte.render(texto, True, cor)
    superficie.blit(render, (x, y))

def mostrar_hud_jogo(score, high_score, ai_ativo): # Adaptado para mostrar status da IA
    score_val = fonte_score.render("Pontuação: " + str(score), True, COR_TEXTO_PONTUACAO)
    tela.blit(score_val, [10, 10])
    highscore_val = fonte_info.render("Recorde: " + str(high_score), True, COR_TEXTO_RECORDE)
    tela.blit(highscore_val, [10, 45])
    if ai_ativo:
        ai_status_val = fonte_info.render("IA ATIVA (A)", True, COR_TEXTO_AI_STATUS)
        tela.blit(ai_status_val, [largura_tela - ai_status_val.get_width() - 10, 10])


def desenhar_bloco(cor, x, y, raio_borda_percent=0.25):
    # ... (sem alteração)
    raio = int(tamanho_bloco * raio_borda_percent) if raio_borda_percent > 0 else 0
    pygame.draw.rect(tela, cor, [x, y, tamanho_bloco, tamanho_bloco], border_radius=raio)

def desenhar_comida(x, y):
    # ... (sem alteração)
    raio_maca = int(tamanho_bloco / 2)
    centro_x_maca = int(x + raio_maca)
    centro_y_maca = int(y + raio_maca)
    pygame.draw.circle(tela, COR_COMIDA_MACA, (centro_x_maca, centro_y_maca), raio_maca)
    pygame.draw.rect(tela, COR_COMIDA_CAULE, [x + raio_maca - 2, y - 3, 4, 6])
    pygame.draw.circle(tela, (255, 255, 200), (int(x + tamanho_bloco / 1.5), int(y + tamanho_bloco / 3)), int(tamanho_bloco / 8))

def desenhar_powerup(powerup):
    # ... (sem alteração)
    if powerup['tipo'] == POWERUP_SLOW_SNAKE: desenhar_bloco(COR_POWERUP_SLOW, powerup['x'], powerup['y'])
    elif powerup['tipo'] == POWERUP_BONUS_POINTS: desenhar_bloco(COR_POWERUP_BONUS, powerup['x'], powerup['y'])

def desenhar_obstaculos(lista_obstaculos):
    # ... (sem alteração)
    for obs_x, obs_y in lista_obstaculos: desenhar_bloco(COR_OBSTACULO, obs_x, obs_y)

def desenhar_cobra(lista_cobra, direcao_atual):
    # ... (sem alteração)
    raio_borda_corpo = int(tamanho_bloco / 4)
    for i, (x, y) in enumerate(lista_cobra[:-1]): # Corpo
        pygame.draw.rect(tela, COR_COBRA_CONTORNO, [x, y, tamanho_bloco, tamanho_bloco], border_radius=raio_borda_corpo)
        pygame.draw.rect(tela, COR_COBRA_CORPO, [x + 2, y + 2, tamanho_bloco - 4, tamanho_bloco - 4], border_radius=max(0, raio_borda_corpo - 1))
    if lista_cobra: # Cabeça
        cabeca_x, cabeca_y = lista_cobra[-1]
        pygame.draw.rect(tela, COR_COBRA_CONTORNO, [cabeca_x, cabeca_y, tamanho_bloco, tamanho_bloco], border_radius=raio_borda_corpo)
        pygame.draw.rect(tela, COR_CABECA, [cabeca_x + 2, cabeca_y + 2, tamanho_bloco - 4, tamanho_bloco - 4], border_radius=max(0, raio_borda_corpo - 1))
        tamanho_olho = int(tamanho_bloco / 5); tamanho_pupila = int(tamanho_olho / 2)
        offset_base_olho = int(tamanho_bloco / 4)
        centro_cabeca_x = cabeca_x + tamanho_bloco / 2; centro_cabeca_y = cabeca_y + tamanho_bloco / 2
        offsets_olhos_por_direcao = {
            DIR_DIREITA: ((offset_base_olho / 2, -offset_base_olho), (offset_base_olho / 2, offset_base_olho)),
            DIR_ESQUERDA: ((-offset_base_olho / 2, -offset_base_olho), (-offset_base_olho / 2, offset_base_olho)),
            DIR_CIMA: ((-offset_base_olho, -offset_base_olho / 2), (offset_base_olho, -offset_base_olho / 2)),
            DIR_BAIXO: ((-offset_base_olho, offset_base_olho / 2), (offset_base_olho, offset_base_olho / 2)),}
        offset_par_olhos = offsets_olhos_por_direcao.get(direcao_atual, offsets_olhos_por_direcao[DIR_DIREITA])
        olho1_pos_rel, olho2_pos_rel = offset_par_olhos
        olho1_pos = (int(centro_cabeca_x + olho1_pos_rel[0]), int(centro_cabeca_y + olho1_pos_rel[1]))
        olho2_pos = (int(centro_cabeca_x + olho2_pos_rel[0]), int(centro_cabeca_y + olho2_pos_rel[1]))
        pygame.draw.circle(tela, COR_OLHOS, olho1_pos, tamanho_olho); pygame.draw.circle(tela, COR_OLHOS, olho2_pos, tamanho_olho)
        pygame.draw.circle(tela, COR_PUPILAS, olho1_pos, tamanho_pupila); pygame.draw.circle(tela, COR_PUPILAS, olho2_pos, tamanho_pupila)


def gerar_posicao_aleatoria_livre(lista_cobra, lista_obstaculos, comida_atual_pos, powerup_atual_obj):
    # ... (sem alteração)
    while True:
        x = round(random.randrange(0, largura_tela - tamanho_bloco) / float(tamanho_bloco)) * tamanho_bloco
        y = round(random.randrange(0, altura_tela - tamanho_bloco) / float(tamanho_bloco)) * tamanho_bloco
        posicao_ocupada = False
        # Convert lists of lists/dicts to lists of tuples for faster 'in' check with sets if performance is an issue
        # For now, direct list checking is fine
        if [x,y] in lista_cobra or [x,y] in lista_obstaculos:
            posicao_ocupada = True
        if comida_atual_pos and x == comida_atual_pos[0] and y == comida_atual_pos[1]:
            posicao_ocupada = True
        if powerup_atual_obj and x == powerup_atual_obj['x'] and y == powerup_atual_obj['y']:
            posicao_ocupada = True
        if not posicao_ocupada:
            return x, y

def inicializar_variaveis_jogo():
    # ... (sem grandes alterações, apenas garante que ai_controle_ativo seja falso no início do jogo)
    global velocidade_atual_cobra, powerup_ativo_lentidao, tempo_fim_lentidao, comidas_normais_coletadas, ai_controle_ativo

    snake_x = round((largura_tela / 2) / tamanho_bloco) * tamanho_bloco
    snake_y = round((altura_tela / 2) / tamanho_bloco) * tamanho_bloco
    snake_x_change, snake_y_change = 0, 0
    direcao_atual = DIR_DIREITA
    lista_cobra = [[snake_x, snake_y]]
    comprimento_cobra = 1; pontuacao = 0
    
    velocidade_atual_cobra = velocidade_base_cobra
    powerup_ativo_lentidao = False; tempo_fim_lentidao = 0
    comidas_normais_coletadas = 0
    ai_controle_ativo = False # Desativa IA no início de cada jogo

    lista_obstaculos = []
    posicoes_invalidas_spawn = [[snake_x, snake_y]] 
    comida_x_inicial, comida_y_inicial = gerar_posicao_aleatoria_livre(lista_cobra, lista_obstaculos, None, None)
    posicoes_invalidas_spawn.append([comida_x_inicial, comida_y_inicial])

    for _ in range(NUM_OBSTACULOS):
        obs_x, obs_y = 0,0 # init
        tentativas = 0
        pos_valida_obs = False
        while not pos_valida_obs and tentativas < 50:
            obs_x, obs_y = gerar_posicao_aleatoria_livre(lista_cobra, lista_obstaculos, [comida_x_inicial, comida_y_inicial], None)
            if [obs_x, obs_y] not in posicoes_invalidas_spawn: # Adicionalmente checa contra a lista temporária
                pos_valida_obs = True
            tentativas +=1
        
        if pos_valida_obs:
            lista_obstaculos.append([obs_x, obs_y])
            posicoes_invalidas_spawn.append([obs_x, obs_y])

    comida_x, comida_y = comida_x_inicial, comida_y_inicial
    powerup_atual_obj = None 
    
    return (snake_x, snake_y, snake_x_change, snake_y_change, direcao_atual, lista_cobra, 
            comprimento_cobra, comida_x, comida_y, pontuacao, lista_obstaculos, powerup_atual_obj)


# --- Lógica da Inteligência Artificial ---
def bfs_find_path(start_node_pos, target_node_pos, snake_list, obstacles_list):
    """Encontra o caminho mais curto usando BFS."""
    queue = deque([[start_node_pos, []]])  # Fila: [ (posição_atual_cabeça), [lista_de_movimentos_para_chegar_aqui] ]
    visited = {tuple(start_node_pos)}      # Posições da cabeça já visitadas para evitar ciclos

    while queue:
        current_pos, path = queue.popleft()

        if current_pos[0] == target_node_pos[0] and current_pos[1] == target_node_pos[1]:
            return path # Retorna a lista de movimentos

        # Explora vizinhos (Cima, Baixo, Esquerda, Direita)
        # Ordem de preferência pode ser ajustada aqui se necessário
        for move_name in [DIR_DIREITA, DIR_ESQUERDA, DIR_CIMA, DIR_BAIXO]: 
            dx, dy, _ = MOVIMENTOS_POSSIVEIS[move_name]
            next_x, next_y = current_pos[0] + dx, current_pos[1] + dy
            next_pos_list = [next_x, next_y] # Próxima posição da cabeça como lista [x,y]
            next_pos_tuple = (next_x, next_y) # Próxima posição da cabeça como tupla (x,y) para 'visited'

            # Verifica validade do movimento
            if not (0 <= next_x < largura_tela and 0 <= next_y < altura_tela): # Fora da tela
                continue
            if next_pos_list in obstacles_list: # Colisão com obstáculo
                continue
            # Colisão com o próprio corpo (considerando que a cauda se moverá)
            # Se next_pos_list estiver no corpo da cobra ATUAL, exceto a cauda, é colisão
            if next_pos_list in snake_list[:-1]: 
                continue
            
            if next_pos_tuple not in visited:
                visited.add(next_pos_tuple)
                new_path = path + [move_name] # Adiciona o nome da direção ao caminho
                queue.append([next_pos_list, new_path])
    return None # Nenhum caminho encontrado

def get_ai_move(snake_list, current_direction, food_pos, obstacles_list):
    """Decide o próximo movimento da IA."""
    if not snake_list: return current_direction # Segurança

    head_pos = snake_list[-1]

    # 1. Tenta encontrar caminho para a comida
    path_to_food = bfs_find_path(head_pos, food_pos, snake_list, obstacles_list)
    if path_to_food:
        # print(f"IA: Caminho para comida encontrado: {path_to_food}")
        return path_to_food[0] # Retorna o primeiro movimento do caminho

    # 2. Modo Sobrevivência: Se não há caminho para comida, tenta qualquer movimento seguro
    # print("IA: Modo sobrevivência.")
    # Prioriza movimentos que não sejam o oposto da direção atual
    prefered_moves = []
    fallback_moves = []

    for move_name in [DIR_DIREITA, DIR_ESQUERDA, DIR_CIMA, DIR_BAIXO]: # Ordem pode influenciar "personalidade"
        dx, dy, _ = MOVIMENTOS_POSSIVEIS[move_name]
        next_x, next_y = head_pos[0] + dx, head_pos[1] + dy
        next_pos_list = [next_x, next_y]

        is_safe = True
        if not (0 <= next_x < largura_tela and 0 <= next_y < altura_tela): is_safe = False
        if next_pos_list in obstacles_list: is_safe = False
        if next_pos_list in snake_list[:-1]: is_safe = False
        
        if is_safe:
            if len(snake_list) == 1 or move_name != OPPOSTOS.get(current_direction):
                prefered_moves.append(move_name)
            else: # Movimento reverso, menos preferível
                fallback_moves.append(move_name)
    
    if prefered_moves:
        # Poderia adicionar uma heurística aqui, como mover-se para o maior espaço vazio,
        # ou na direção que estava indo, se seguro. Por ora, aleatório entre os preferidos.
        return random.choice(prefered_moves) 
    if fallback_moves: # Se só sobrou movimento reverso seguro
        return random.choice(fallback_moves)

    # 3. Se nenhum movimento seguro, retorna a direção atual (provavelmente resultará em game over)
    # print("IA: Nenhum movimento seguro encontrado!")
    return current_direction


# --- Loop Principal e Gerenciador de Estados ---
def main():
    global recorde_atual, velocidade_atual_cobra 
    global powerup_ativo_lentidao, tempo_fim_lentidao, comidas_normais_coletadas
    global ai_controle_ativo # Importante para modificar a global

    estado_atual = ESTADO_MENU_PRINCIPAL
    rodando = True
    opcoes_menu = ["Iniciar Jogo", "Recorde", "Sair"]; opcao_selecionada_menu = 0
    
    snake_x, snake_y, snake_x_change, snake_y_change, direcao_atual, lista_cobra, \
    comprimento_cobra, comida_x, comida_y, pontuacao, lista_obstaculos, powerup_atual_obj = \
    0,0,0,0,DIR_DIREITA,[],1,0,0,0,[],None 

    while rodando:
        tempo_agora = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: rodando = False; estado_atual = ESTADO_SAIR
            
            if estado_atual == ESTADO_MENU_PRINCIPAL:
                # ... (lógica do menu mantida)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP: opcao_selecionada_menu = (opcao_selecionada_menu - 1) % len(opcoes_menu)
                    elif event.key == pygame.K_DOWN: opcao_selecionada_menu = (opcao_selecionada_menu + 1) % len(opcoes_menu)
                    elif event.key == pygame.K_RETURN:
                        if opcao_selecionada_menu == 0: # Iniciar Jogo
                            (snake_x, snake_y, snake_x_change, snake_y_change,
                             direcao_atual, lista_cobra, comprimento_cobra,
                             comida_x, comida_y, pontuacao, lista_obstaculos,
                             powerup_atual_obj) = inicializar_variaveis_jogo() # ai_controle_ativo é resetado aqui
                            estado_atual = ESTADO_JOGANDO
                        elif opcao_selecionada_menu == 1: estado_atual = ESTADO_TELA_RECORDE
                        elif opcao_selecionada_menu == 2: rodando = False; estado_atual = ESTADO_SAIR
            
            elif estado_atual == ESTADO_TELA_RECORDE:
                # ... (lógica mantida)
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN):
                    estado_atual = ESTADO_MENU_PRINCIPAL

            elif estado_atual == ESTADO_JOGANDO:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p: estado_atual = ESTADO_PAUSADO
                    elif event.key == pygame.K_a: # Alterna controle da IA
                        ai_controle_ativo = not ai_controle_ativo
                        print(f"Controle da IA: {'Ativado' if ai_controle_ativo else 'Desativado'}")
                        if ai_controle_ativo: # Se acabou de ativar a IA, limpa as mudanças de input do jogador
                            snake_x_change, snake_y_change = 0,0 


                    if not ai_controle_ativo: # Processa input do jogador APENAS se IA estiver desativada
                        if event.key == pygame.K_LEFT and direcao_atual != DIR_DIREITA:
                            snake_x_change = -tamanho_bloco; snake_y_change = 0; direcao_atual = DIR_ESQUERDA
                        elif event.key == pygame.K_RIGHT and direcao_atual != DIR_ESQUERDA:
                            snake_x_change = tamanho_bloco; snake_y_change = 0; direcao_atual = DIR_DIREITA
                        elif event.key == pygame.K_UP and direcao_atual != DIR_BAIXO:
                            snake_y_change = -tamanho_bloco; snake_x_change = 0; direcao_atual = DIR_CIMA
                        elif event.key == pygame.K_DOWN and direcao_atual != DIR_CIMA:
                            snake_y_change = tamanho_bloco; snake_x_change = 0; direcao_atual = DIR_BAIXO
            
            elif estado_atual == ESTADO_PAUSADO:
                # ... (lógica mantida)
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_p or event.key == pygame.K_ESCAPE):
                    estado_atual = ESTADO_JOGANDO
            
            elif estado_atual == ESTADO_FIM_DE_JOGO:
                # ... (lógica mantida)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q: estado_atual = ESTADO_MENU_PRINCIPAL; ai_controle_ativo = False # Desativa IA ao sair
                    if event.key == pygame.K_c:
                        (snake_x, snake_y, snake_x_change, snake_y_change,
                         direcao_atual, lista_cobra, comprimento_cobra,
                         comida_x, comida_y, pontuacao, lista_obstaculos,
                         powerup_atual_obj) = inicializar_variaveis_jogo() # ai_controle_ativo é resetado aqui
                        estado_atual = ESTADO_JOGANDO

        # --- Lógica de Decisão da IA (se ativa) ---
        if estado_atual == ESTADO_JOGANDO and ai_controle_ativo:
            if lista_cobra: # Garante que a cobra exista
                # A IA decide a *próxima direção*, não a mudança de coordenadas diretamente
                # Isso evita que a IA tente se mover instantaneamente em direções opostas sem passar um frame
                proxima_direcao_ia = get_ai_move(lista_cobra, direcao_atual, [comida_x, comida_y], lista_obstaculos)
                
                # Se a IA retornou uma direção válida e não é oposta à atual (ou cobra tem tamanho 1)
                if proxima_direcao_ia and \
                   (len(lista_cobra) == 1 or proxima_direcao_ia != OPPOSTOS.get(direcao_atual)):
                    
                    dx, dy, nome_dir = MOVIMENTOS_POSSIVEIS[proxima_direcao_ia]
                    snake_x_change, snake_y_change = dx, dy
                    direcao_atual = nome_dir 
                # Se a IA não encontrou um movimento bom ou tentou reverter, a cobra continua com a mudança anterior
                # (ou parada se snake_x_change/y_change for 0).
                # A lógica de sobrevivência do get_ai_move deve tentar evitar isso.
        
        # --- Lógica de Atualização de Estados (Jogo Principal) ---
        if estado_atual == ESTADO_JOGANDO:
            # ... (Efeito do Power-up de Lentidão - mantido) ...
            if powerup_ativo_lentidao and tempo_agora > tempo_fim_lentidao:
                velocidade_restaurada = velocidade_base_cobra + (pontuacao // 3) 
                velocidade_atual_cobra = min(velocidade_restaurada, int(velocidade_base_cobra * 2.5))
                powerup_ativo_lentidao = False

            # Só move se houver uma mudança definida (seja pelo jogador ou IA)
            # Ou se a IA estiver ativa e não houver mudança (ela pode ter decidido parar, mas o jogo continua)
            if not (snake_x_change == 0 and snake_y_change == 0) or ai_controle_ativo :
                 snake_x += snake_x_change; snake_y += snake_y_change

            # ... (Colisões, coleta de comida/powerup - lógica principal mantida, com pequenas adaptações) ...
            # Colisão com paredes
            if snake_x >= largura_tela or snake_x < 0 or snake_y >= altura_tela or snake_y < 0:
                if som_game_over: pygame.mixer.Sound.play(som_game_over)
                if pontuacao > recorde_atual: recorde_atual = pontuacao; salvar_recorde(recorde_atual)
                estado_atual = ESTADO_FIM_DE_JOGO
            
            # Colisão com obstáculos
            if [snake_x, snake_y] in lista_obstaculos:
                if som_game_over: pygame.mixer.Sound.play(som_game_over)
                if pontuacao > recorde_atual: recorde_atual = pontuacao; salvar_recorde(recorde_atual)
                estado_atual = ESTADO_FIM_DE_JOGO

            if estado_atual == ESTADO_JOGANDO: 
                cabeca_cobra = [snake_x, snake_y]
                # Verifica se a cabeça já está na lista (acontece se a IA/jogador não define x_change/y_change)
                # Evita adicionar segmentos duplicados se a cobra estiver parada mas o jogo rodando.
                if not lista_cobra or lista_cobra[-1] != cabeca_cobra : # Adiciona só se for uma nova posição
                    lista_cobra.append(cabeca_cobra)

                if len(lista_cobra) > comprimento_cobra: del lista_cobra[0]

                # Colisão com o próprio corpo
                # Só checa se a cobra se moveu para uma nova posição OU se é controlada por IA e pode ter ficado parada
                if not (snake_x_change == 0 and snake_y_change == 0) or ai_controle_ativo: 
                    for segmento in lista_cobra[:-1]:
                        if segmento == cabeca_cobra:
                            if som_game_over: pygame.mixer.Sound.play(som_game_over)
                            if pontuacao > recorde_atual: recorde_atual = pontuacao; salvar_recorde(recorde_atual)
                            estado_atual = ESTADO_FIM_DE_JOGO; break
                
                if estado_atual == ESTADO_JOGANDO:
                    # Colisão com comida normal
                    if snake_x == comida_x and snake_y == comida_y:
                        if som_comer: pygame.mixer.Sound.play(som_comer)
                        comida_x_nova, comida_y_nova = gerar_posicao_aleatoria_livre(lista_cobra, lista_obstaculos, None, powerup_atual_obj)
                        comida_x, comida_y = comida_x_nova, comida_y_nova
                        comprimento_cobra += 1; pontuacao += 1; comidas_normais_coletadas +=1

                        if not powerup_ativo_lentidao:
                            if pontuacao % 3 == 0: 
                                velocidade_atual_cobra = min(velocidade_atual_cobra + 1, int(velocidade_base_cobra * 2.5))
                        
                        if comidas_normais_coletadas >= PONTOS_PARA_GERAR_POWERUP and not powerup_atual_obj:
                            comidas_normais_coletadas = 0
                            tipo_powerup_novo = random.choice([POWERUP_SLOW_SNAKE, POWERUP_BONUS_POINTS])
                            px, py = gerar_posicao_aleatoria_livre(lista_cobra, lista_obstaculos, [comida_x, comida_y], None)
                            powerup_atual_obj = {'x': px, 'y': py, 'tipo': tipo_powerup_novo}

                    # Colisão com power-up
                    if powerup_atual_obj and snake_x == powerup_atual_obj['x'] and snake_y == powerup_atual_obj['y']:
                        if som_powerup: pygame.mixer.Sound.play(som_powerup)
                        if powerup_atual_obj['tipo'] == POWERUP_SLOW_SNAKE:
                            if not powerup_ativo_lentidao: 
                                velocidade_atual_cobra = max(3, velocidade_base_cobra // 2) 
                                powerup_ativo_lentidao = True
                                tempo_fim_lentidao = tempo_agora + DURACAO_POWERUP_SLOW
                        elif powerup_atual_obj['tipo'] == POWERUP_BONUS_POINTS:
                            pontuacao += PONTOS_DO_POWERUP_BONUS
                        powerup_atual_obj = None

        # --- Desenho na Tela ---
        tela.fill(COR_FUNDO)
        if estado_atual == ESTADO_MENU_PRINCIPAL:
            # ... (desenho do menu mantido)
            mostrar_texto_centralizado("Cobrinha com IA", fonte_titulo_menu, COR_TEXTO_MENU, -150) # Título atualizado
            for i, opcao_texto in enumerate(opcoes_menu):
                cor = COR_TEXTO_MENU_SELECIONADO if i == opcao_selecionada_menu else COR_TEXTO_MENU
                mostrar_texto_centralizado(opcao_texto, fonte_menu, cor, -50 + i * 60)
            mostrar_texto("Use ↑ ↓ e ENTER", fonte_info, (100,100,100), 10, altura_tela - 40)

        elif estado_atual == ESTADO_TELA_RECORDE:
            # ... (desenho da tela de recorde mantido)
            mostrar_texto_centralizado("Maior Pontuação", fonte_titulo_menu, COR_TEXTO_RECORDE, -100)
            mostrar_texto_centralizado(str(recorde_atual), fonte_titulo_menu, COR_TEXTO_RECORDE, 0)
            mostrar_texto_centralizado("Pressione ENTER ou ESC para voltar", fonte_info, COR_TEXTO_MENU, 150)

        elif estado_atual == ESTADO_JOGANDO or estado_atual == ESTADO_PAUSADO:
            desenhar_obstaculos(lista_obstaculos)
            desenhar_comida(comida_x, comida_y)
            if powerup_atual_obj: desenhar_powerup(powerup_atual_obj)
            if lista_cobra : desenhar_cobra(lista_cobra, direcao_atual) # Só desenha se existir
            mostrar_hud_jogo(pontuacao, recorde_atual, ai_controle_ativo) # Passa status da IA
            if estado_atual == ESTADO_PAUSADO:
                s = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
                s.fill((0,0,0,128)); tela.blit(s, (0,0))
                mostrar_texto_centralizado("PAUSADO", fonte_titulo_menu, COR_TEXTO_PAUSA, -50)
                mostrar_texto_centralizado("Pressione P ou ESC para continuar", fonte_info, COR_TEXTO_PAUSA, 50)
                if ai_controle_ativo:
                     mostrar_texto_centralizado("IA está em PAUSA", fonte_info, COR_TEXTO_AI_STATUS, 100)


        elif estado_atual == ESTADO_FIM_DE_JOGO:
            # ... (desenho da tela de game over mantido)
            mostrar_texto_centralizado("Você Perdeu!", fonte_titulo_menu, COR_TEXTO_GAMEOVER, -100)
            if ai_controle_ativo: # Mensagem se a IA estava jogando
                mostrar_texto_centralizado("(IA jogando)", fonte_info, COR_TEXTO_AI_STATUS, -60)
            mostrar_texto_centralizado(f"Pontuação Final: {pontuacao}", fonte_menu, COR_TEXTO_PONTUACAO, 0)
            if pontuacao >= recorde_atual and pontuacao > 0 :
                 mostrar_texto_centralizado("NOVO RECORDE!", fonte_menu, COR_TEXTO_RECORDE, 50)
            else:
                 mostrar_texto_centralizado(f"Recorde Atual: {recorde_atual}", fonte_info, COR_TEXTO_RECORDE, 50)
            mostrar_texto_centralizado("C-Jogar Novamente  |  Q-Menu Principal", fonte_info, COR_TEXTO_MENU, 150)
        
        if estado_atual != ESTADO_SAIR:
            pygame.display.update()
            if estado_atual == ESTADO_JOGANDO: fps_aplicado = velocidade_atual_cobra 
            else: fps_aplicado = 15 
            relogio.tick(fps_aplicado)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()