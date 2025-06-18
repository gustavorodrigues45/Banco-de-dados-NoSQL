# -*- coding: utf-8 -*-

import pygame
import time
import random
import sys
import os
import uuid
from collections import deque
from cassandra.cluster import Cluster

# --- INÍCIO: LÓGICA DE CONEXÃO E OPERAÇÕES COM O CASSANDRA ---

CASSANDRA_CLUSTER = None
CASSANDRA_SESSION = None

def conectar_cassandra():
    """Tenta estabelecer uma conexão com o cluster Cassandra."""
    global CASSANDRA_CLUSTER, CASSANDRA_SESSION
    if CASSANDRA_SESSION and not CASSANDRA_CLUSTER.is_shutdown:
        return
    try:
        print("Conectando ao Cassandra em 127.0.0.1...")
        cluster = Cluster(['127.0.0.1'])
        session = cluster.connect('jogo_cobra')
        CASSANDRA_CLUSTER = cluster
        CASSANDRA_SESSION = session
        print("Conexão com Cassandra estabelecida com sucesso.")
    except Exception as e:
        print(f"ERRO CRÍTICO: Não foi possível conectar ao Cassandra. {e}")
        print("Verifique se o contêiner Docker do Cassandra está em execução.")
        CASSANDRA_CLUSTER = None
        CASSANDRA_SESSION = None

def desconectar_cassandra():
    """Encerra a conexão com o Cassandra."""
    if CASSANDRA_CLUSTER and not CASSANDRA_CLUSTER.is_shutdown:
        CASSANDRA_CLUSTER.shutdown()
        print("Conexão com Cassandra encerrada.")

def inserir_pontuacao(nome, pontuacao):
    """Insere o nome e a pontuação de um jogador no ranking."""
    if not CASSANDRA_SESSION:
        print("Falha ao inserir: Sem sessão com Cassandra.")
        return
    try:
        query = "INSERT INTO ranking_geral (particao, nome, pontuacao, id) VALUES (%s, %s, %s, %s)"
        CASSANDRA_SESSION.execute(query, ('ranking', nome, pontuacao, uuid.uuid1()))
        print(f"Pontuação de {pontuacao} para o jogador {nome} inserida com sucesso.")
    except Exception as e: 
        print(f"Erro ao inserir pontuação no Cassandra: {e}")

def buscar_top_jogadores():
    """Busca TODOS os jogadores com as maiores pontuações, sem limite."""
    if not CASSANDRA_SESSION:
        return []
    try:
        query = "SELECT nome, pontuacao FROM ranking_geral WHERE particao = 'ranking'"
        rows = CASSANDRA_SESSION.execute(query)
        return list(rows)
    except Exception as e:
        print(f"Erro ao buscar ranking do Cassandra: {e}")
        return []

def buscar_jogador_por_nome(nome_busca):
    """
    Busca jogadores cujo nome contenha o termo de busca (insensível a maiúsculas/minúsculas).
    """
    if not CASSANDRA_SESSION:
        return []
    termo_busca_lower = nome_busca.lower()
    resultados_encontrados = []
    try:
        query = "SELECT nome, pontuacao FROM ranking_geral WHERE particao = 'ranking'"
        todos_jogadores = CASSANDRA_SESSION.execute(query)
        for jogador in todos_jogadores:
            if termo_busca_lower in jogador.nome.lower():
                resultados_encontrados.append(jogador)
        return sorted(resultados_encontrados, key=lambda r: r.pontuacao, reverse=True)
    except Exception as e:
        print(f"Erro ao buscar jogador no Cassandra: {e}")
        return []

# --- FIM: LÓGICA DO CASSANDRA ---


pygame.init()
pygame.mixer.init()

