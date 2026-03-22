import streamlit as st
import json
import sqlite3
import pandas as pd
import os

from cerebro import (
    init_db,
    clasificar_avanzado,
    clasificar_con_ia,
    guardar,
    sugerencia,
    obtener_historial,
    calcular_score,
    score_temporal,
    alerta_tiempo_real,
    generar_prediccion,
    preguntar_ia
)

# ---------- INIT ----------
init_db()

with open("reglas.json") as f:
    reglas = json.load(f)

categorias = list(reglas.keys())

st.set_page_config(layout="wide")
st.title("🧠 IA Personal")

# ---------- SIDEBAR ----------
st.sidebar.title("📌 Navegación")

seccion = st.sidebar.radio(
    "Ir a:",
    ["💬 Chat", "📊 Dashboard", "🔮 Predicción", "⚙️ Sistema"]
)

# ---------- FUNCIONES ----------
def delta_score(df, area):
    if df is None or df.empty or len(df) < 2:
        return 0
    df = df.sort_values("fecha")
    return int(df.iloc[-1][area] - df.iloc[-2][area])

# ---------- CHAT ----------
if seccion == "💬 Chat":

    st.subheader("💬 Chat")

    with st.form("chat_form"):
        texto = st.text_input("Contame qué pasó hoy")
        submitted = st.form_submit_button("Enviar")

    if submitted and texto:

        categorias_detectadas = clasificar_avanzado(texto, reglas)
        categoria = categorias_detectadas[0]

        try:
            cat_ia = clasificar_con_ia(texto, categorias)
            if cat_ia != "general":
                categoria = cat_ia
        except:
            pass

        acciones = sugerencia(categoria, reglas)

        prompt = f"""
Usuario: {texto}
Categoría: {categoria}
Acciones: {acciones}

Respuesta breve y directa.
"""

        respuesta = preguntar_ia(prompt)

        # ✅ guardar correctamente (después de generar respuesta)
        guardar(texto, categoria, respuesta)

    # ✅ mostrar desde base de datos (NO session_state)
    conn = sqlite3.connect("memoria.db")
    df = pd.read_sql_query("SELECT * FROM registros ORDER BY fecha DESC LIMIT 20", conn)
    conn.close()

    for _, row in df.iterrows():
        st.markdown(f"**Vos:** {row['texto']}")
        st.markdown(f"**IA:** {row['respuesta']}")
        st.markdown("---")

# ---------- DASHBOARD ----------
elif seccion == "📊 Dashboard":

    st.subheader("📊 Estado general")

    # ALERTA
    alerta_rt = alerta_tiempo_real()

    if alerta_rt:
        st.error(alerta_rt)
    else:
        st.success("Sin riesgo detectado")

    # SCORE
    score = calcular_score(reglas)
    df_score = score_temporal(reglas)

    col1, col2, col3 = st.columns(3)

    col1.metric("Laboral", score["laboral"], delta=delta_score(df_score, "laboral"))
    col2.metric("Emocional", score["emocional"], delta=delta_score(df_score, "emocional"))
    col3.metric("Financiero", score["financiero"], delta=delta_score(df_score, "financiero"))

    # EVOLUCIÓN
    st.subheader("📈 Evolución")

    if df_score is not None and not df_score.empty:
        df_score = df_score.sort_values("fecha").set_index("fecha")
        st.line_chart(df_score)
    else:
        st.info("Sin datos suficientes")

    # TOP PROBLEMAS
    conn = sqlite3.connect("memoria.db")
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    conn.close()

    if not df.empty:
        top = df["categoria"].value_counts().head(5)
        st.subheader("⚠️ Principales patrones")
        st.bar_chart(top)

# ---------- PREDICCIÓN ----------
elif seccion == "🔮 Predicción":

    st.subheader("🔮 Predicción de comportamiento")

    try:
        pred = generar_prediccion()
        st.markdown(pred)
    except:
        st.info("Predicción no disponible")

# ---------- SISTEMA ----------
elif seccion == "⚙️ Sistema":

    st.subheader("⚙️ Configuración")

    # RESET DB
    if st.checkbox("Confirmar reset de base"):
        if st.button("🗑 Resetear base"):
            try:
                os.remove("memoria.db")
                st.success("Base eliminada. Reiniciá la app.")
            except:
                st.error("No se pudo eliminar la base")

    # REGISTROS
    st.subheader("📂 Registros")

    conn = sqlite3.connect("memoria.db")
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    conn.close()

    if not df.empty:
        df_mostrar = df.copy()

        df_mostrar["fecha"] = pd.to_datetime(df_mostrar["fecha"]).dt.strftime("%Y-%m-%d %H:%M")
        df_mostrar = df_mostrar[["fecha", "texto", "categoria"]]

        st.dataframe(df_mostrar.tail(20), use_container_width=True)
    else:
        st.info("Sin registros todavía")