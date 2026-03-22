import json
from cerebro import *

init_db()

with open("reglas.json") as f:
    reglas = json.load(f)

categorias = list(reglas.keys())

print("IA Personal iniciada. Escribí algo sobre tu día:\n")

while True:
    texto = input(">> ")

    # 1) Clasificación base (rápida, sin IA)
    categoria = clasificar(texto, reglas)

    # 2) Intento de mejora con IA (si responde)
    cat_ia = clasificar_con_ia(texto, categorias)

    if cat_ia != "general":
        categoria = cat_ia

    # Guardar
    guardar(texto, categoria)

    # Acciones base
    acciones = sugerencia(categoria, reglas)

    # Historial (sin IA)
    historial = obtener_historial(categoria)

    patron = None
    if len(historial) >= 5:
        patron = f"Repetición detectada en {categoria}"

    alerta = generar_alerta(categoria)

    # UNA sola llamada IA
    prompt = f"""
Usuario: {texto}
Categoría: {categoria}
Patrón: {patron if patron else "sin patrón claro"}
Acciones: {acciones}

Respuesta breve y directa.
"""
    if categoria != "general":
     respuesta = preguntar_ia(prompt)
    else:
     respuesta = "Registro guardado."

    print("\nIA:", respuesta)

    if alerta:
        print(alerta)

    if patron:
        print("Patrón:", patron)

    print("Categoría:", categoria)
    print("-" * 50)