"""
Agente de redacción — pipeline ADK para AI News Business (Track Técnico, Sesión 5).

Pipeline secuencial: limpiar transcripción -> resumir -> categorizar -> titular -> borrador.
Cada sub-agente deja su resultado en el estado con `output_key` y el siguiente lo lee
inyectando {clave} en su instrucción. El último sub-agente llama a una herramienta
(publicar_en_cms) que crea un BORRADOR — nunca publica en vivo.

Cómo correr:
  1) pip install google-adk
  2) copia .env.example a .env y pega tu GOOGLE_API_KEY (de Google AI Studio)
  3) desde la carpeta padre:  adk web   ->   abre http://localhost:8000
  4) en el chat, pega un texto que simule la transcripción de un audio del corresponsal.

Reto: cambia las instrucciones, agrega un paso (p. ej. detectar nombres propios)
o conecta publicar_en_cms a la API real de tu CMS.
"""

import datetime
from google.adk.agents import LlmAgent, SequentialAgent

MODEL = "gemini-flash-latest"  # barato y rápido para arrancar


# --------------------------------------------------------------------------- #
# HERRAMIENTA PROPIA: el agente "actúa" sobre tu CMS.
# Aquí está como mock para que corra sin credenciales. La versión real está
# comentada abajo: es solo un requests.post a TU endpoint, con TU auth.
# --------------------------------------------------------------------------- #
def publicar_en_cms(titulo: str, cuerpo: str, categoria: str) -> dict:
    """Crea una nota en estado BORRADOR en el CMS del medio.

    Úsala cuando el contenido ya esté resumido, categorizado y con un titular
    propuesto, y esté listo para revisión humana. NUNCA publica en vivo: solo
    deja el borrador para que un editor lo apruebe.

    Args:
        titulo: el titular propuesto para la nota.
        cuerpo: el texto (resumen) de la nota.
        categoria: la sección destino (p. ej. "regional", "clima", "sismo").

    Returns:
        dict con el status de la operación y la URL del borrador creado.
    """
    folio = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    # --- Versión real (descomenta y ajusta a tu CMS) ---
    # import os, requests
    # resp = requests.post(
    #     os.environ["CMS_DRAFT_URL"],
    #     headers={"Authorization": f"Bearer {os.environ['CMS_TOKEN']}"},
    #     json={"title": titulo, "body": cuerpo,
    #           "section": categoria, "status": "draft"},
    #     timeout=15,
    # )
    # resp.raise_for_status()
    # return {"status": "ok", "url": resp.json()["url"]}

    # --- Mock para el taller ---
    return {
        "status": "ok",
        "estado": "BORRADOR (pendiente de revisión humana)",
        "url": f"https://cms.tu-medio.test/borradores/{folio}",
        "categoria": categoria,
    }


# --------------------------------------------------------------------------- #
# SUB-AGENTES: cada uno hace UNA cosa y la pasa al siguiente vía output_key.
# --------------------------------------------------------------------------- #
limpiar = LlmAgent(
    name="limpiar_transcripcion",
    model=MODEL,
    description="Limpia una transcripción cruda de audio.",
    instruction=(
        "Recibes la transcripción cruda de un audio enviado por un corresponsal. "
        "Quita muletillas, repeticiones y ruido. NO inventes datos. "
        "Devuelve únicamente el texto limpio, fiel a lo que se dijo."
    ),
    output_key="transcripcion",
)

resumir = LlmAgent(
    name="resumir",
    model=MODEL,
    description="Resume el texto en 3 a 4 líneas claras.",
    instruction=(
        "Resume en 3 o 4 líneas, en español neutro y claro, el siguiente texto:\n\n"
        "{transcripcion}\n\n"
        "Conserva los hechos y cifras. No agregues opiniones."
    ),
    output_key="resumen",
)

categorizar = LlmAgent(
    name="categorizar",
    model=MODEL,
    description="Asigna una sección al contenido.",
    instruction=(
        "Clasifica el siguiente resumen en UNA sola sección de esta lista: "
        "regional, política, clima, sismo, economía, deportes, cultura.\n\n"
        "Resumen: {resumen}\n\n"
        "Devuelve solo la palabra de la sección, en minúsculas."
    ),
    output_key="categoria",
)

titular = LlmAgent(
    name="titular",
    model=MODEL,
    description="Propone titulares editoriales.",
    instruction=(
        "Propón 3 titulares para esta nota. Claros, sin clickbait, máx. 12 palabras.\n\n"
        "Resumen: {resumen}\n"
        "Sección: {categoria}\n\n"
        "Devuelve los 3 titulares numerados."
    ),
    output_key="titulares",
)

publicar = LlmAgent(
    name="publicar",
    model=MODEL,
    description="Crea el borrador en el CMS usando la herramienta.",
    tools=[publicar_en_cms],
    instruction=(
        "Tienes un resumen ({resumen}), una sección ({categoria}) y titulares "
        "propuestos ({titulares}). Elige el MEJOR titular y llama a la herramienta "
        "publicar_en_cms con ese titulo, el resumen como cuerpo y la categoria. "
        "Reporta al usuario la URL del borrador y recuérdale que un editor debe "
        "revisarlo antes de publicar."
    ),
)


# --------------------------------------------------------------------------- #
# ROOT: encadena todo en orden estricto. Esto es el "agentic workflow".
# --------------------------------------------------------------------------- #
root_agent = SequentialAgent(
    name="redaccion",
    description="Pipeline supervisado: de audio del corresponsal a borrador en el CMS.",
    sub_agents=[limpiar, resumir, categorizar, titular, publicar],
)
