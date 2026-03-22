from fastapi import FastAPI
from pydantic import BaseModel
import json

from cerebro import (
    init_db,
    clasificar_avanzado,
    clasificar_con_ia,
    guardar,
    sugerencia,
    preguntar_ia
)

app = FastAPI()

init_db()

with open("reglas.json") as f:
    reglas = json.load(f)

categorias = list(reglas.keys())


class InputUsuario(BaseModel):
    texto: str


@app.post("/chat")
def chat(data: InputUsuario):

    texto = data.texto

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

    guardar(texto, categoria, respuesta)

    return {
        "respuesta": respuesta,
        "categoria": categoria,
        "acciones": acciones
    }