import customtkinter as custom
import sqlite3
import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox

import graficos
from conexao import (
    criar_tabela,
    adicionar_lancamento,
    atualizar_lancamento,
    excluir_lancamento,
    buscar_lancamentos,
    obter_totais,
    totais_periodo,
    serie_periodo,
    top_por_descricao,
    listar_meses,
    resumo_mensal,
    exportar_mes,
    fechar_meses_encerrados
)


# CONFIGURAÇÕES VISUAIS
custom.set_appearance_mode("dark")
custom.set_default_color_theme("blue")

FUNDO = "#0F172A"
MENU = "#111827"
CARTAO = "#1E293B"
BORDA = "#334155"
TEXTO = "#F8FAFC"
TEXTO_SECUNDARIO = "#94A3B8"
VERDE = "#22C55E"
VERMELHO = "#F87171"
AZUL = "#2563EB"

# Dashboard (visual futurista)
CIANO = graficos.CIANO
FUNDO_NEON = graficos.FUNDO_GRAFICO
EIXO = graficos.EIXO
BORDA_NEON = graficos.misturar(BORDA, CIANO, 0.35)

MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]
MESES_ABREV = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez"
]

TODOS_OS_MESES = "Todos os meses"


# ---------------------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------------------

def formatar_moeda(valor):
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def converter_valor(texto):
    """Converte o texto digitado em número. Aceita 1500, 1500.50,
    1.500,50 e R$ 1.500,50. Retorna None se for inválido."""

    texto = texto.strip().replace("R$", "").replace(" ", "")

    if not texto:
        return None

    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")

    try:
        valor = float(texto)
    except ValueError:
        return None

    if valor != valor or valor in (float("inf"), float("-inf")):
        return None

    return round(valor, 2)


def converter_data(texto):
    """'04/11/2026' -> '2026-11-04'. Retorna None se for inválida."""

    texto = texto.strip().replace("-", "/").replace(".", "/")

    try:
        data = datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        return None

    if not 1990 <= data.year <= 2100:
        return None

    return data.isoformat()


def formatar_data(iso):
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return "--/--/----"


def nome_mes(ano_mes):
    """'2026-11' -> 'Novembro/2026'"""
    ano, mes = ano_mes.split("-")
    return f"{MESES[int(mes) - 1]}/{ano}"


def mes_atual():
    return date.today().strftime("%Y-%m")