# --- Configurações Visuais ---
COR_FUNDO = (152, 251, 152)
COR_COBRA_CORPO = (0, 128, 0)
COR_COBRA_CONTORNO = (0, 100, 0)
COR_CABECA = (0, 150, 0)
COR_OLHOS = (255, 255, 255)
COR_PUPILAS = (0, 0, 0)
COR_COMIDA_MACA = (255, 0, 0)
COR_OBSTACULO = (100, 100, 100)
COR_TEXTO_PONTUACAO = (50, 50, 50)
COR_TEXTO_GAMEOVER = (200, 0, 0)
COR_TEXTO_MENU = (70, 70, 70)
COR_TEXTO_MENU_SELECIONADO = (0, 0, 200)
COR_TEXTO_PAUSA = (0, 0, 128)
COR_TEXTO_RANKING = (218, 165, 32)
COR_TEXTO_AI_STATUS = (200, 100, 0)
COR_INPUT_BOX = (255, 255, 255)
COR_INPUT_TEXTO = (0, 0, 0)

# --- Dimensões e Tela ---
largura_tela = 800
altura_tela = 600
tela = pygame.display.set_mode((largura_tela, altura_tela))
pygame.display.set_caption('Jogo da Cobrinha com Ranking em Cassandra')

# --- Controle de Jogo ---
relogio = pygame.time.Clock()
tamanho_bloco = 20
velocidade_base_cobra = 10
NUM_OBSTACULOS = 7

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

# --- Carregar Sons ---
som_comer, som_game_over = None, None
if os.path.exists("eat_sound.wav"): som_comer = pygame.mixer.Sound("eat_sound.wav")
if os.path.exists("game_over_sound.wav"): som_game_over = pygame.mixer.Sound("game_over_sound.wav")

# --- Constantes de Direção ---
DIR_DIREITA, DIR_ESQUERDA, DIR_CIMA, DIR_BAIXO = "DIREITA", "ESQUERDA", "CIMA", "BAIXO"
MOVIMENTOS_POSSIVEIS = {
    DIR_CIMA: (0, -tamanho_bloco, DIR_CIMA),
    DIR_BAIXO: (0, tamanho_bloco, DIR_BAIXO),
    DIR_ESQUERDA: (-tamanho_bloco, 0, DIR_ESQUERDA),
    DIR_DIREITA: (tamanho_bloco, 0, DIR_DIREITA),
}
OPPOSTOS = {DIR_CIMA: DIR_BAIXO, DIR_BAIXO: DIR_CIMA, DIR_ESQUERDA: DIR_DIREITA, DIR_DIREITA: DIR_ESQUERDA}

# --- Estados do Jogo ---
ESTADO_MENU_PRINCIPAL = "MENU_PRINCIPAL"
ESTADO_JOGANDO = "JOGANDO"
ESTADO_PAUSADO = "PAUSADO"
ESTADO_FIM_DE_JOGO = "FIM_DE_JOGO"
ESTADO_TELA_RANKING = "TELA_RANKING"
ESTADO_TELA_BUSCA = "TELA_BUSCA"
ESTADO_SAIR = "SAIR"

# --- Funções de Desenho e Lógica ---
def mostrar_texto(texto, fonte, cor, x, y, superficie=tela):
    render = fonte.render(texto, True, cor)
    superficie.blit(render, (x, y))

def mostrar_texto_centralizado(texto, fonte, cor, y_offset=0, superficie=tela):
    render = fonte.render(texto, True, cor)
    rect = render.get_rect(center=(largura_tela / 2, altura_tela / 2 + y_offset))
    superficie.blit(render, rect)

def desenhar_bloco(cor, x, y):
    pygame.draw.rect(tela, cor, [x, y, tamanho_bloco, tamanho_bloco], border_radius=4)

def desenhar_comida(x, y):
    raio_maca = int(tamanho_bloco / 2)
    pygame.draw.circle(tela, COR_COMIDA_MACA, (x + raio_maca, y + raio_maca), raio_maca)

def desenhar_cobra(lista_cobra):
    for x, y in lista_cobra:
        pygame.draw.rect(tela, COR_COBRA_CONTORNO, [x, y, tamanho_bloco, tamanho_bloco], border_radius=6)
        pygame.draw.rect(tela, COR_COBRA_CORPO, [x + 2, y + 2, tamanho_bloco - 4, tamanho_bloco - 4], border_radius=6)

