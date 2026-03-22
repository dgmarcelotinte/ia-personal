import sqlite3
import pandas as pd
import streamlit as st
import json
from cerebro import calcular_score, score_temporal
from cerebro import generar_prediccion
from cerebro import alerta_tiempo_real

st.title("IA Personal - Dashboard")

# -------- CARGA DE REGLAS --------
with open("reglas.json") as f:
    reglas = json.load(f)

# -------- SCORE ACTUAL --------
score = calcular_score(reglas)

# -------- EVOLUCIÓN (necesaria para delta) --------
df_score = score_temporal(reglas)

def delta_score(df, area):
    if df is None or df.empty or len(df) < 2:
        return 0
    df = df.sort_values("fecha")
    return int(df.iloc[-1][area] - df.iloc[-2][area])

st.subheader("Score actual")

col1, col2, col3 = st.columns(3)
col1.metric("Laboral", score["laboral"], delta=delta_score(df_score, "laboral"))
col2.metric("Emocional", score["emocional"], delta=delta_score(df_score, "emocional"))
col3.metric("Financiero", score["financiero"], delta=delta_score(df_score, "financiero"))

# -------- EVOLUCIÓN VISUAL --------
st.subheader("Evolución por día")

if df_score is not None and not df_score.empty:
    df_score = df_score.sort_values("fecha")
    df_score = df_score.set_index("fecha")
    st.line_chart(df_score)
else:
    st.warning("No hay suficientes datos para mostrar evolución")

# -------- DATOS CRUDOS --------
conn = sqlite3.connect("memoria.db")
df = pd.read_sql_query("SELECT * FROM registros", conn)
conn.close()

st.subheader("Registros recientes")

if df.empty:
    st.warning("No hay registros todavía. Ejecutá main.py primero.")
else:
    st.dataframe(df.tail(20))

# -------- BALANCE CONDUCTUAL --------
st.subheader("Balance conductual")

def obtener_tipo(cat):
    if cat in reglas:
        return reglas[cat].get("tipo", "otro")
    return "otro"

if not df.empty:
    df["tipo"] = df["categoria"].apply(obtener_tipo)
    st.bar_chart(df["tipo"].value_counts())
else:
    st.info("Sin datos para balance conductual")

    from cerebro import generar_prediccion

st.subheader("Predicción de comportamiento")

pred = generar_prediccion()
st.warning(pred)

@st.cache_data
def obtener_prediccion():
    return generar_prediccion()

st.subheader("Alerta en tiempo real")

alerta = alerta_tiempo_real()

if alerta:
    st.error(alerta)
else:
    st.success("Sin riesgo detectado ahora")