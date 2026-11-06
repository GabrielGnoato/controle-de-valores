"""Gráficos futuristas desenhados direto em um tkinter.Canvas.
 
Não depende de matplotlib nem de nenhuma biblioteca extra.
Cada função recebe o canvas e os dados, limpa o canvas e redesenha tudo,
então pode ser chamada de novo sempre que a janela mudar de tamanho.
"""
 
import math
from bisect import bisect_right
 
# PALETA NEON
FUNDO_GRAFICO = "#0B1220"
GRADE = "#1C2A45"
EIXO = "#7C8DB0"
TEXTO_CLARO = "#E2E8F0"
CIANO = "#22D3EE"
VERDE_NEON = "#34D399"
ROSA_NEON = "#FB7185"
ROXO_NEON = "#A78BFA"
 
FONTE = "Consolas"
 
 
# ---------------------------------------------------------------
# UTILITÁRIOS
# ---------------------------------------------------------------
 
def misturar(cor_a, cor_b, t):
    """Mistura duas cores hex. t=0 devolve cor_a, t=1 devolve cor_b."""
    t = max(0.0, min(1.0, t))
    a = [int(cor_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(cor_b[i:i + 2], 16) for i in (1, 3, 5)]
    r, g, bl = (round(x + (y - x) * t) for x, y in zip(a, b))
    return f"#{r:02x}{g:02x}{bl:02x}"
 
 
def neon(cor, intensidade):
    """A cor 'apagada' sobre o fundo escuro (usada para brilho/glow)."""
    return misturar(FUNDO_GRAFICO, cor, intensidade)
 
 
def abreviar(valor):
    """1234 -> 1,2k | 2500000 -> 2,5M | -300 -> -300"""
    absoluto = abs(valor)
    sinal = "-" if valor < 0 else ""
 
    if absoluto >= 1_000_000:
        texto = f"{absoluto / 1_000_000:.1f}M"
    elif absoluto >= 1_000:
        texto = f"{absoluto / 1_000:.1f}k"
    else:
        texto = f"{absoluto:.0f}"
 
    return sinal + texto.replace(".0", "").replace(".", ",")
 
 
def _marcas(minimo, maximo, quantidade=4):
    """Valores 'redondos' para as linhas de grade do eixo Y."""
    if maximo <= minimo:
        maximo = minimo + 1
 
    bruto = (maximo - minimo) / quantidade
    magnitude = 10 ** math.floor(math.log10(bruto))
 
    passo = magnitude * 10
    for multiplo in (1, 2, 2.5, 5, 10):
        if multiplo * magnitude >= bruto:
            passo = multiplo * magnitude
            break
 
    inicio = math.floor(minimo / passo) * passo
    fim = math.ceil(maximo / passo) * passo
 
    marcas = []
    atual = inicio
 
    while atual <= fim + passo / 2:
        marcas.append(round(atual, 6))
        atual += passo
 
    return marcas
 
 
def _tamanho(canvas):
    return canvas.winfo_width(), canvas.winfo_height()
 
 
def _vazio(canvas, largura, altura, texto="SEM DADOS NO PERÍODO"):
    canvas.create_text(
        largura / 2, altura / 2,
        text=texto, fill=EIXO, font=(FONTE, 11, "bold")
    )
 
 
def _grade(canvas, marcas, y_de, x0, x1):
    for marca in marcas:
        y = y_de(marca)
        eh_zero = abs(marca) < 1e-9
 
        canvas.create_line(
            x0, y, x1, y,
            fill=misturar(GRADE, EIXO, 0.45) if eh_zero else GRADE,
            width=1,
            dash=() if eh_zero else (2, 5)
        )
        canvas.create_text(
            x0 - 8, y,
            text=abreviar(marca), fill=EIXO,
            font=(FONTE, 9), anchor="e"
        )
 
 
def _rotulos_x(canvas, rotulos, xs, y, largura):
    quantidade = len(rotulos)
    maximo = max(2, int(largura / 46))
    passo = max(1, math.ceil(quantidade / maximo))
 
    for i in range(0, quantidade, passo):
        canvas.create_text(
            xs[i], y, text=rotulos[i],
            fill=EIXO, font=(FONTE, 9)
        )
 
 
def _legenda(canvas, itens, x_fim, y):
    """Legenda alinhada à direita: [(texto, cor), ...]"""
    x = x_fim
 
    for texto, cor in reversed(itens):
        canvas.create_text(
            x, y, text=texto, fill=EIXO,
            font=(FONTE, 9, "bold"), anchor="e"
        )
        x -= len(texto) * 7 + 6
        canvas.create_rectangle(
            x - 8, y - 4, x, y + 4, fill=cor, outline=""
        )
        x -= 22
 
 
# ---------------------------------------------------------------
# 1) BARRAS: ENTRADAS x SAÍDAS
# ---------------------------------------------------------------
 
def _barra_vertical(canvas, xa, y_topo, xb, y_base, cor):
    altura = y_base - y_topo
 
    if altura < 2:
        y_topo = y_base - 2
        altura = 2
 
    # brilho
    canvas.create_rectangle(
        xa - 2, y_topo - 2, xb + 2, y_base,
        fill=neon(cor, 0.14), outline=""
    )
 
    fatias = max(1, min(8, int(altura // 3)))
 
    for k in range(fatias):
        ya = y_topo + altura * k / fatias
        yb = y_topo + altura * (k + 1) / fatias
        canvas.create_rectangle(
            xa, ya, xb, yb,
            fill=misturar(cor, FUNDO_GRAFICO, 0.62 * k / fatias),
            outline=""
        )
 
    # tampa clara no topo
    canvas.create_line(
        xa, y_topo, xb, y_topo,
        fill=misturar(cor, "#FFFFFF", 0.5), width=2
    )
 
 
def grafico_barras(canvas, rotulos, entradas, saidas):
    largura, altura = _tamanho(canvas)
    canvas.delete("all")
 
    if largura < 80 or altura < 80:
        return
 
    maximo = max(list(entradas) + list(saidas), default=0)
 
    if not rotulos or maximo <= 0:
        _vazio(canvas, largura, altura)
        return
 
    x0, x1 = 54, largura - 16
    y0, y1 = 30, altura - 30
 
    marcas = _marcas(0, maximo)
    teto = marcas[-1]
 
    def y_de(valor):
        return y1 - (valor / teto) * (y1 - y0)
 
    _grade(canvas, marcas, y_de, x0, x1)
 
    quantidade = len(rotulos)
    faixa = (x1 - x0) / quantidade
    larg_barra = max(2, min(faixa * 0.34, 20))
 
    xs = [x0 + faixa * (i + 0.5) for i in range(quantidade)]
 
    for i, cx in enumerate(xs):
        if entradas[i] > 0:
            _barra_vertical(
                canvas, cx - larg_barra - 1, y_de(entradas[i]),
                cx - 1, y1, VERDE_NEON
            )
        if saidas[i] > 0:
            _barra_vertical(
                canvas, cx + 1, y_de(saidas[i]),
                cx + larg_barra + 1, y1, ROSA_NEON
            )
 
    _rotulos_x(canvas, rotulos, xs, y1 + 15, x1 - x0)
    _legenda(
        canvas,
        [("ENTRADAS", VERDE_NEON), ("SAÍDAS", ROSA_NEON)],
        x1, 12
    )
 
 
# ---------------------------------------------------------------
# 2) ÁREA: EVOLUÇÃO DO SALDO
# ---------------------------------------------------------------
 
def grafico_area(canvas, rotulos, valores, cor=CIANO):
    largura, altura = _tamanho(canvas)
    canvas.delete("all")
 
    if largura < 80 or altura < 80:
        return
 
    if not rotulos or all(abs(v) < 1e-9 for v in valores):
        _vazio(canvas, largura, altura)
        return
 
    x0, x1 = 54, largura - 20
    y0, y1 = 30, altura - 30
 
    marcas = _marcas(min(0, min(valores)), max(0, max(valores)))
    base_valor, teto_valor = marcas[0], marcas[-1]
 
    def y_de(valor):
        return y1 - (valor - base_valor) / (teto_valor - base_valor) * (y1 - y0)
 
    quantidade = len(rotulos)
 
    if quantidade == 1:
        xs = [(x0 + x1) / 2]
    else:
        xs = [x0 + (x1 - x0) * i / (quantidade - 1) for i in range(quantidade)]
 
    ys = [y_de(v) for v in valores]
    y_zero = y_de(0)
 
    # preenchimento em degradê (colunas finas que se apagam até o zero)
    if quantidade >= 2:
        for px in range(int(x0), int(x1), 3):
            xm = px + 1.5
            posicao = bisect_right(xs, xm)
            i = min(max(posicao - 1, 0), quantidade - 2)
            t = (xm - xs[i]) / (xs[i + 1] - xs[i])
            y = ys[i] + (ys[i + 1] - ys[i]) * max(0.0, min(1.0, t))
 
            if abs(y - y_zero) < 1:
                continue
 
            cor_area = cor if y < y_zero else ROSA_NEON
            passos = 8
 
            for k in range(passos):
                ya = y + (y_zero - y) * k / passos
                yb = y + (y_zero - y) * (k + 1) / passos
                intensidade = 0.45 * (1 - k / passos) + 0.03
                canvas.create_rectangle(
                    px, ya, px + 3, yb,
                    fill=neon(cor_area, intensidade), outline=""
                )
 
    _grade(canvas, marcas, y_de, x0, x1)
 
    # linha com brilho (3 camadas)
    if quantidade >= 2:
        pontos = [c for par in zip(xs, ys) for c in par]
 
        for espessura, intensidade in ((9, 0.14), (5, 0.32), (2, 1.0)):
            canvas.create_line(
                *pontos,
                fill=neon(cor, intensidade), width=espessura,
                capstyle="round", joinstyle="round"
            )
 
    # pontos
    if quantidade <= 31:
        for x, y in zip(xs, ys):
            canvas.create_oval(
                x - 2.5, y - 2.5, x + 2.5, y + 2.5,
                fill=FUNDO_GRAFICO, outline=cor, width=1.5
            )
 
    # ponto final em destaque com o valor atual
    x_final, y_final = xs[-1], ys[-1]
    canvas.create_oval(
        x_final - 9, y_final - 9, x_final + 9, y_final + 9,
        fill=neon(cor, 0.22), outline=""
    )
    canvas.create_oval(
        x_final - 4, y_final - 4, x_final + 4, y_final + 4,
        fill=cor, outline=""
    )
    canvas.create_text(
        x_final - 10, y_final - 14,
        text=abreviar(valores[-1]), fill=TEXTO_CLARO,
        font=(FONTE, 10, "bold"), anchor="e"
    )
 
    _rotulos_x(canvas, rotulos, xs, y1 + 15, x1 - x0)
    _legenda(canvas, [("SALDO ACUMULADO", cor)], x1, 12)
 
 
# ---------------------------------------------------------------
# 3) ROSCA: PROPORÇÃO ENTRADAS x SAÍDAS
# ---------------------------------------------------------------
 
def grafico_rosca(canvas, entradas, saidas, texto_centro, sub_centro, formatar):
    largura, altura = _tamanho(canvas)
    canvas.delete("all")
 
    if largura < 120 or altura < 100:
        return
 
    total = entradas + saidas
    raio = min(altura * 0.40, largura * 0.24)
    espessura = max(10, raio * 0.26)
    cx, cy = largura * 0.30, altura / 2
    r_arco = raio - espessura / 2
    caixa = (cx - r_arco, cy - r_arco, cx + r_arco, cy + r_arco)
 
    # trilho
    canvas.create_arc(
        *caixa, start=0, extent=359.9, style="arc",
        outline=GRADE, width=espessura
    )
 
    if total <= 0:
        canvas.create_text(
            cx, cy, text="SEM\nDADOS", fill=EIXO,
            font=(FONTE, 11, "bold"), justify="center"
        )
        return
 
    inicio = 90
 
    for valor, cor in ((entradas, VERDE_NEON), (saidas, ROSA_NEON)):
        if valor <= 0:
            continue
 
        extensao = -min(359.9, 360 * valor / total)
 
        for extra, intensidade in ((10, 0.12), (5, 0.26)):
            canvas.create_arc(
                *caixa, start=inicio, extent=extensao, style="arc",
                outline=neon(cor, intensidade), width=espessura + extra
            )
 
        canvas.create_arc(
            *caixa, start=inicio, extent=extensao, style="arc",
            outline=cor, width=espessura
        )
 
        inicio += extensao
 
    canvas.create_text(
        cx, cy - 8, text=texto_centro, fill=TEXTO_CLARO,
        font=(FONTE, 14, "bold")
    )
    canvas.create_text(
        cx, cy + 14, text=sub_centro, fill=EIXO,
        font=(FONTE, 9, "bold")
    )
 
    # legenda à direita
    x = cx + raio + 38
 
    for deslocamento, nome, valor, cor in (
        (-38, "ENTRADAS", entradas, VERDE_NEON),
        (22, "SAÍDAS", saidas, ROSA_NEON),
    ):
        y = cy + deslocamento
        canvas.create_rectangle(x, y - 5, x + 10, y + 5, fill=cor, outline="")
        canvas.create_text(
            x + 18, y, text=nome, fill=EIXO,
            font=(FONTE, 9, "bold"), anchor="w"
        )
        canvas.create_text(
            x, y + 20, text=formatar(valor), fill=TEXTO_CLARO,
            font=(FONTE, 12, "bold"), anchor="w"
        )
        canvas.create_text(
            x, y + 38, text=f"{valor / total * 100:.0f}% do movimento",
            fill=cor, font=(FONTE, 9), anchor="w"
        )
 
 
# ---------------------------------------------------------------
# 4) RANKING: MAIORES MOVIMENTAÇÕES
# ---------------------------------------------------------------
 
def grafico_ranking(canvas, itens, cor, formatar):
    largura, altura = _tamanho(canvas)
    canvas.delete("all")
 
    if largura < 120 or altura < 80:
        return
 
    itens = [(nome, valor) for nome, valor in itens if valor > 0][:5]
 
    if not itens:
        _vazio(canvas, largura, altura)
        return
 
    maximo = max(valor for _, valor in itens)
    esq, dir_, topo = 18, 18, 14
    altura_linha = min(48, (altura - topo - 6) / 5)
    largura_total = largura - esq - dir_
    limite_texto = max(8, int((largura - 170) / 7))
 
    for i, (nome, valor) in enumerate(itens):
        y = topo + i * altura_linha
 
        if len(nome) > limite_texto:
            nome = nome[:limite_texto - 1] + "…"
 
        canvas.create_text(
            esq, y + 8, text=f"{i + 1:02d}  {nome}",
            fill=TEXTO_CLARO, font=(FONTE, 10, "bold"), anchor="w"
        )
        canvas.create_text(
            largura - dir_, y + 8, text=formatar(valor),
            fill=cor, font=(FONTE, 10, "bold"), anchor="e"
        )
 
        y_barra, altura_barra = y + 22, 9
        comprimento = max(4, largura_total * valor / maximo)
 
        canvas.create_rectangle(
            esq, y_barra, esq + largura_total, y_barra + altura_barra,
            fill=GRADE, outline=""
        )
        canvas.create_rectangle(
            esq - 1, y_barra - 2, esq + comprimento + 1,
            y_barra + altura_barra + 2,
            fill=neon(cor, 0.14), outline=""
        )
 
        fatias = max(2, min(24, int(comprimento // 6)))
 
        for k in range(fatias):
            xa = esq + comprimento * k / fatias
            xb = esq + comprimento * (k + 1) / fatias
            canvas.create_rectangle(
                xa, y_barra, xb, y_barra + altura_barra,
                fill=misturar(
                    misturar(cor, FUNDO_GRAFICO, 0.6), cor,
                    (k + 1) / fatias
                ),
                outline=""
            )
 
        canvas.create_line(
            esq + comprimento, y_barra - 1,
            esq + comprimento, y_barra + altura_barra + 1,
            fill=misturar(cor, "#FFFFFF", 0.6), width=2
        )
 