def gerar_posicao_aleatoria_livre(lista_cobra, lista_obstaculos):
    while True:
        x = round(random.randrange(0, largura_tela - tamanho_bloco) / tamanho_bloco) * tamanho_bloco
        y = round(random.randrange(0, altura_tela - tamanho_bloco) / tamanho_bloco) * tamanho_bloco
        if [x, y] not in lista_cobra and [x, y] not in lista_obstaculos:
            return x, y

def inicializar_variaveis_jogo():
    snake_x = round((largura_tela / 2) / tamanho_bloco) * tamanho_bloco
    snake_y = round((altura_tela / 2) / tamanho_bloco) * tamanho_bloco
    direcao_atual = DIR_DIREITA
    lista_cobra = [[snake_x, snake_y]]
    comprimento_cobra = 1
    pontuacao = 0
    ai_controle_ativo = False
    velocidade_atual_cobra = velocidade_base_cobra
    lista_obstaculos = []
    for _ in range(NUM_OBSTACULOS):
        obs_x, obs_y = gerar_posicao_aleatoria_livre(lista_cobra, lista_obstaculos)
        lista_obstaculos.append([obs_x, obs_y])
    comida_x, comida_y = gerar_posicao_aleatoria_livre(lista_cobra, lista_obstaculos)
    return (direcao_atual, lista_cobra, comprimento_cobra, pontuacao,
            ai_controle_ativo, velocidade_atual_cobra, lista_obstaculos, comida_x, comida_y)

# --- Lógica da Inteligência Artificial ---
def bfs_find_path(start_pos, target_pos, snake_list, obstacles_list):
    queue = deque([[start_pos, []]])
    visited = {tuple(start_pos)}
    while queue:
        current_pos, path = queue.popleft()
        if current_pos == target_pos:
            return path
        for move_name, (dx, dy, _) in MOVIMENTOS_POSSIVEIS.items():
            next_x, next_y = current_pos[0] + dx, current_pos[1] + dy
            if not (0 <= next_x < largura_tela and 0 <= next_y < altura_tela) or \
               [next_x, next_y] in obstacles_list or \
               [next_x, next_y] in snake_list[:-1] or \
               (next_x, next_y) in visited:
                continue
            visited.add((next_x, next_y))
            queue.append([[next_x, next_y], path + [move_name]])
    return None

def get_ai_move(snake_list, current_direction, food_pos, obstacles_list):
    head_pos = snake_list[-1]
    path_to_food = bfs_find_path(head_pos, food_pos, snake_list, obstacles_list)
    if path_to_food:
        return path_to_food[0]
    safe_moves = []
    for move_name, (dx, dy, _) in MOVIMENTOS_POSSIVEIS.items():
        if move_name == OPPOSTOS.get(current_direction) and len(snake_list) > 1:
            continue
        next_x, next_y = head_pos[0] + dx, head_pos[1] + dy
        if (0 <= next_x < largura_tela and 0 <= next_y < altura_tela and
            [next_x, next_y] not in obstacles_list and
            [next_x, next_y] not in snake_list[:-1]):
            safe_moves.append(move_name)
    return random.choice(safe_moves) if safe_moves else current_direction

