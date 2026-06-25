# Lab — Sesión 5: Más allá del no-code con ADK
### AI News Business · Track Técnico · Google News Initiative × Marktube

Esta guía es tu copiloto durante el taller. Tiene todo el código listo para copiar.
La meta no es leerla completa: es **tener un agente corriendo** y entender por qué corre.

> Repo starter incluido: carpeta `newsroom_agent/`. Si no quieres teclear todo, úsala.

---

## 0. Antes de empezar (5 min)

Necesitas:

- **Python 3.10 o superior** — verifica con `python --version`
- Un editor (VS Code) y una terminal
- Una **API key de Gemini** gratis: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

---

## 1. Tu primer agente (Hands-on #1 · ~10 min)

Sigue el codelab oficial de Google: **goo.gle/your-first-agent-with-adk**
([codelabs.developers.google.com/your-first-agent-with-adk](https://codelabs.developers.google.com/your-first-agent-with-adk)).

```bash
# Entorno aislado
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Instala ADK
pip install google-adk

# Crea el proyecto
adk create editor_nova
# pega tu API key en editor_nova/.env

# Levanta la UI de desarrollo
adk web
# abre http://localhost:8000 y selecciona tu agente
```

**Meta del bloque:** tu agente responde en `localhost:8000`, le agregaste una
herramienta (la del clima del codelab) y abriste la pestaña **Trace** para ver
qué pensó y qué llamó.

### La pieza mínima

Un agente son cuatro cosas: **modelo + instrucción + herramientas + memoria.**
En código cabe en una pantalla:

```python
from google.adk.agents import Agent

root_agent = Agent(
    model="gemini-flash-latest",
    name="editor_nova",
    instruction="""Eres asistente de redacción.
                   Resume claro y propón titulares.""",
    tools=[publicar_en_cms],
)
```

### El docstring es la magia

Una herramienta es una función normal de Python. **El modelo lee tu docstring**
para decidir cuándo y cómo usarla. Tres reglas de oro:

1. Describe **qué hace** y **cuándo usarla** — el modelo lo lee literal.
2. **Tipa** los argumentos (`titulo: str`). ADK arma el contrato solo.
3. Devuelve un **dict con `status`** para que el agente sepa si salió bien.

```python
def publicar_en_cms(titulo: str, cuerpo: str) -> dict:
    """Crea una nota en BORRADOR en el CMS.

    Úsala cuando el contenido esté listo para revisión humana.
    NUNCA publica en vivo.

    Args:
        titulo: titular propuesto.
        cuerpo: texto de la nota.
    Returns:
        dict con status y url del borrador.
    """
    ...
    return {"status": "ok", "url": "..."}
```

---

## 2. Agentic workflows: encadenar tareas (Hands-on #2 · ~15 min)

Un agente es útil. **Varios agentes encadenados automatizan un proceso completo.**
El patrón es `SequentialAgent` + `output_key`:

```
transcribir ─▶ resumir ─▶ categorizar ─▶ titular ─▶ borrador
output_key:   "transcripcion"  "resumen"   "categoria"  "titulares"
```

El **estado compartido** es tu pizarrón: lo que un paso escribe con
`output_key="resumen"`, el siguiente lo lee inyectando `{resumen}` en su
instrucción.

```python
from google.adk.agents import LlmAgent, SequentialAgent

M = "gemini-flash-latest"

resumir = LlmAgent(
    name="resumir", model=M, output_key="resumen",
    instruction="Resume en 3 líneas: {transcripcion}",
)

titular = LlmAgent(
    name="titular", model=M, output_key="titulares",
    instruction="Propón 3 títulos para: {resumen}",
)

root_agent = SequentialAgent(
    name="redaccion",
    sub_agents=[transcribir, resumir, categorizar, titular],
)
```

> El pipeline completo (5 pasos + herramienta de CMS) está en
> **`newsroom_agent/agent.py`**. Cópialo a tu carpeta, corre `adk web` desde la
> carpeta padre y prueba pegando un texto que simule la transcripción de un audio.

### El remate: conecta tu CMS

Aquí el agente deja de pensar y **actúa** — pero con **humano en el bucle**.
La herramienta crea un **BORRADOR**; la persona revisa y publica.

```python
publicar = LlmAgent(
    name="publicar", model=M, tools=[publicar_en_cms],
    instruction="""Toma {titulares} y {resumen}. Llama a publicar_en_cms
                   para crear el BORRADOR. Reporta la URL.""",
)
```

El no-code no tenía tu CMS en su catálogo. Aquí, un `requests.post` con tu auth
y tus headers lo resuelve. **Tú pones las reglas**: valida longitud, groserías o
datos sensibles antes de tocar el CMS.

---

## 3. Reto final (~18 min)

**Misión:** vuelve real tu pipeline en ADK.

1. Toma el pipeline que dibujaste en papel.
2. Mínimo **2 pasos encadenados** con `SequentialAgent` y `output_key`.
3. Al menos **1 herramienta propia** (vale un mock que devuelva un dict de prueba).
4. Corre en `adk web` y muestra en **Trace** cómo fluye el dato.
5. **Bonus:** la última herramienta crea un BORRADOR (real o simulado).

**Se vale ganar así:**

- Corre sin tronar → funciona
- El dato salta entre pasos → está encadenado
- La herramienta se llama sola → es agente, no script
- Lo puedes explicar en 60 segundos → lo entendiste

---

## 4. ¿Cuándo NO bajar al código?

Code-first no es religión. **Quédate en no-code** si es un flujo de 2 pasos que no
va a crecer, los conectores oficiales ya cubren tus apps, o solo necesitas un demo
para mañana. **Baja a ADK** cuando haya lógica de verdad (ramas, reintentos,
validaciones), tengas que tocar tu CMS o una API sin conector, vaya a correr a
volumen, o necesites versionar y testear sin depender de una sola persona.

---

## 5. Chuleta ADK

| Quiero…             | Escribo…                                            |
|---------------------|-----------------------------------------------------|
| Instalar            | `pip install google-adk`                            |
| Crear proyecto      | `adk create mi_agente`                              |
| Probar (CLI)        | `adk run mi_agente`                                 |
| UI de desarrollo    | `adk web` → `localhost:8000`                        |
| Un agente           | `Agent(model=, name=, instruction=, tools=[])`      |
| Una herramienta     | `def fn(x: str) -> dict:` + docstring claro         |
| Encadenar           | `SequentialAgent(sub_agents=[a, b, c])`             |
| Pasar datos         | `output_key="k"` → leer con `{k}`                   |

---

## 6. Problemas comunes

- **`API key not valid`** → revisa que copiaste la llave completa, sin espacios.
- **`GOOGLE_API_KEY not found`** → el archivo debe llamarse exactamente `.env`
  y estar dentro de la carpeta del agente.
- **`Address already in use` (puerto 8000)** → cierra el `adk web` anterior
  (Ctrl + C) o corre `adk web --port 8001`.
- **El agente no llama a tu herramienta** → casi siempre el docstring no es claro.
  Describe mejor *cuándo* usarla.

---

## 7. Tu tarea (post-sesión)

1. **Avanza el path de ADK** en [skills.google](https://www.skills.google/course_templates/1382?locale=es) (curso 1382). Trae tu badge.
2. **Presume tu agente:** sube foto o video de tu agente corriendo solo y
   etiqueta a **@Google**, **@Marktube** y **@NovaCode**.

> Lo que construiste aquí es el germen de tu **blueprint** para el Taller de
> Prototipado. Llévalo allá y conviértelo en el proyecto de tu medio.