def iniciar_app():

    criar_tabela()

    try:
        fechar_meses_encerrados()
    except (OSError, sqlite3.Error) as erro:
        print(f"Erro ao fechar meses encerrados: {erro}")

    # "mes" é o mês do Menu principal; vira sozinho na virada do mês
    estado = {"mes": mes_atual(), "tela": "visao"}

    # JANELA PRINCIPAL
    janela = custom.CTk()
    janela.geometry("1200x750")
    janela.minsize(1100, 650)
    janela.title("Finance Control")
    janela.configure(fg_color=FUNDO)

    janela.grid_columnconfigure(1, weight=1)
    janela.grid_rowconfigure(0, weight=1)

    # MENU LATERAL
    menu_lateral = custom.CTkFrame(
        janela,
        width=230,
        corner_radius=0,
        fg_color=MENU
    )
    menu_lateral.grid(
        row=0,
        column=0,
        sticky="nsew"
    )
    menu_lateral.grid_propagate(False)

    # IDENTIDADE DO APLICATIVO
    logo = custom.CTkLabel(
        menu_lateral,
        text="FINANCE\nCONTROL",
        font=("Arial", 23, "bold"),
        text_color=TEXTO,
        justify="left"
    )
    logo.pack(anchor="w", padx=25, pady=(35, 50))

    titulo_menu = custom.CTkLabel(
        menu_lateral,
        text="MENU PRINCIPAL",
        font=("Arial", 16, "bold"),
        text_color=TEXTO
    )
    titulo_menu.pack(anchor="w", padx=25, pady=(0, 15))

    # RODAPÉ DO MENU
    rodape_menu = custom.CTkLabel(
        menu_lateral,
        text="Sistema financeiro local\nVersão 1.0",
        font=("Arial", 11),
        text_color=TEXTO_SECUNDARIO,
        justify="left"
    )
    rodape_menu.pack(
        side="bottom",
        anchor="w",
        padx=25,
        pady=25
    )

    # ÁREA PRINCIPAL
    conteudo = custom.CTkFrame(
        janela,
        fg_color="transparent"
    )
    conteudo.grid(
        row=0,
        column=1,
        sticky="nsew",
        padx=30,
        pady=25
    )

    conteudo.grid_columnconfigure(0, weight=1)
    conteudo.grid_rowconfigure(0, weight=1)

    # Cada tela do menu é um frame dentro da área principal
    telas = {}
    botoes_menu = {}

    estilo_menu_opcoes = dict(
        fg_color=CARTAO,
        button_color=BORDA,
        button_hover_color=AZUL,
        text_color=TEXTO,
        dropdown_fg_color=CARTAO,
        dropdown_text_color=TEXTO,
        dropdown_hover_color=BORDA,
        font=("Arial", 13),
        dropdown_font=("Arial", 13)
    )

    def criar_cabecalho(pai, texto_titulo, texto_subtitulo):

        cabecalho_tela = custom.CTkFrame(
            pai,
            fg_color="transparent"
        )
        cabecalho_tela.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 25)
        )

        titulo_tela = custom.CTkLabel(
            cabecalho_tela,
            text=texto_titulo,
            font=("Arial", 27, "bold"),
            text_color=TEXTO
        )
        titulo_tela.pack(anchor="w")

        subtitulo_tela = custom.CTkLabel(
            cabecalho_tela,
            text=texto_subtitulo,
            font=("Arial", 13),
            text_color=TEXTO_SECUNDARIO
        )
        subtitulo_tela.pack(anchor="w", pady=(5, 0))

        return cabecalho_tela, subtitulo_tela

    def criar_feedback(label):
        """Devolve uma função que mostra uma mensagem e a apaga em 5 s."""

        tarefa = {"id": None}

        def mostrar(texto, cor):

            if tarefa["id"] is not None:
                try:
                    janela.after_cancel(tarefa["id"])
                except Exception:
                    pass

            label.configure(text=texto, text_color=cor)
            tarefa["id"] = janela.after(
                5000,
                lambda: label.configure(text="")
            )

        return mostrar

    def montar_opcoes_meses():
        opcoes = {TODOS_OS_MESES: None}

        for ano_mes in listar_meses():
            opcoes[nome_mes(ano_mes)] = ano_mes

        return opcoes

    def atualizar_menu_meses(menu, mapa):
        """Recarrega os meses disponíveis, mantendo a escolha atual."""

        selecionado = menu.get()
        novas = montar_opcoes_meses()

        mapa.clear()
        mapa.update(novas)
        menu.configure(values=list(novas.keys()))

        if selecionado not in novas:
            menu.set(nome_mes(estado["mes"]))

    def desenhar_linha(
        pai, id_lancamento, descricao, valor, tipo, data=None,
        editar=None, excluir=None
    ):

        linha = custom.CTkFrame(
            pai,
            fg_color="#263449",
            corner_radius=8
        )
        linha.pack(
            fill="x",
            pady=4,
            padx=3
        )

        linha.grid_columnconfigure(0, weight=1)

        nome = custom.CTkLabel(
            linha,
            text=f"{id_lancamento} - {descricao}",
            text_color=TEXTO,
            font=("Arial", 13),
            anchor="w"
        )
        nome.grid(
            row=0,
            column=0,
            sticky="w",
            padx=15,
            pady=13
        )

        if tipo == "entrada":
            cor = VERDE
            sinal = "+"
            texto_tipo = "ENTRADA"
        elif tipo == "saida":
            cor = VERMELHO
            sinal = "-"
            texto_tipo = "SAÍDA"
        else:
            cor = TEXTO_SECUNDARIO
            sinal = ""
            texto_tipo = "NÃO INFORMADO"

        data_label = custom.CTkLabel(
            linha,
            text=formatar_data(data),
            text_color=TEXTO_SECUNDARIO,
            font=("Arial", 12),
            width=90
        )
        data_label.grid(
            row=0,
            column=1,
            padx=8,
            pady=13
        )

        valor_label = custom.CTkLabel(
            linha,
            text=f"{sinal} {formatar_moeda(abs(valor))}",
            text_color=cor,
            font=("Arial", 13, "bold"),
            width=130,
            anchor="e"
        )
        valor_label.grid(
            row=0,
            column=2,
            padx=8,
            pady=13
        )

        tipo_label = custom.CTkLabel(
            linha,
            text=texto_tipo,
            text_color=cor,
            font=("Arial", 11, "bold"),
            width=70
        )
        tipo_label.grid(
            row=0,
            column=3,
            padx=8,
            pady=13
        )

        if editar is not None:
            botao_editar = custom.CTkButton(
                linha,
                text="Editar",
                width=64,
                height=28,
                corner_radius=6,
                fg_color=AZUL,
                hover_color="#1D4ED8",
                text_color=TEXTO,
                font=("Arial", 12, "bold"),
                command=editar
            )
            botao_editar.grid(row=0, column=4, padx=(8, 4), pady=10)

        if excluir is not None:
            botao_excluir = custom.CTkButton(
                linha,
                text="Excluir",
                width=64,
                height=28,
                corner_radius=6,
                fg_color=VERMELHO,
                hover_color="#EF4444",
                text_color=TEXTO,
                font=("Arial", 12, "bold"),
                command=excluir
            )
            botao_excluir.grid(row=0, column=5, padx=(4, 12), pady=10)

    # ===============================================================
    # TELA: VISÃO GERAL (MENU PRINCIPAL DO MÊS)
    # ===============================================================
    tela_visao = custom.CTkFrame(
        conteudo,
        fg_color="transparent"
    )
    tela_visao.grid(row=0, column=0, sticky="nsew")
    tela_visao.grid_columnconfigure(0, weight=1)
    tela_visao.grid_rowconfigure(3, weight=1)
    telas["visao"] = tela_visao

    # CABEÇALHO
    _, subtitulo_visao = criar_cabecalho(
        tela_visao,
        "Visão geral",
        "Acompanhe e movimente o seu saldo."
    )

    # CARTÕES FINANCEIROS
    area_cartoes = custom.CTkFrame(
        tela_visao,
        fg_color="transparent"
    )
    area_cartoes.grid(
        row=1,
        column=0,
        sticky="ew",
        pady=(0, 25)
    )

    for coluna in range(3):
        area_cartoes.grid_columnconfigure(
            coluna,
            weight=1
        )

    def criar_cartao(coluna, titulo, cor):

        cartao = custom.CTkFrame(
            area_cartoes,
            fg_color=CARTAO,
            corner_radius=12,
            border_width=1,
            border_color=BORDA
        )
        cartao.grid(
            row=0,
            column=coluna,
            sticky="ew",
            padx=7,
            ipady=8
        )

        nome = custom.CTkLabel(
            cartao,
            text=titulo,
            font=("Arial", 13),
            text_color=TEXTO_SECUNDARIO
        )
        nome.pack(anchor="w", padx=20, pady=(15, 6))

        valor = custom.CTkLabel(
            cartao,
            text="R$ 0,00",
            font=("Arial", 23, "bold"),
            text_color=cor
        )
        valor.pack(anchor="w", padx=20, pady=(0, 2))

        rodape = custom.CTkLabel(
            cartao,
            text="",
            font=("Arial", 11),
            text_color=TEXTO_SECUNDARIO
        )
        rodape.pack(anchor="w", padx=20, pady=(0, 10))

        return valor, rodape

    valor_saldo, rodape_saldo = criar_cartao(
        0, "SALDO DO MÊS", TEXTO
    )

    valor_entradas, rodape_entradas = criar_cartao(
        1, "ENTRADAS DO MÊS", VERDE
    )

    valor_saidas, rodape_saidas = criar_cartao(
        2, "SAÍDAS DO MÊS", VERMELHO
    )

    # AÇÕES: ADICIONAR E DIMINUIR SALDO
    area_acoes = custom.CTkFrame(
        tela_visao,
        fg_color="transparent"
    )
    area_acoes.grid(
        row=2,
        column=0,
        sticky="ew",
        pady=(0, 25)
    )

    area_acoes.grid_columnconfigure(0, weight=1)
    area_acoes.grid_columnconfigure(1, weight=1)

    mensagem_acao = custom.CTkLabel(
        area_acoes,
        text="",
        font=("Arial", 13, "bold"),
        text_color=TEXTO_SECUNDARIO,
        anchor="w"
    )
    mensagem_acao.grid(
        row=1,
        column=0,
        columnspan=2,
        sticky="w",
        padx=7,
        pady=(8, 0)
    )

    mostrar_feedback = criar_feedback(mensagem_acao)

    # ---------------------------------------------------------------
    # JANELA DE LANÇAMENTO (ADICIONAR / DIMINUIR / EDITAR)
    # ---------------------------------------------------------------
    def abrir_dialogo(tipo, lancamento=None, ao_concluir=None):

        editando = lancamento is not None
        entrada = tipo == "entrada"

        if editando:
            cor = "#60A5FA"
            cor_hover = "#3B82F6"
            titulo_dialogo = "Editar lançamento"
            texto_dialogo = "Altere os dados e salve."
            texto_confirmar = "Salvar alterações"
            altura = 520
        elif entrada:
            cor = VERDE
            cor_hover = "#16A34A"
            titulo_dialogo = "Adicionar saldo"
            texto_dialogo = "Registre uma nova entrada de dinheiro."
            texto_confirmar = "Confirmar entrada"
            altura = 440
        else:
            cor = VERMELHO
            cor_hover = "#EF4444"
            titulo_dialogo = "Diminuir saldo"
            texto_dialogo = "Registre uma nova saída de dinheiro."
            texto_confirmar = "Confirmar saída"
            altura = 440

        dialogo = custom.CTkToplevel(janela)
        dialogo.title(titulo_dialogo)
        dialogo.configure(fg_color=FUNDO)
        dialogo.resizable(False, False)

        largura = 480
        pos_x = janela.winfo_x() + (janela.winfo_width() - largura) // 2
        pos_y = janela.winfo_y() + (janela.winfo_height() - altura) // 2
        dialogo.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
        dialogo.transient(janela)

        titulo_d = custom.CTkLabel(
            dialogo,
            text=titulo_dialogo,
            font=("Arial", 24, "bold"),
            text_color=cor
        )
        titulo_d.pack(anchor="w", padx=30, pady=(28, 0))

        subtitulo_d = custom.CTkLabel(
            dialogo,
            text=texto_dialogo,
            font=("Arial", 13),
            text_color=TEXTO_SECUNDARIO
        )
        subtitulo_d.pack(anchor="w", padx=30, pady=(4, 20))

        rotulo_descricao = custom.CTkLabel(
            dialogo,
            text="Descrição",
            font=("Arial", 13),
            text_color=TEXTO_SECUNDARIO
        )
        rotulo_descricao.pack(anchor="w", padx=30, pady=(0, 6))

        campo_descricao = custom.CTkEntry(
            dialogo,
            height=42,
            fg_color=CARTAO,
            border_color=BORDA,
            text_color=TEXTO,
            font=("Arial", 14),
            placeholder_text="Ex.: Salário, Mercado, Aluguel"
        )
        campo_descricao.pack(fill="x", padx=30)

        # Valor e data lado a lado
        linha_valor_data = custom.CTkFrame(
            dialogo,
            fg_color="transparent"
        )
        linha_valor_data.pack(fill="x", padx=30, pady=(16, 0))
        linha_valor_data.grid_columnconfigure(0, weight=1)
        linha_valor_data.grid_columnconfigure(1, weight=1)

        rotulo_valor = custom.CTkLabel(
            linha_valor_data,
            text="Valor (R$)",
            font=("Arial", 13),
            text_color=TEXTO_SECUNDARIO
        )
        rotulo_valor.grid(row=0, column=0, sticky="w")

        campo_valor = custom.CTkEntry(
            linha_valor_data,
            height=42,
            fg_color=CARTAO,
            border_color=BORDA,
            text_color=TEXTO,
            font=("Arial", 14),
            placeholder_text="Ex.: 1500,00"
        )
        campo_valor.grid(
            row=1, column=0, sticky="ew", padx=(0, 8), pady=(6, 0)
        )

        rotulo_data = custom.CTkLabel(
            linha_valor_data,
            text="Data (dd/mm/aaaa)",
            font=("Arial", 13),
            text_color=TEXTO_SECUNDARIO
        )
        rotulo_data.grid(row=0, column=1, sticky="w", padx=(8, 0))

        campo_data = custom.CTkEntry(
            linha_valor_data,
            height=42,
            fg_color=CARTAO,
            border_color=BORDA,
            text_color=TEXTO,
            font=("Arial", 14),
            placeholder_text="dd/mm/aaaa"
        )
        campo_data.grid(
            row=1, column=1, sticky="ew", padx=(8, 0), pady=(6, 0)
        )

        seletor_tipo = None

        if editando:
            rotulo_tipo = custom.CTkLabel(
                dialogo,
                text="Tipo",
                font=("Arial", 13),
                text_color=TEXTO_SECUNDARIO
            )
            rotulo_tipo.pack(anchor="w", padx=30, pady=(16, 6))

            seletor_tipo = custom.CTkSegmentedButton(
                dialogo,
                values=["Entrada", "Saída"],
                fg_color=CARTAO,
                selected_color=AZUL,
                selected_hover_color="#1D4ED8",
                unselected_color=CARTAO,
                unselected_hover_color=BORDA,
                text_color=TEXTO,
                height=34
            )
            seletor_tipo.pack(anchor="w", padx=30)

        # Valores iniciais
        if editando:
            _, descricao_atual, valor_atual, _, data_atual = lancamento

            campo_descricao.insert(0, descricao_atual)
            campo_valor.insert(0, f"{abs(valor_atual):.2f}".replace(".", ","))
            campo_data.insert(0, formatar_data(data_atual))
            seletor_tipo.set("Entrada" if entrada else "Saída")
        else:
            campo_data.insert(0, date.today().strftime("%d/%m/%Y"))

        erro_label = custom.CTkLabel(
            dialogo,
            text="",
            font=("Arial", 13),
            text_color=VERMELHO,
            anchor="w"
        )
        erro_label.pack(anchor="w", padx=30, pady=(10, 0))

        def fechar(evento=None):
            try:
                dialogo.grab_release()
            except Exception:
                pass
            dialogo.destroy()

        def confirmar(evento=None):

            descricao = campo_descricao.get().strip()
            valor = converter_valor(campo_valor.get())
            data_iso = converter_data(campo_data.get())

            if not descricao:
                erro_label.configure(text="Informe uma descrição.")
                campo_descricao.focus()
                return

            if valor is None or valor <= 0:
                erro_label.configure(
                    text="Informe um valor válido maior que zero."
                )
                campo_valor.focus()
                return

            if data_iso is None:
                erro_label.configure(
                    text="Informe uma data válida (dd/mm/aaaa)."
                )
                campo_data.focus()
                return

            tipo_final = tipo

            if editando:
                tipo_final = (
                    "entrada" if seletor_tipo.get() == "Entrada" else "saida"
                )

            try:
                # Nova saída maior que o saldo acumulado: pede confirmação
                if not editando and tipo_final == "saida":
                    saldo_atual = obter_totais()[2]

                    if valor > saldo_atual:
                        continuar = messagebox.askyesno(
                            "Saldo insuficiente",
                            f"Esta saída é maior que o saldo acumulado "
                            f"({formatar_moeda(saldo_atual)}).\n"
                            f"O saldo ficará negativo. Deseja continuar?",
                            parent=dialogo
                        )
                        if not continuar:
                            return

                if editando:
                    atualizar_lancamento(
                        lancamento[0], descricao, valor, tipo_final, data_iso
                    )
                else:
                    adicionar_lancamento(
                        descricao, valor, tipo_final, data_iso
                    )

            except sqlite3.Error as erro:
                print(f"Erro ao salvar lançamento: {erro}")
                erro_label.configure(
                    text="Não foi possível salvar a movimentação."
                )
                return

            fechar()

            # ATUALIZAÇÃO AUTOMÁTICA
            atualizar_tudo()

            if editando:
                texto = "Lançamento atualizado."
                cor_msg = CIANO
            elif tipo_final == "entrada":
                texto = (
                    f"Saldo adicionado: + {formatar_moeda(valor)}  "
                    f"({descricao})"
                )
                cor_msg = VERDE
            else:
                texto = (
                    f"Saldo diminuído: - {formatar_moeda(valor)}  "
                    f"({descricao})"
                )
                cor_msg = VERMELHO

            # Data em outro mês: avisa onde o lançamento foi parar
            if data_iso[:7] != estado["mes"]:
                texto += f"  [lançado em {nome_mes(data_iso[:7])}]"

            (ao_concluir or mostrar_feedback)(texto, cor_msg)

        botoes_dialogo = custom.CTkFrame(
            dialogo,
            fg_color="transparent"
        )
        botoes_dialogo.pack(fill="x", padx=30, pady=(14, 0))
        botoes_dialogo.grid_columnconfigure(0, weight=1)
        botoes_dialogo.grid_columnconfigure(1, weight=2)

        botao_cancelar = custom.CTkButton(
            botoes_dialogo,
            text="Cancelar",
            height=44,
            corner_radius=8,
            fg_color=CARTAO,
            hover_color=BORDA,
            text_color=TEXTO,
            font=("Arial", 14, "bold"),
            command=fechar
        )
        botao_cancelar.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        botao_confirmar = custom.CTkButton(
            botoes_dialogo,
            text=texto_confirmar,
            height=44,
            corner_radius=8,
            fg_color=cor,
            hover_color=cor_hover,
            text_color=TEXTO,
            font=("Arial", 14, "bold"),
            command=confirmar
        )
        botao_confirmar.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        campo_descricao.bind("<Return>", lambda e: campo_valor.focus())
        campo_valor.bind("<Return>", lambda e: campo_data.focus())
        campo_data.bind("<Return>", confirmar)
        dialogo.bind("<Escape>", fechar)

        def ativar():
            try:
                dialogo.grab_set()
            except Exception:
                pass
            campo_descricao.focus()

        dialogo.after(150, ativar)

    botao_adicionar = custom.CTkButton(
        area_acoes,
        text="+  Adicionar saldo",
        height=56,
        corner_radius=10,
        fg_color=VERDE,
        hover_color="#16A34A",
        text_color=TEXTO,
        font=("Arial", 16, "bold"),
        command=lambda: abrir_dialogo("entrada")
    )
    botao_adicionar.grid(
        row=0,
        column=0,
        sticky="ew",
        padx=7
    )

    botao_diminuir = custom.CTkButton(
        area_acoes,
        text="-  Diminuir saldo",
        height=56,
        corner_radius=10,
        fg_color=VERMELHO,
        hover_color="#EF4444",
        text_color=TEXTO,
        font=("Arial", 16, "bold"),
        command=lambda: abrir_dialogo("saida")
    )
    botao_diminuir.grid(
        row=0,
        column=1,
        sticky="ew",
        padx=7
    )

    # ÁREA DE TRANSAÇÕES
    frame_historico = custom.CTkFrame(
        tela_visao,
        fg_color=CARTAO,
        corner_radius=12,
        border_width=1,
        border_color=BORDA
    )
    frame_historico.grid(
        row=3,
        column=0,
        sticky="nsew"
    )

    frame_historico.grid_columnconfigure(0, weight=1)
    frame_historico.grid_rowconfigure(1, weight=1)

    cabecalho_historico = custom.CTkFrame(
        frame_historico,
        fg_color="transparent"
    )
    cabecalho_historico.grid(
        row=0,
        column=0,
        sticky="ew",
        padx=20,
        pady=20
    )

    titulo_historico = custom.CTkLabel(
        cabecalho_historico,
        text="Movimentações recentes do mês",
        font=("Arial", 18, "bold"),
        text_color=TEXTO
    )
    titulo_historico.pack(side="left")

    # LISTA DE TRANSAÇÕES
    lista_transacoes = custom.CTkScrollableFrame(
        frame_historico,
        fg_color="transparent"
    )
    lista_transacoes.grid(
        row=1,
        column=0,
        sticky="nsew",
        padx=15,
        pady=(0, 15)
    )

    # ATUALIZAR DADOS DO PAINEL (SOMENTE O MÊS ATUAL)
    def atualizar_painel():

        try:
            totais = totais_periodo(estado["mes"])
            acumulado = obter_totais()[2]
            transacoes, _ = buscar_lancamentos(
                mes=estado["mes"], limite=10
            )

        except sqlite3.Error as erro:
            print(f"Erro ao atualizar painel: {erro}")
            return

        saldo = totais["saldo"]

        subtitulo_visao.configure(
            text=f"{nome_mes(estado['mes'])}  ·  "
                 f"Acompanhe e movimente o seu saldo."
        )

        valor_saldo.configure(
            text=formatar_moeda(saldo),
            text_color=VERDE if saldo >= 0 else VERMELHO
        )
        rodape_saldo.configure(
            text=f"Acumulado: {formatar_moeda(acumulado)}"
        )

        valor_entradas.configure(
            text=formatar_moeda(totais["entradas"])
        )
        rodape_entradas.configure(
            text=f"{totais['qtd_entradas']} entrada(s) no mês"
        )

        valor_saidas.configure(
            text=formatar_moeda(totais["saidas"])
        )
        rodape_saidas.configure(
            text=f"{totais['qtd_saidas']} saída(s) no mês"
        )

        # LIMPAR LISTA
        for widget in lista_transacoes.winfo_children():
            widget.destroy()

        if not transacoes:
            vazio = custom.CTkLabel(
                lista_transacoes,
                text="Nenhuma movimentação neste mês.",
                text_color=TEXTO_SECUNDARIO,
                font=("Arial", 14)
            )
            vazio.pack(pady=35)
            return

        # EXIBIR TRANSAÇÕES
        for id_lancamento, descricao, valor, tipo, data in transacoes:
            desenhar_linha(
                lista_transacoes, id_lancamento, descricao, valor, tipo, data
            )

    # BOTÃO DE ATUALIZAÇÃO
    botao_atualizar = custom.CTkButton(
        cabecalho_historico,
        text="Atualizar",
        width=100,
        height=32,
        fg_color=AZUL,
        hover_color="#1D4ED8",
        command=atualizar_painel
    )
    botao_atualizar.pack(side="right")

    tela_visao.preparar = atualizar_painel

    # ===============================================================
    # TELA: DASHBOARD (GRÁFICOS)
    # ===============================================================
    tela_dash = custom.CTkFrame(
        conteudo,
        fg_color="transparent"
    )
    tela_dash.grid(row=0, column=0, sticky="nsew")
    tela_dash.grid_columnconfigure(0, weight=1)
    tela_dash.grid_rowconfigure(1, weight=1)
    telas["dashboard"] = tela_dash

    cabecalho_dash, subtitulo_dash = criar_cabecalho(
        tela_dash,
        "Dashboard",
        "Visão analítica de todas as suas transações."
    )

    mapa_dash = {}

    menu_dash = custom.CTkOptionMenu(
        cabecalho_dash,
        values=[TODOS_OS_MESES],
        width=190,
        height=36,
        command=lambda _=None: atualizar_dashboard(),
        **estilo_menu_opcoes
    )
    menu_dash.set(nome_mes(estado["mes"]))
    menu_dash.place(relx=1.0, rely=0.5, anchor="e")

    corpo_dash = custom.CTkScrollableFrame(
        tela_dash,
        fg_color="transparent"
    )
    corpo_dash.grid(row=1, column=0, sticky="nsew")
    corpo_dash.grid_columnconfigure(0, weight=1, uniform="graficos")
    corpo_dash.grid_columnconfigure(1, weight=1, uniform="graficos")

    # INDICADORES (KPIs)
    area_kpis = custom.CTkFrame(
        corpo_dash,
        fg_color="transparent"
    )
    area_kpis.grid(row=0, column=0, columnspan=2, sticky="ew")

    for coluna in range(4):
        area_kpis.grid_columnconfigure(coluna, weight=1, uniform="kpis")

    def criar_kpi(coluna, titulo, cor):

        cartao = custom.CTkFrame(
            area_kpis,
            fg_color=FUNDO_NEON,
            corner_radius=12,
            border_width=1,
            border_color=BORDA_NEON
        )
        cartao.grid(row=0, column=coluna, sticky="ew", padx=7, pady=7)

        nome = custom.CTkLabel(
            cartao,
            text=f"▸ {titulo}",
            font=("Consolas", 11, "bold"),
            text_color=EIXO
        )
        nome.pack(anchor="w", padx=16, pady=(14, 4))

        valor = custom.CTkLabel(
            cartao,
            text="R$ 0,00",
            font=("Consolas", 18, "bold"),
            text_color=cor
        )
        valor.pack(anchor="w", padx=16)

        sub = custom.CTkLabel(
            cartao,
            text="",
            font=("Arial", 11),
            text_color=EIXO
        )
        sub.pack(anchor="w", padx=16, pady=(2, 14))

        return valor, sub

    kpi_entradas, sub_entradas = criar_kpi(0, "ENTRADAS", graficos.VERDE_NEON)
    kpi_saidas, sub_saidas = criar_kpi(1, "SAÍDAS", graficos.ROSA_NEON)
    kpi_saldo, sub_saldo = criar_kpi(2, "SALDO", CIANO)
    kpi_qtd, sub_qtd = criar_kpi(3, "MOVIMENTAÇÕES", graficos.ROXO_NEON)

    # CARTÕES DE GRÁFICO
    desenhos = {}

    def criar_card_grafico(linha, coluna, titulo, subtitulo):

        card = custom.CTkFrame(
            corpo_dash,
            fg_color=FUNDO_NEON,
            corner_radius=12,
            border_width=1,
            border_color=BORDA_NEON
        )
        card.grid(row=linha, column=coluna, sticky="nsew", padx=7, pady=7)

        titulo_card = custom.CTkLabel(
            card,
            text=f"◈  {titulo}",
            font=("Consolas", 13, "bold"),
            text_color=CIANO
        )
        titulo_card.pack(anchor="w", padx=18, pady=(14, 0))

        sub_card = custom.CTkLabel(
            card,
            text=subtitulo,
            font=("Arial", 11),
            text_color=EIXO
        )
        sub_card.pack(anchor="w", padx=18)

        canvas = tk.Canvas(
            card,
            height=250,
            bg=FUNDO_NEON,
            highlightthickness=0
        )
        canvas.pack(fill="both", expand=True, padx=12, pady=(6, 14))

        return card, canvas, sub_card

    def registrar_desenho(canvas, funcao):
        desenhos[canvas] = funcao
        canvas.bind("<Configure>", lambda e, c=canvas: desenhos[c]())

    dados_dash = {
        "rotulos": [], "entradas": [], "saidas": [], "saldo": [],
        "total_entradas": 0, "total_saidas": 0,
        "rank_saidas": [], "rank_entradas": []
    }

    card_fluxo, canvas_fluxo, sub_fluxo = criar_card_grafico(
        1, 0, "FLUXO DE CAIXA", "Entradas e saídas por dia"
    )
    card_saldo, canvas_saldo, sub_saldo_grafico = criar_card_grafico(
        1, 1, "EVOLUÇÃO DO SALDO", "Saldo acumulado ao longo do período"
    )
    card_rosca, canvas_rosca, _ = criar_card_grafico(
        2, 0, "ENTRADAS x SAÍDAS", "Proporção do movimento no período"
    )
    card_rank, canvas_rank, sub_rank = criar_card_grafico(
        2, 1, "MAIORES MOVIMENTAÇÕES", "Top 5 por descrição"
    )

    def desenhar_fluxo():
        graficos.grafico_barras(
            canvas_fluxo,
            dados_dash["rotulos"],
            dados_dash["entradas"],
            dados_dash["saidas"]
        )

    def desenhar_saldo():
        graficos.grafico_area(
            canvas_saldo,
            dados_dash["rotulos"],
            dados_dash["saldo"]
        )

    def desenhar_rosca():
        saldo_periodo = (
            dados_dash["total_entradas"] - dados_dash["total_saidas"]
        )
        graficos.grafico_rosca(
            canvas_rosca,
            dados_dash["total_entradas"],
            dados_dash["total_saidas"],
            "R$ " + graficos.abreviar(saldo_periodo),
            "SALDO",
            formatar_moeda
        )

    def desenhar_ranking():
        if seletor_ranking.get() == "Entradas":
            itens, cor = dados_dash["rank_entradas"], graficos.VERDE_NEON
        else:
            itens, cor = dados_dash["rank_saidas"], graficos.ROSA_NEON

        graficos.grafico_ranking(canvas_rank, itens, cor, formatar_moeda)

    seletor_ranking = custom.CTkSegmentedButton(
        card_rank,
        values=["Saídas", "Entradas"],
        fg_color=CARTAO,
        selected_color=AZUL,
        selected_hover_color="#1D4ED8",
        unselected_color=CARTAO,
        unselected_hover_color=BORDA,
        text_color=TEXTO,
        height=28,
        command=lambda _=None: desenhar_ranking()
    )
    seletor_ranking.set("Saídas")
    seletor_ranking.place(relx=1.0, x=-16, y=14, anchor="ne")

    registrar_desenho(canvas_fluxo, desenhar_fluxo)
    registrar_desenho(canvas_saldo, desenhar_saldo)
    registrar_desenho(canvas_rosca, desenhar_rosca)
    registrar_desenho(canvas_rank, desenhar_ranking)

    def atualizar_dashboard(*_):

        ano_mes = mapa_dash.get(menu_dash.get())

        try:
            totais = totais_periodo(ano_mes)
            serie = serie_periodo(ano_mes)
            rank_saidas = top_por_descricao("saida", ano_mes)
            rank_entradas = top_por_descricao("entrada", ano_mes)
        except sqlite3.Error as erro:
            print(f"Erro ao atualizar dashboard: {erro}")
            return

        rotulos, entradas, saidas, saldo = [], [], [], []
        acumulado = 0

        for chave, valor_entrada, valor_saida in serie:
            if ano_mes:
                rotulos.append(str(int(chave[8:10])))
            else:
                rotulos.append(
                    f"{MESES_ABREV[int(chave[5:7]) - 1]}/{chave[2:4]}"
                )

            entradas.append(valor_entrada)
            saidas.append(valor_saida)
            acumulado = round(acumulado + valor_entrada - valor_saida, 2)
            saldo.append(acumulado)

        dados_dash.update(
            rotulos=rotulos, entradas=entradas, saidas=saidas, saldo=saldo,
            total_entradas=totais["entradas"],
            total_saidas=totais["saidas"],
            rank_saidas=rank_saidas, rank_entradas=rank_entradas
        )

        periodo = nome_mes(ano_mes) if ano_mes else "todos os meses"
        subtitulo_dash.configure(
            text=f"Visão analítica das suas transações  ·  {periodo}"
        )
        sub_fluxo.configure(
            text="Entradas e saídas por " + ("dia" if ano_mes else "mês")
        )

        # indicadores
        kpi_entradas.configure(text=formatar_moeda(totais["entradas"]))
        sub_entradas.configure(
            text=f"Maior: {formatar_moeda(totais['maior_entrada'])}"
            if totais["qtd_entradas"] else "Nenhuma entrada"
        )

        kpi_saidas.configure(text=formatar_moeda(totais["saidas"]))
        sub_saidas.configure(
            text="Ticket médio: " + formatar_moeda(
                totais["saidas"] / totais["qtd_saidas"]
            ) if totais["qtd_saidas"] else "Nenhuma saída"
        )

        kpi_saldo.configure(
            text=formatar_moeda(totais["saldo"]),
            text_color=CIANO if totais["saldo"] >= 0 else graficos.ROSA_NEON
        )

        if totais["entradas"] > 0:
            sub_saldo.configure(
                text=f"{totais['saldo'] / totais['entradas'] * 100:.0f}% "
                     f"das entradas"
            )
        else:
            sub_saldo.configure(text="Sem entradas no período")

        kpi_qtd.configure(text=str(totais["qtd"]))
        sub_qtd.configure(
            text=f"{totais['qtd_entradas']} entradas · "
                 f"{totais['qtd_saidas']} saídas"
        )

        for funcao in desenhos.values():
            funcao()

    def preparar_dashboard():
        atualizar_menu_meses(menu_dash, mapa_dash)
        atualizar_dashboard()

    tela_dash.preparar = preparar_dashboard

    # ===============================================================
    # TELA: EXTRATO (PESQUISAR, EDITAR E EXCLUIR)
    # ===============================================================
    tela_extrato = custom.CTkFrame(
        conteudo,
        fg_color="transparent"
    )
    tela_extrato.grid(row=0, column=0, sticky="nsew")
    tela_extrato.grid_columnconfigure(0, weight=1)
    tela_extrato.grid_rowconfigure(1, weight=1)
    telas["extrato"] = tela_extrato

    criar_cabecalho(
        tela_extrato,
        "Extrato",
        "Pesquise, edite e exclua as suas movimentações."
    )

    frame_extrato = custom.CTkFrame(
        tela_extrato,
        fg_color=CARTAO,
        corner_radius=12,
        border_width=1,
        border_color=BORDA
    )
    frame_extrato.grid(row=1, column=0, sticky="nsew")
    frame_extrato.grid_columnconfigure(0, weight=1)
    frame_extrato.grid_rowconfigure(2, weight=1)

    barra_filtros = custom.CTkFrame(
        frame_extrato,
        fg_color="transparent"
    )
    barra_filtros.grid(
        row=0,
        column=0,
        sticky="ew",
        padx=20,
        pady=(20, 8)
    )
    barra_filtros.grid_columnconfigure(0, weight=1)

    campo_busca = custom.CTkEntry(
        barra_filtros,
        height=38,
        fg_color=MENU,
        border_color=BORDA,
        text_color=TEXTO,
        font=("Arial", 14),
        placeholder_text="Pesquisar por descrição, valor ou data..."
    )
    campo_busca.grid(row=0, column=0, sticky="ew", padx=(0, 10))

    mapa_extrato = {}

    menu_extrato = custom.CTkOptionMenu(
        barra_filtros,
        values=[TODOS_OS_MESES],
        width=170,
        height=38,
        command=lambda _=None: carregar_extrato(),
        **estilo_menu_opcoes
    )
    menu_extrato.set(nome_mes(estado["mes"]))
    menu_extrato.grid(row=0, column=1, padx=(0, 10))

    filtros_tipo = {
        "Todos": None,
        "Entradas": "entrada",
        "Saídas": "saida"
    }

    filtro_extrato = custom.CTkSegmentedButton(
        barra_filtros,
        values=list(filtros_tipo.keys()),
        fg_color=MENU,
        selected_color=AZUL,
        selected_hover_color="#1D4ED8",
        unselected_color=MENU,
        unselected_hover_color=BORDA,
        text_color=TEXTO,
        height=38,
        command=lambda _=None: carregar_extrato()
    )
    filtro_extrato.set("Todos")
    filtro_extrato.grid(row=0, column=2)

    barra_info = custom.CTkFrame(
        frame_extrato,
        fg_color="transparent"
    )
    barra_info.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 6))
    barra_info.grid_columnconfigure(0, weight=1)

    info_extrato = custom.CTkLabel(
        barra_info,
        text="",
        font=("Arial", 12),
        text_color=TEXTO_SECUNDARIO,
        anchor="w"
    )
    info_extrato.grid(row=0, column=0, sticky="w")

    mensagem_extrato = custom.CTkLabel(
        barra_info,
        text="",
        font=("Arial", 13, "bold"),
        text_color=TEXTO_SECUNDARIO,
        anchor="e"
    )
    mensagem_extrato.grid(row=0, column=1, sticky="e")

    mostrar_feedback_extrato = criar_feedback(mensagem_extrato)

    lista_extrato = custom.CTkScrollableFrame(
        frame_extrato,
        fg_color="transparent"
    )
    lista_extrato.grid(
        row=2,
        column=0,
        sticky="nsew",
        padx=15,
        pady=(0, 15)
    )

    LIMITE_EXTRATO = 100

    def excluir_do_extrato(lancamento):

        id_lancamento, descricao, valor, _, data = lancamento

        confirmou = messagebox.askyesno(
            "Excluir lançamento",
            f"Excluir \"{descricao}\" ({formatar_moeda(valor)}) "
            f"de {formatar_data(data)}?\n\n"
            f"Essa ação não pode ser desfeita.",
            parent=janela
        )

        if not confirmou:
            return

        try:
            excluir_lancamento(id_lancamento)
        except sqlite3.Error as erro:
            print(f"Erro ao excluir lançamento: {erro}")
            mostrar_feedback_extrato(
                "Não foi possível excluir o lançamento.", VERMELHO
            )
            return

        atualizar_tudo()
        mostrar_feedback_extrato("Lançamento excluído.", VERMELHO)

    def carregar_extrato(*_):

        texto = campo_busca.get().strip()
        ano_mes = mapa_extrato.get(menu_extrato.get())
        tipo = filtros_tipo.get(filtro_extrato.get())

        try:
            dados, total = buscar_lancamentos(
                texto, ano_mes, tipo, limite=LIMITE_EXTRATO
            )
        except sqlite3.Error as erro:
            print(f"Erro ao carregar extrato: {erro}")
            return

        for widget in lista_extrato.winfo_children():
            widget.destroy()

        periodo = nome_mes(ano_mes) if ano_mes else "todos os meses"

        if total > len(dados):
            info_extrato.configure(
                text=f"Mostrando {len(dados)} de {total} resultados "
                     f"({periodo}). Refine a busca para ver os demais."
            )
        else:
            info_extrato.configure(
                text=f"{total} resultado(s)  ·  {periodo}"
            )

        if not dados:
            vazio = custom.CTkLabel(
                lista_extrato,
                text="Nenhuma movimentação encontrada.",
                text_color=TEXTO_SECUNDARIO,
                font=("Arial", 14)
            )
            vazio.pack(pady=35)
            return

        for lancamento in dados:
            id_lancamento, descricao, valor, tipo_linha, data = lancamento

            desenhar_linha(
                lista_extrato, id_lancamento, descricao, valor, tipo_linha,
                data,
                editar=lambda l=lancamento: abrir_dialogo(
                    l[3], l, mostrar_feedback_extrato
                ),
                excluir=lambda l=lancamento: excluir_do_extrato(l)
            )

    busca = {"id": None}

    def agendar_busca(evento=None):

        if busca["id"] is not None:
            try:
                janela.after_cancel(busca["id"])
            except Exception:
                pass

        busca["id"] = janela.after(250, carregar_extrato)

    campo_busca.bind("<KeyRelease>", agendar_busca)

    def preparar_extrato():
        atualizar_menu_meses(menu_extrato, mapa_extrato)
        carregar_extrato()

    tela_extrato.preparar = preparar_extrato

    # ===============================================================
    # TELA: LEVANTAMENTO MENSAL
    # ===============================================================
    tela_lev = custom.CTkFrame(
        conteudo,
        fg_color="transparent"
    )
    tela_lev.grid(row=0, column=0, sticky="nsew")
    tela_lev.grid_columnconfigure(0, weight=1)
    tela_lev.grid_rowconfigure(1, weight=1)
    telas["levantamento"] = tela_lev

    criar_cabecalho(
        tela_lev,
        "Levantamento mensal",
        "Cada mês fica salvo em arquivo. Na virada, o painel recomeça do zero."
    )

    frame_lev = custom.CTkFrame(
        tela_lev,
        fg_color=CARTAO,
        corner_radius=12,
        border_width=1,
        border_color=BORDA
    )
    frame_lev.grid(row=1, column=0, sticky="nsew")
    frame_lev.grid_columnconfigure(0, weight=1)
    frame_lev.grid_rowconfigure(1, weight=1)

    resumo_lev = custom.CTkLabel(
        frame_lev,
        text="",
        font=("Arial", 14, "bold"),
        text_color=TEXTO,
        anchor="w"
    )
    resumo_lev.grid(row=0, column=0, sticky="w", padx=22, pady=(20, 10))

    mensagem_lev = custom.CTkLabel(
        frame_lev,
        text="",
        font=("Arial", 12, "bold"),
        text_color=TEXTO_SECUNDARIO,
        anchor="e"
    )
    mensagem_lev.grid(row=0, column=1, sticky="e", padx=22, pady=(20, 10))

    mostrar_feedback_lev = criar_feedback(mensagem_lev)

    def exportar_do_levantamento(ano_mes):

        try:
            caminho = exportar_mes(ano_mes)
        except (OSError, sqlite3.Error) as erro:
            print(f"Erro ao exportar mês: {erro}")
            mostrar_feedback_lev("Não foi possível gerar o arquivo.", VERMELHO)
            return

        mostrar_feedback_lev(f"Arquivo salvo: {caminho}", CIANO)

    lista_lev = custom.CTkScrollableFrame(
        frame_lev,
        fg_color="transparent"
    )
    lista_lev.grid(
        row=1,
        column=0,
        sticky="nsew",
        padx=15,
        pady=(0, 15)
    )

    def abrir_extrato_do_mes(ano_mes):
        campo_busca.delete(0, "end")
        filtro_extrato.set("Todos")
        menu_extrato.set(nome_mes(ano_mes))
        mostrar_tela("extrato")

    def abrir_dashboard_do_mes(ano_mes):
        menu_dash.set(nome_mes(ano_mes))
        mostrar_tela("dashboard")

    def carregar_levantamento():

        try:
            meses = resumo_mensal()
        except sqlite3.Error as erro:
            print(f"Erro ao carregar levantamento: {erro}")
            return

        for widget in lista_lev.winfo_children():
            widget.destroy()

        acumulado_total = meses[0]["acumulado"] if meses else 0

        resumo_lev.configure(
            text=f"{len(meses)} mês(es) registrado(s)  ·  "
                 f"Saldo acumulado: {formatar_moeda(acumulado_total)}"
        )

        larguras = (110, 110, 110, 120)

        # CABEÇALHO DA TABELA
        titulos = ("MÊS", "ENTRADAS", "SAÍDAS", "SALDO DO MÊS", "ACUMULADO")

        linha_titulos = custom.CTkFrame(lista_lev, fg_color="transparent")
        linha_titulos.pack(fill="x", padx=3, pady=(0, 2))
        linha_titulos.grid_columnconfigure(0, weight=1)

        for coluna, titulo in enumerate(titulos):
            rotulo = custom.CTkLabel(
                linha_titulos,
                text=titulo,
                font=("Arial", 11, "bold"),
                text_color=TEXTO_SECUNDARIO,
                width=0 if coluna == 0 else 110,
                anchor="w" if coluna == 0 else "e"
            )
            rotulo.grid(
                row=0, column=coluna, padx=(15 if coluna == 0 else 8, 8),
                sticky="w" if coluna == 0 else "e"
            )

        for mes in meses:

            linha = custom.CTkFrame(
                lista_lev,
                fg_color="#263449",
                corner_radius=8
            )
            linha.pack(fill="x", pady=4, padx=3)
            linha.grid_columnconfigure(0, weight=1)

            eh_atual = mes["mes"] == estado["mes"]

            nome = custom.CTkLabel(
                linha,
                text=nome_mes(mes["mes"]) + ("  ● atual" if eh_atual else ""),
                text_color=CIANO if eh_atual else TEXTO,
                font=("Arial", 13, "bold"),
                anchor="w"
            )
            nome.grid(row=0, column=0, sticky="w", padx=15, pady=14)

            valores = (
                (mes["entradas"], VERDE),
                (mes["saidas"], VERMELHO),
                (mes["saldo"], VERDE if mes["saldo"] >= 0 else VERMELHO),
                (mes["acumulado"], CIANO),
            )

            for coluna, (valor, cor) in enumerate(valores, start=1):
                rotulo = custom.CTkLabel(
                    linha,
                    text=formatar_moeda(valor),
                    text_color=cor,
                    font=("Arial", 13, "bold"),
                    width=110,
                    anchor="e"
                )
                rotulo.grid(row=0, column=coluna, padx=8, pady=14)

            botao_extrato = custom.CTkButton(
                linha,
                text="Extrato",
                width=70,
                height=28,
                corner_radius=6,
                fg_color=AZUL,
                hover_color="#1D4ED8",
                text_color=TEXTO,
                font=("Arial", 12, "bold"),
                command=lambda m=mes["mes"]: abrir_extrato_do_mes(m)
            )
            botao_extrato.grid(row=0, column=5, padx=(8, 4))

            botao_graficos = custom.CTkButton(
                linha,
                text="Gráficos",
                width=70,
                height=28,
                corner_radius=6,
                fg_color=BORDA,
                hover_color=AZUL,
                text_color=TEXTO,
                font=("Arial", 12, "bold"),
                command=lambda m=mes["mes"]: abrir_dashboard_do_mes(m)
            )
            botao_graficos.grid(row=0, column=6, padx=(4, 4))

            botao_exportar = custom.CTkButton(
                linha,
                text="Arquivo",
                width=70,
                height=28,
                corner_radius=6,
                fg_color=BORDA,
                hover_color=AZUL,
                text_color=TEXTO,
                font=("Arial", 12, "bold"),
                command=lambda m=mes["mes"]: exportar_do_levantamento(m)
            )
            botao_exportar.grid(row=0, column=7, padx=(4, 12))

    tela_lev.preparar = carregar_levantamento

    # ---------------------------------------------------------------
    # ATUALIZAÇÃO AUTOMÁTICA APÓS QUALQUER ALTERAÇÃO
    # ---------------------------------------------------------------
    def atualizar_tudo():
        atualizar_painel()

        if estado["tela"] == "extrato":
            carregar_extrato()

    # ---------------------------------------------------------------
    # VIRADA DE MÊS: o painel principal recomeça do zero sozinho
    # ---------------------------------------------------------------
    def verificar_virada_mes():

        atual = mes_atual()

        if atual != estado["mes"]:
            estado["mes"] = atual

            try:
                fechar_meses_encerrados()
            except (OSError, sqlite3.Error) as erro:
                print(f"Erro ao fechar o mês: {erro}")

            atualizar_tudo()
            mostrar_feedback(
                f"Novo mês: {nome_mes(atual)}. O mês anterior foi fechado "
                f"e salvo em arquivo (pasta meses).",
                CIANO
            )

        janela.after(60000, verificar_virada_mes)

    # NAVEGAÇÃO DO MENU
    def mostrar_tela(nome):

        estado["tela"] = nome

        for tela in telas.values():
            tela.grid_remove()

        telas[nome].grid()
        telas[nome].preparar()

        for chave, botao in botoes_menu.items():
            if chave == nome:
                botao.configure(fg_color=AZUL, hover_color="#1D4ED8")
            else:
                botao.configure(fg_color="transparent", hover_color=CARTAO)

    def criar_botao_menu(chave, texto):

        botao = custom.CTkButton(
            menu_lateral,
            text=texto,
            anchor="w",
            height=42,
            corner_radius=8,
            fg_color="transparent",
            hover_color=CARTAO,
            text_color=TEXTO,
            font=("Arial", 14, "bold"),
            command=lambda: mostrar_tela(chave)
        )
        botao.pack(fill="x", padx=15, pady=(0, 6))
        botoes_menu[chave] = botao

    criar_botao_menu("visao", "  Visão geral")
    criar_botao_menu("dashboard", "  Dashboard")
    criar_botao_menu("extrato", "  Extrato")
    criar_botao_menu("levantamento", "  Levantamento mensal")

    # SAIR
    def sair():
        if messagebox.askyesno("Sair", "Deseja realmente sair?"):
            janela.destroy()

    botao_sair = custom.CTkButton(
        menu_lateral,
        text="  Sair",
        anchor="w",
        height=42,
        corner_radius=8,
        fg_color="transparent",
        hover_color=CARTAO,
        text_color=VERMELHO,
        font=("Arial", 14, "bold"),
        command=sair
    )
    botao_sair.pack(
        side="bottom",
        fill="x",
        padx=15,
        pady=(0, 5)
    )

    # CARREGAR TELA INICIAL
    mostrar_tela("visao")

    janela.after(60000, verificar_virada_mes)

    # INICIAR APLICAÇÃO
    janela.mainloop()