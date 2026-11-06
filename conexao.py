import sqlite3
import os
import calendar
import csv
import unicodedata
from datetime import date

CAMINHO_BANCO = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'dados.db'
)

TIPOS_VALIDOS = ("entrada", "saida")


def conectar():
    return sqlite3.connect(CAMINHO_BANCO)


def hoje_iso():
    return date.today().isoformat()


def _consultar(sql, params=(), um=False):
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute(sql, params)
        return cursor.fetchone() if um else cursor.fetchall()
    finally:
        conexao.close()


def _executar(sql, params=()):
    conexao = conectar()
    try:
        conexao.execute(sql, params)
        conexao.commit()
    finally:
        conexao.close()


def criar_tabela():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            tipo TEXT,
            data TEXT
        )
    ''')

    cursor.execute("PRAGMA table_info(lancamentos)")
    colunas = [coluna[1] for coluna in cursor.fetchall()]

    # MIGRAÇÃO: bancos antigos não tinham a coluna "tipo"
    if "tipo" not in colunas:
        cursor.execute("ALTER TABLE lancamentos ADD COLUMN tipo TEXT")
        cursor.execute("""
            UPDATE lancamentos
            SET tipo = CASE WHEN valor < 0 THEN 'saida' ELSE 'entrada' END
        """)

    # MIGRAÇÃO: bancos antigos não tinham a coluna "data"
    if "data" not in colunas:
        cursor.execute("ALTER TABLE lancamentos ADD COLUMN data TEXT")

    # Lançamentos sem data recebem a data de hoje
    cursor.execute("""
        UPDATE lancamentos
        SET data = date('now', 'localtime')
        WHERE data IS NULL OR data = ''
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_lancamentos_data
        ON lancamentos(data)
    """)

    conexao.commit()
    conexao.close()


# ---------------------------------------------------------------
# LANÇAMENTOS: CRIAR, EDITAR, EXCLUIR
# ---------------------------------------------------------------

def adicionar_lancamento(descricao, valor, tipo, data=None):
    if tipo not in TIPOS_VALIDOS:
        raise ValueError("Tipo de lançamento inválido.")

    _executar(
        "INSERT INTO lancamentos (descricao, valor, tipo, data) "
        "VALUES (?, ?, ?, ?)",
        (descricao, abs(valor), tipo, data or hoje_iso())
    )


def atualizar_lancamento(id_lancamento, descricao, valor, tipo, data):
    if tipo not in TIPOS_VALIDOS:
        raise ValueError("Tipo de lançamento inválido.")

    _executar(
        "UPDATE lancamentos SET descricao = ?, valor = ?, tipo = ?, data = ? "
        "WHERE id = ?",
        (descricao, abs(valor), tipo, data, id_lancamento)
    )


def excluir_lancamento(id_lancamento):
    _executar(
        "DELETE FROM lancamentos WHERE id = ?",
        (id_lancamento,)
    )


# ---------------------------------------------------------------
# CONSULTAS
# ---------------------------------------------------------------

def listar_lancamentos(tipo=None):
    if tipo in TIPOS_VALIDOS:
        return _consultar(
            "SELECT id, descricao, valor, tipo FROM lancamentos "
            "WHERE tipo = ? ORDER BY id DESC",
            (tipo,)
        )

    return _consultar(
        "SELECT id, descricao, valor, tipo FROM lancamentos ORDER BY id DESC"
    )


def _normalizar(texto):
    """Minúsculas e sem acentos, para a busca não ser exigente."""
    texto = unicodedata.normalize("NFD", str(texto).casefold())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def _formato_br(valor):
    return (
        f"{valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def buscar_lancamentos(texto="", mes=None, tipo=None, limite=None):
    """Retorna (lista, total_encontrado).

    Cada item: (id, descricao, valor, tipo, data 'AAAA-MM-DD').
    A busca olha descrição, valor (1500,50 / 1.500,50 / 1500.5) e
    data (dd/mm/aaaa), ignorando maiúsculas e acentos.
    """

    condicoes, params = [], []

    if mes:
        condicoes.append("substr(data, 1, 7) = ?")
        params.append(mes)

    if tipo in TIPOS_VALIDOS:
        condicoes.append("tipo = ?")
        params.append(tipo)

    where = ("WHERE " + " AND ".join(condicoes)) if condicoes else ""
    ordem = "ORDER BY data DESC, id DESC"
    colunas = "id, descricao, valor, tipo, data"

    palavras = [p for p in _normalizar((texto or "").strip()).split() if p]

    if not palavras:
        total = _consultar(
            f"SELECT COUNT(*) FROM lancamentos {where}", params, um=True
        )[0]

        sql = f"SELECT {colunas} FROM lancamentos {where} {ordem}"
        if limite:
            sql += " LIMIT ?"
            params = params + [limite]

        return _consultar(sql, params), total

    linhas = _consultar(
        f"SELECT {colunas} FROM lancamentos {where} {ordem}", params
    )

    encontrados = []

    for linha in linhas:
        _, descricao, valor, _, data = linha

        try:
            data_br = date.fromisoformat(data).strftime("%d/%m/%Y")
        except (TypeError, ValueError):
            data_br = ""

        alvo = " ".join([
            _normalizar(descricao),
            f"{abs(valor):.2f}",
            f"{abs(valor):.2f}".replace(".", ","),
            _formato_br(abs(valor)),
            data_br
        ])

        if all(p in alvo for p in palavras):
            encontrados.append(linha)

    total = len(encontrados)

    if limite:
        encontrados = encontrados[:limite]

    return encontrados, total


def obter_totais():
    """Retorna (entradas, saidas, saldo) de TODOS os meses."""
    entradas, saidas = _consultar("""
        SELECT
            COALESCE(SUM(CASE WHEN tipo = 'entrada' THEN ABS(valor) ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN tipo = 'saida' THEN ABS(valor) ELSE 0 END), 0)
        FROM lancamentos
    """, um=True)

    return entradas, saidas, round(entradas - saidas, 2)


def totais_periodo(mes=None):
    """Totais de um mês ('AAAA-MM') ou de todos os meses (mes=None)."""
    where, params = "", []

    if mes:
        where = "WHERE substr(data, 1, 7) = ?"
        params = [mes]

    (entradas, saidas, qtd_entradas, qtd_saidas,
     maior_entrada, maior_saida) = _consultar(f"""
        SELECT
            COALESCE(SUM(CASE WHEN tipo = 'entrada' THEN ABS(valor) END), 0),
            COALESCE(SUM(CASE WHEN tipo = 'saida' THEN ABS(valor) END), 0),
            COALESCE(SUM(CASE WHEN tipo = 'entrada' THEN 1 END), 0),
            COALESCE(SUM(CASE WHEN tipo = 'saida' THEN 1 END), 0),
            COALESCE(MAX(CASE WHEN tipo = 'entrada' THEN ABS(valor) END), 0),
            COALESCE(MAX(CASE WHEN tipo = 'saida' THEN ABS(valor) END), 0)
        FROM lancamentos
        {where}
    """, params, um=True)

    return {
        "entradas": entradas,
        "saidas": saidas,
        "saldo": round(entradas - saidas, 2),
        "qtd_entradas": qtd_entradas,
        "qtd_saidas": qtd_saidas,
        "qtd": qtd_entradas + qtd_saidas,
        "maior_entrada": maior_entrada,
        "maior_saida": maior_saida,
    }


def _proximo_mes(mes):
    ano, numero = map(int, mes.split("-"))
    numero += 1

    if numero > 12:
        ano += 1
        numero = 1

    return f"{ano:04d}-{numero:02d}"


def serie_periodo(mes=None):
    """Série para os gráficos: lista de (chave, entradas, saidas).

    Com mes='AAAA-MM': um item por dia ('AAAA-MM-DD').
    Com mes=None: um item por mês ('AAAA-MM'), sem buracos.
    """

    hoje = date.today()
    mes_hoje = hoje.strftime("%Y-%m")

    soma = """
        SUM(CASE WHEN tipo = 'entrada' THEN ABS(valor) ELSE 0 END),
        SUM(CASE WHEN tipo = 'saida' THEN ABS(valor) ELSE 0 END)
    """

    if mes:
        linhas = _consultar(
            f"SELECT data, {soma} FROM lancamentos "
            f"WHERE substr(data, 1, 7) = ? GROUP BY data",
            (mes,)
        )
        por_dia = {int(d[8:10]): (e, s) for d, e, s in linhas}

        ano, numero = map(int, mes.split("-"))
        ultimo = calendar.monthrange(ano, numero)[1]

        if mes == mes_hoje:
            ultimo = hoje.day

        if por_dia:
            ultimo = max(ultimo, max(por_dia))

        return [
            (f"{mes}-{dia:02d}", *por_dia.get(dia, (0, 0)))
            for dia in range(1, ultimo + 1)
        ]

    linhas = _consultar(
        f"SELECT substr(data, 1, 7), {soma} FROM lancamentos "
        f"WHERE data IS NOT NULL GROUP BY 1 ORDER BY 1"
    )

    if not linhas:
        return []

    por_mes = {m: (e, s) for m, e, s in linhas}
    atual = min(por_mes)
    fim = max(max(por_mes), mes_hoje)

    resultado = []

    while atual <= fim:
        resultado.append((atual, *por_mes.get(atual, (0, 0))))
        atual = _proximo_mes(atual)

    return resultado


def top_por_descricao(tipo, mes=None, limite=5):
    """Maiores totais por descrição: lista de (descricao, total)."""
    condicoes = ["tipo = ?"]
    params = [tipo]

    if mes:
        condicoes.append("substr(data, 1, 7) = ?")
        params.append(mes)

    return _consultar(f"""
        SELECT MIN(TRIM(descricao)), SUM(ABS(valor)) AS total
        FROM lancamentos
        WHERE {" AND ".join(condicoes)}
        GROUP BY LOWER(TRIM(descricao))
        ORDER BY total DESC
        LIMIT ?
    """, params + [limite])


def listar_meses():
    """Meses com movimentação ('AAAA-MM'), do mais novo ao mais antigo.
    O mês atual sempre aparece."""
    linhas = _consultar("""
        SELECT DISTINCT substr(data, 1, 7)
        FROM lancamentos
        WHERE data IS NOT NULL
    """)

    meses = {linha[0] for linha in linhas if linha[0]}
    meses.add(date.today().strftime("%Y-%m"))

    return sorted(meses, reverse=True)


def resumo_mensal():
    """Levantamento de todos os meses, do mais novo ao mais antigo.

    Cada item: mes, entradas, saidas, saldo (do mês), qtd e
    acumulado (saldo somado até o fim daquele mês).
    """
    linhas = _consultar("""
        SELECT
            substr(data, 1, 7),
            SUM(CASE WHEN tipo = 'entrada' THEN ABS(valor) ELSE 0 END),
            SUM(CASE WHEN tipo = 'saida' THEN ABS(valor) ELSE 0 END),
            COUNT(*)
        FROM lancamentos
        WHERE data IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """)

    dados = {mes: (e, s, q) for mes, e, s, q in linhas}
    dados.setdefault(date.today().strftime("%Y-%m"), (0, 0, 0))

    resultado = []
    acumulado = 0

    for mes in sorted(dados):
        entradas, saidas, qtd = dados[mes]
        saldo = round(entradas - saidas, 2)
        acumulado = round(acumulado + saldo, 2)

        resultado.append({
            "mes": mes,
            "entradas": entradas,
            "saidas": saidas,
            "saldo": saldo,
            "qtd": qtd,
            "acumulado": acumulado,
        })

    resultado.reverse()
    return resultado


# ---------------------------------------------------------------
# FECHAMENTO MENSAL: UM ARQUIVO POR MÊS
# ---------------------------------------------------------------

def pasta_meses():
    """Pasta onde ficam os arquivos dos meses (ao lado do dados.db)."""
    return os.path.join(
        os.path.dirname(os.path.abspath(CAMINHO_BANCO)),
        "meses"
    )


def caminho_mes(ano_mes):
    return os.path.join(pasta_meses(), f"{ano_mes}.csv")


def _num_br(valor):
    return f"{valor:.2f}".replace(".", ",")


def exportar_mes(ano_mes):
    """Grava meses/AAAA-MM.csv com todos os lançamentos do mês e o resumo.

    Usa ';' e UTF-8 com BOM, então abre direto no Excel em português.
    Retorna o caminho do arquivo.
    """
    lancamentos, _ = buscar_lancamentos(mes=ano_mes)
    lancamentos = sorted(lancamentos, key=lambda l: (l[4], l[0]))
    totais = totais_periodo(ano_mes)

    os.makedirs(pasta_meses(), exist_ok=True)
    caminho = caminho_mes(ano_mes)
    temporario = caminho + ".tmp"

    with open(temporario, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")

        escritor.writerow(["Data", "Descrição", "Tipo", "Valor (R$)"])

        for _, descricao, valor, tipo, data in lancamentos:
            try:
                data_br = date.fromisoformat(data).strftime("%d/%m/%Y")
            except (TypeError, ValueError):
                data_br = ""

            sinal = "" if tipo == "entrada" else "-"
            escritor.writerow([
                data_br,
                descricao,
                "Entrada" if tipo == "entrada" else "Saída",
                sinal + _num_br(abs(valor))
            ])

        escritor.writerow([])
        escritor.writerow(["RESUMO", ano_mes])
        escritor.writerow(["Total de entradas", "", "", _num_br(totais["entradas"])])
        escritor.writerow(["Total de saídas", "", "", _num_br(totais["saidas"])])
        escritor.writerow(["Saldo do mês", "", "", _num_br(totais["saldo"])])
        escritor.writerow(["Movimentações", "", "", totais["qtd"]])

    # grava por inteiro ou não grava: nunca deixa arquivo pela metade
    os.replace(temporario, caminho)
    return caminho


def fechar_meses_encerrados():
    """Cria o arquivo de todo mês que já terminou e ainda não tem um.

    Retorna a lista de meses fechados agora. O mês atual nunca é fechado.
    """
    atual = date.today().strftime("%Y-%m")
    fechados = []

    for ano_mes in sorted(listar_meses()):
        if ano_mes >= atual:
            continue

        if not os.path.exists(caminho_mes(ano_mes)):
            exportar_mes(ano_mes)
            fechados.append(ano_mes)

    return fechados