import sqlite3
import datetime
import requests
import pandas as pd


DB = "memoria.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS registros (
        id INTEGER PRIMARY KEY,
        fecha TEXT,
        texto TEXT,
        categoria TEXT,
        respuesta TEXT
        )
        """)
    conn.commit()
    conn.close()

    

def guardar(texto, categoria, respuesta):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
        INSERT INTO registros (fecha, texto, categoria, respuesta)
        VALUES (?, ?, ?, ?)
    """, (str(datetime.datetime.now()), texto, categoria, respuesta))

    conn.commit()
    conn.close()

def clasificar_avanzado(texto, reglas):
    texto = texto.lower()
    categorias_detectadas = []

    for categoria, data in reglas.items():
        triggers = data.get("triggers", [])

        for trigger in triggers:
            if trigger in texto:
                categorias_detectadas.append(categoria)
                break

    return categorias_detectadas if categorias_detectadas else ["general"]

def clasificar_con_ia(texto, categorias):
    prompt = f"""
    Clasificá el texto en UNA categoría exacta.

    Categorías posibles:
    {categorias}

    IMPORTANTE:
    - Algunas categorías son positivas (logros)
    - Otras son negativas (problemas)

    Texto: {texto}

    Respondé SOLO con una categoría exacta de la lista.
    """ 

    respuesta = preguntar_ia(prompt).strip().lower()

    for cat in categorias:
        if cat in respuesta:
            return cat

    return "general"

def obtener_historial(categoria, limite=20):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
        SELECT fecha, texto FROM registros
        WHERE categoria = ?
        ORDER BY fecha DESC
        LIMIT ?
    """, (categoria, limite))

    datos = c.fetchall()
    conn.close()
    return datos

def analizar_patron(categoria):
    historial = obtener_historial(categoria)

    if len(historial) < 5:
        return None

    textos = "\n".join([h[1] for h in historial])

    prompt = f"""
    Analizá estos registros de una persona:

    {textos}

    Detectá si hay un patrón repetitivo.
    Explicalo en 1 frase concreta.
    """

    return preguntar_ia(prompt)

def analizar_patrones_temporales():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT fecha, categoria FROM registros", conn)
    conn.close()

    if df.empty:
        return None

    df["fecha"] = pd.to_datetime(df["fecha"])
    df["hora"] = df["fecha"].dt.hour
    df["dia_semana"] = df["fecha"].dt.day_name()

    return df

def detectar_horas_criticas():
    df = analizar_patrones_temporales()
    if df is None:
        return None

    conteo = df.groupby(["hora", "categoria"]).size().reset_index(name="cantidad")

    # Ordenar por mayor frecuencia
    top = conteo.sort_values("cantidad", ascending=False).head(5)

    return top

def detectar_dias_criticos():
    df = analizar_patrones_temporales()
    if df is None:
        return None

    conteo = df.groupby(["dia_semana", "categoria"]).size().reset_index(name="cantidad")

    top = conteo.sort_values("cantidad", ascending=False).head(5)

    return top

import datetime

def alerta_tiempo_real():
    df = analizar_patrones_temporales()

    if df is None or df.empty:
        return None

    ahora = datetime.datetime.now()
    hora_actual = ahora.hour

    # contar problemas por hora
    conteo = df.groupby(["hora", "categoria"]).size().reset_index(name="cantidad")

    # filtrar hora actual
    actuales = conteo[conteo["hora"] == hora_actual]

    if actuales.empty:
        return None

    # tomar el más frecuente
    top = actuales.sort_values("cantidad", ascending=False).iloc[0]

    categoria = top["categoria"]
    cantidad = top["cantidad"]

    if cantidad < 2:
        return None

    return f"⚠️ Posible {categoria} en este horario ({hora_actual}:00)"

def generar_prediccion():
    horas = detectar_horas_criticas()
    dias = detectar_dias_criticos()

    if horas is None or dias is None:
        return "No hay suficientes datos aún"

    resumen = f"""
Datos:

Horas críticas:
{horas.to_string(index=False)}

Días críticos:
{dias.to_string(index=False)}

Generá una predicción en este formato EXACTO:

Riesgo principal:
- (qué problema)

Cuándo ocurre:
- (hora + día)

Causa probable:
- (explicación corta)

Acción preventiva:
- (acción concreta y aplicable)
"""

    return preguntar_ia(resumen)

def generar_alerta(categoria):
    historial = obtener_historial(categoria)

    if len(historial) >= 5:
        return f"⚠️ Repetición detectada en '{categoria}' (últimos registros)"
    return None


def sugerencia(categoria, reglas):
    if categoria in reglas:
        return reglas[categoria]["acciones"]
    return ["reflexionar sobre la situación"]

def calcular_score(reglas):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT categoria FROM registros")
    datos = c.fetchall()
    conn.close()

    # Base 100 por área
    score = {
        "laboral": 100,
        "emocional": 100,
        "financiero": 100
    }

    for (cat,) in datos:
        if cat in reglas:
            area = reglas[cat].get("area")
            impacto = reglas[cat].get("impacto", 0)

            if area in score:
                score[area] += impacto

    # Clamp (0–100)
    for k in score:
        score[k] = max(0, min(100, score[k]))

    return score

def score_temporal(reglas):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT fecha, categoria FROM registros", conn)
    conn.close()

    df["fecha"] = pd.to_datetime(df["fecha"])
    df["dia"] = df["fecha"].dt.date

    resultados = []

    for dia, grupo in df.groupby("dia"):
        score = {
            "laboral": 100,
            "emocional": 100,
            "financiero": 100
        }

        for cat in grupo["categoria"]:
            if cat in reglas:
                area = reglas[cat].get("area")
                impacto = reglas[cat].get("impacto", 0)
                if area in score:
                    score[area] += impacto

        score["fecha"] = dia
        resultados.append(score)

    return pd.DataFrame(resultados)

def preguntar_ia(prompt):
    try:
        API_KEY = "AIzaSyBxvzEwlzF4miQw6AkxNGGIxZ_yqcLntyw"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

        response = requests.post(
            url,
            json={
                "contents": [
                    {"parts": [{"text": prompt}]}
                ]
            },
            timeout=15
        )

        data = response.json()

        # DEBUG real
        if "candidates" not in data:
            return f"Error Gemini API: {data}"

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        return f"Error Gemini: {e}"
    
    