# --- Loop Principal e Gerenciador de Estados ---
def main():
    conectar_cassandra()

    estado_atual = ESTADO_MENU_PRINCIPAL
    rodando = True
    
    opcoes_menu = ["Iniciar Jogo", "Ranking", "Buscar Jogador", "Sair"]
    opcao_selecionada_menu = 0
    
    nome_jogador = ""
    input_ativo = False
    pontuacao_final_partida = 0
    ranking_data = []
    scroll_y = 0
    busca_data = []
    busca_realizada = False
    
    (direcao_atual, lista_cobra, comprimento_cobra, pontuacao, ai_controle_ativo, 
     velocidade_atual_cobra, lista_obstaculos, comida_x, comida_y) = (DIR_DIREITA, [], 1, 0, False, 0, [], 0, 0)

    while rodando:
        # --- PROCESSAMENTO DE EVENTOS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                rodando = False

            if estado_atual == ESTADO_MENU_PRINCIPAL:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        opcao_selecionada_menu = (opcao_selecionada_menu - 1) % len(opcoes_menu)
                    elif event.key == pygame.K_DOWN:
                        opcao_selecionada_menu = (opcao_selecionada_menu + 1) % len(opcoes_menu)
                    elif event.key == pygame.K_RETURN:
                        if opcao_selecionada_menu == 0: # Iniciar Jogo
                            (direcao_atual, lista_cobra, comprimento_cobra, pontuacao, ai_controle_ativo, 
                             velocidade_atual_cobra, lista_obstaculos, comida_x, comida_y) = inicializar_variaveis_jogo()
                            estado_atual = ESTADO_JOGANDO
                        elif opcao_selecionada_menu == 1: # Ranking
                            ranking_data = buscar_top_jogadores()
                            scroll_y = 0
                            estado_atual = ESTADO_TELA_RANKING
                        elif opcao_selecionada_menu == 2: # Buscar Jogador
                            nome_jogador = ""
                            input_ativo = True
                            busca_realizada = False
                            busca_data = []
                            estado_atual = ESTADO_TELA_BUSCA
                        elif opcao_selecionada_menu == 3: # Sair
                            rodando = False
            
            elif estado_atual == ESTADO_JOGANDO:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p: estado_atual = ESTADO_PAUSADO
                    elif event.key == pygame.K_a: ai_controle_ativo = not ai_controle_ativo
                    if not ai_controle_ativo:
                        if event.key == pygame.K_LEFT and direcao_atual != DIR_DIREITA: direcao_atual = DIR_ESQUERDA
                        elif event.key == pygame.K_RIGHT and direcao_atual != DIR_ESQUERDA: direcao_atual = DIR_DIREITA
                        elif event.key == pygame.K_UP and direcao_atual != DIR_BAIXO: direcao_atual = DIR_CIMA
                        elif event.key == pygame.K_DOWN and direcao_atual != DIR_CIMA: direcao_atual = DIR_BAIXO

            elif estado_atual == ESTADO_PAUSADO:
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_p or event.key == pygame.K_ESCAPE):
                    estado_atual = ESTADO_JOGANDO

            elif estado_atual == ESTADO_FIM_DE_JOGO:
                if input_ativo and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if nome_jogador.strip():
                            inserir_pontuacao(nome_jogador.strip(), pontuacao_final_partida)
                        input_ativo = False
                        estado_atual = ESTADO_MENU_PRINCIPAL
                    elif event.key == pygame.K_BACKSPACE:
                        nome_jogador = nome_jogador[:-1]
                    else:
                        nome_jogador += event.unicode
            
            elif estado_atual == ESTADO_TELA_RANKING:
                # --- Lógica de Input da Rolagem ---
                line_height = 40
                top_margin = 100
                bottom_margin = 100
                visible_area_height = altura_tela - top_margin - bottom_margin
                total_content_height = len(ranking_data) * line_height
                max_scroll = max(0, total_content_height - visible_area_height)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4: # Roda do mouse para cima
                        scroll_y = max(scroll_y - 20, 0)
                    elif event.button == 5: # Roda do mouse para baixo
                        scroll_y = min(scroll_y + 20, max_scroll)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                         scroll_y = max(scroll_y - 20, 0)
                    if event.key == pygame.K_DOWN:
                         scroll_y = min(scroll_y + 20, max_scroll)
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                        estado_atual = ESTADO_MENU_PRINCIPAL

            elif estado_atual == ESTADO_TELA_BUSCA:
                if event.type == pygame.KEYDOWN:
                    if input_ativo:
                        if event.key == pygame.K_RETURN:
                            if nome_jogador.strip():
                                busca_data = buscar_jogador_por_nome(nome_jogador.strip())
                            busca_realizada = True
                            input_ativo = False
                        elif event.key == pygame.K_BACKSPACE:
                            nome_jogador = nome_jogador[:-1]
                        else:
                            nome_jogador += event.unicode
                    elif event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                        estado_atual = ESTADO_MENU_PRINCIPAL
        
        # --- LÓGICA DE ATUALIZAÇÃO DE ESTADOS ---
        if estado_atual == ESTADO_JOGANDO:
            if ai_controle_ativo:
                direcao_atual = get_ai_move(lista_cobra, direcao_atual, [comida_x, comida_y], lista_obstaculos)
            dx, dy, _ = MOVIMENTOS_POSSIVEIS[direcao_atual]
            cabeca_x, cabeca_y = lista_cobra[-1][0] + dx, lista_cobra[-1][1] + dy
            game_over = False
            if (cabeca_x >= largura_tela or cabeca_x < 0 or cabeca_y >= altura_tela or cabeca_y < 0 or
                [cabeca_x, cabeca_y] in lista_obstaculos or [cabeca_x, cabeca_y] in lista_cobra):
                game_over = True
            if game_over:
                if som_game_over: som_game_over.play()
                pontuacao_final_partida = pontuacao
                nome_jogador = "IA" if ai_controle_ativo else ""
                input_ativo = not ai_controle_ativo
                estado_atual = ESTADO_FIM_DE_JOGO
                if ai_controle_ativo and pontuacao_final_partida > 0:
                    inserir_pontuacao(nome_jogador, pontuacao_final_partida)
                    estado_atual = ESTADO_MENU_PRINCIPAL
            else:
                lista_cobra.append([cabeca_x, cabeca_y])
                if cabeca_x == comida_x and cabeca_y == comida_y:
                    if som_comer: som_comer.play()
                    comprimento_cobra += 1
                    pontuacao += 1
                    if pontuacao % 5 == 0: velocidade_atual_cobra = min(30, velocidade_atual_cobra + 1)
                    comida_x, comida_y = gerar_posicao_aleatoria_livre(lista_cobra, lista_obstaculos)
                if len(lista_cobra) > comprimento_cobra:
                    del lista_cobra[0]

        # --- DESENHO NA TELA ---
        tela.fill(COR_FUNDO)

        if estado_atual == ESTADO_MENU_PRINCIPAL:
            mostrar_texto_centralizado("Cobrinha com Cassandra", fonte_titulo_menu, COR_TEXTO_MENU, -150)
            for i, opcao in enumerate(opcoes_menu):
                cor = COR_TEXTO_MENU_SELECIONADO if i == opcao_selecionada_menu else COR_TEXTO_MENU
                mostrar_texto_centralizado(opcao, fonte_menu, cor, -50 + i * 60)
            if not CASSANDRA_SESSION:
                 mostrar_texto("AVISO: Não conectado ao Banco de Dados", fonte_info, COR_TEXTO_GAMEOVER, 10, altura_tela - 40)

        elif estado_atual in [ESTADO_JOGANDO, ESTADO_PAUSADO]:
            for x, y in lista_obstaculos: desenhar_bloco(COR_OBSTACULO, x, y)
            desenhar_comida(comida_x, comida_y)
            desenhar_cobra(lista_cobra)
            mostrar_texto(f"Pontuação: {pontuacao}", fonte_score, COR_TEXTO_PONTUACAO, 10, 10)
            if ai_controle_ativo:
                mostrar_texto("IA ATIVA (A)", fonte_info, COR_TEXTO_AI_STATUS, largura_tela - 160, 10)
            if estado_atual == ESTADO_PAUSADO:
                s = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
                s.fill((0, 0, 0, 128))
                tela.blit(s, (0, 0))
                mostrar_texto_centralizado("PAUSADO", fonte_titulo_menu, COR_TEXTO_PAUSA, -50)
                mostrar_texto_centralizado("Pressione P ou ESC para continuar", fonte_info, COR_TEXTO_PAUSA, 50)
        
        elif estado_atual == ESTADO_FIM_DE_JOGO:
            mostrar_texto_centralizado("Fim de Jogo!", fonte_titulo_menu, COR_TEXTO_GAMEOVER, -200)
            mostrar_texto_centralizado(f"Sua Pontuação: {pontuacao_final_partida}", fonte_menu, COR_TEXTO_PONTUACAO, -100)
            if input_ativo:
                mostrar_texto_centralizado("Digite seu nome e pressione ENTER para salvar:", fonte_info, COR_TEXTO_MENU, -20)
                input_rect = pygame.Rect(largura_tela/2 - 200, altura_tela/2, 400, 50)
                pygame.draw.rect(tela, COR_INPUT_BOX, input_rect)
                pygame.draw.rect(tela, COR_TEXTO_MENU, input_rect, 2)
                texto_render = fonte_menu.render(nome_jogador, True, COR_INPUT_TEXTO)
                tela.blit(texto_render, (input_rect.x + 10, input_rect.y + 5))
        
        elif estado_atual == ESTADO_TELA_RANKING:
            line_height = 40
            top_margin = 100
            bottom_margin = 100
            visible_area_height = altura_tela - top_margin - bottom_margin
            total_content_height = len(ranking_data) * line_height
            max_scroll = max(0, total_content_height - visible_area_height)

            mostrar_texto_centralizado("Ranking Global", fonte_titulo_menu, COR_TEXTO_RANKING, -250)
            if ranking_data:
                for i, jogador in enumerate(ranking_data):
                    item_y = top_margin + (i * line_height) - scroll_y
                    if top_margin <= item_y < altura_tela - bottom_margin:
                        texto = f"{i+1: >2}. {jogador.nome:<20} - {jogador.pontuacao} Pontos"
                        mostrar_texto(texto, fonte_info, COR_TEXTO_PONTUACAO, 180, item_y)
                if max_scroll > 0:
                    scrollbar_track_rect = pygame.Rect(largura_tela - 25, top_margin, 15, visible_area_height)
                    pygame.draw.rect(tela, (200, 200, 200), scrollbar_track_rect)
                    thumb_height = max(20, (visible_area_height / total_content_height) * visible_area_height)
                    thumb_y_pos = top_margin + (scroll_y / max_scroll) * (visible_area_height - thumb_height)
                    scrollbar_thumb_rect = pygame.Rect(largura_tela - 25, thumb_y_pos, 15, thumb_height)
                    pygame.draw.rect(tela, (100, 100, 100), scrollbar_thumb_rect)
            else:
                msg = "Ranking vazio." if CASSANDRA_SESSION else "Não foi possível carregar o ranking."
                mostrar_texto_centralizado(msg, fonte_menu, COR_TEXTO_PONTUACAO, -100)
            mostrar_texto_centralizado("Use a roda do mouse ou as setas para rolar", fonte_info, COR_TEXTO_MENU, 250)
            mostrar_texto_centralizado("Pressione ENTER ou ESC para voltar", fonte_info, COR_TEXTO_MENU, 280)

        elif estado_atual == ESTADO_TELA_BUSCA:
            mostrar_texto_centralizado("Buscar Jogador", fonte_titulo_menu, COR_TEXTO_MENU, -250)
            prompt = "Digite o nome e pressione ENTER" if input_ativo else "Pressione ENTER ou ESC para voltar"
            mostrar_texto_centralizado(prompt, fonte_info, COR_TEXTO_MENU, 250)
            input_rect = pygame.Rect(largura_tela/2 - 200, altura_tela/2 - 150, 400, 50)
            pygame.draw.rect(tela, COR_INPUT_BOX, input_rect)
            pygame.draw.rect(tela, COR_TEXTO_MENU, input_rect, 2)
            texto_render = fonte_menu.render(nome_jogador, True, COR_INPUT_TEXTO)
            tela.blit(texto_render, (input_rect.x + 10, input_rect.y + 5))
            if busca_realizada:
                if busca_data:
                    mostrar_texto_centralizado(f"Resultados para '{nome_jogador}':", fonte_menu, COR_TEXTO_PONTUACAO, -50)
                    for i, resultado in enumerate(busca_data[:5]): 
                        texto = f"{resultado.nome}: {resultado.pontuacao} Pontos"
                        mostrar_texto_centralizado(texto, fonte_info, COR_TEXTO_PONTUACAO, 0 + i * 40)
                else:
                    mostrar_texto_centralizado(f"Nenhum resultado encontrado para '{nome_jogador}'.", fonte_menu, COR_TEXTO_GAMEOVER, 0)

        pygame.display.update()
        fps = velocidade_atual_cobra if estado_atual == ESTADO_JOGANDO else 30
        relogio.tick(fps)

    desconectar_cassandra()
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()