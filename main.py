import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from groq import Groq 
import os
from dotenv import load_dotenv

# Inicializar el cliente de Groq
load_dotenv()
client = Groq()

st.set_page_config(page_title="Eddy_Sync", layout="wide", initial_sidebar_state="collapsed")

# --- 1. CONFIGURACIÓN DE RUTINAS Y EJERCICIOS ---
RUTINAS = {
    "Tren Inferior": {
        "Cuádriceps (Prensa)": {
            "imagen": "https://images.unsplash.com/photo-1434608519344-49d77a699e1d?q=80&w=400", # Piernas/Foco inferior
            "nota": "Enfoque en pierna afectada por hemiparesia."
        },
        "Isquiotibiales (Curl)": {
            "imagen": "https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?q=80&w=400", 
            "nota": "Controlar extensión máxima."
        },
        "Extensión de Cadera (Polea Baja)": {
            "imagen": "https://images.unsplash.com/photo-1574680096145-d05b474e2155?q=80&w=400", # Glúteo/Cadera
            "nota": "Activación del glúteo mayor y control de la extensión de cadera afectada."
        },
        "Abductores (Polea Baja)": {
            "imagen": "https://images.unsplash.com/photo-1434608519344-49d77a699e1d?q=80&w=400",
            "nota": "Estabilización de la pelvis. Evitar compensación con el tronco."
        }
    },
    "Tren Superior": {
        "Bíceps (Polea)": {
            "imagen": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?q=80&w=400", # Brazos
            "nota": "Asistencia en agarre si es necesario."
        },
        "Pectoral (Press)": {
            "imagen": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?q=80&w=400", # Pectoral/Torso
            "nota": "Simetría en el empuje."
        },
        "Tríceps (Extensión en Polea Alta)": {
            "imagen": "https://images.unsplash.com/photo-1593079831268-3381b0db4a77?q=80&w=400",
            "nota": "Fomentar la extensión del codo afectado. Controlar el retorno excéntrico."
        },
        "Espalda (Remo sentado en Polea)": {
            "imagen": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=400", # Espalda posterior
            "nota": "Retracción escapular bilateral para corregir la postura asimétrica del hombro."
        },
        "Hombro (Elevación Lateral en Polea)": {
            "imagen": "https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?q=80&w=400", # Deltoides/Hombro
            "nota": "Evitar subluxación del hombro afectado regulando una carga muy baja."
        }
    },
    "Core y Estabilidad": {
        "Abdomen (Rotación)": {
            "imagen": "https://images.unsplash.com/photo-1518310383802-640c2de311b2?q=80&w=400", # Abdominales/Core
            "nota": "Estabilización de tronco en bipedestación."
        },
        "Core (Press Pallof en Polea)": {
            "imagen": "https://images.unsplash.com/photo-1518310383802-640c2de311b2?q=80&w=400",
            "nota": "Resistencia isométrica antirrotación para mejorar el control postural central."
        },
        "Flexión Lateral de Tronco (Polea Baja)": {
            "imagen": "https://images.unsplash.com/photo-1518310383802-640c2de311b2?q=80&w=400",
            "nota": "Fortalecimiento de cuadrados lumbares y oblicuos para mejorar la marcha."
        }
    }
}

# --- 2. GESTIÓN DEL ESTADO ---
if 'alto_contraste' not in st.session_state:
    st.session_state.alto_contraste = False
if 'resistencia' not in st.session_state:
    st.session_state.resistencia = 50  
if 'discapacidad' not in st.session_state:
    st.session_state.discapacidad = "Secuela de ictus"
if 'historial_fatiga' not in st.session_state:
    st.session_state.historial_fatiga = [20, 22, 25, 24, 28, 30] 
if 'explicacion_ia' not in st.session_state:
    st.session_state.explicacion_ia = "Iniciando sistema adaptativo con IA..."
if 'grupo_seleccionado' not in st.session_state:
    st.session_state.grupo_seleccionado = list(RUTINAS.keys())[0]
if 'ejercicio_idx' not in st.session_state:
    st.session_state.ejercicio_idx = 0

# EXPLICACIÓN INGENIERIL: Forzamos el rerun en el callback para redibujar los estilos alterados
def toggle_contraste():
    st.session_state.alto_contraste = not st.session_state.alto_contraste
    st.rerun()

# --- 3. FUNCIÓN DE CONEXIÓN CON GROQ ---
def consultar_ia_resistencia(ppm, o2, discapacidad, resistencia_actual, ejercicio, grupo):
    prompt = f"""
    Eres un sistema experto en neurorrehabilitación y entrenamiento adaptativo post-ictus.
    
    DATOS DEL PACIENTE:
    - Discapacidad: {discapacidad}
    - Frecuencia Cardíaca Actual: {ppm} PPM
    - Saturación de Oxígeno (O2): {o2}%
    - Resistencia Actual del equipo: {resistencia_actual}%
    
    CONTEXTO DEL EJERCICIO:
    - Grupo Muscular: {grupo}
    - Ejercicio Actual: {ejercicio}

    Tu tarea es calcular el nuevo nivel de resistencia (0 a 100) más seguro y eficiente para el paciente.
    - Si las PPM son peligrosamente altas (>150), debes bajar la resistencia drásticamente.
    - Si los parámetros son estables, mantén o sube ligeramente para promover la neuroplasticidad, adaptándote al grupo muscular.
    
    RESPONDE ESTRICTAMENTE en este formato de dos líneas:
    NIVEL: [Número del 0 al 100]
    MOTIVO: [Breve explicación de 1 frase estilo boceto/médico]
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        texto = response.choices[0].message.content
        lineas = texto.strip().split("\n")
        nuevo_nivel = resistencia_actual
        motivo = "Error al procesar recomendación."
        
        for linea in lineas:
            if linea.startswith("NIVEL:"):
                nuevo_nivel = int(linea.replace("NIVEL:", "").strip().replace("%", ""))
            elif linea.startswith("MOTIVO:"):
                motivo = linea.replace("MOTIVO:", "").strip()
        return nuevo_nivel, motivo
    except Exception as e:
        return resistencia_actual, f"Error de conexión con Groq: {str(e)}"


# --- 4. INYECCIÓN DE CSS (Optimizado para sobreescribir Streamlit dinámicamente) ---
if st.session_state.alto_contraste:
    # Combinamos todo en un único bloque sólido que destruye el CSS por defecto si está activo
    font_css = """
    <style>
    /* Fondo negro absoluto e hilos amarillo puro de accesibilidad (WCAG AAA) */
    .stApp, [data-testid="stSidebar"] { 
        background-color: #000000 !important; 
    }
    h1, h2, h3, p, span, div, label, strong, .stMarkdown { 
        color: #FFFF00 !important; 
    }
    /* Forzar que los textos de los sliders y cajas de texto muten a amarillo */
    .stSlider, div[data-baseweb="select"] *, input {
        color: #FFFF00 !important;
    }
    /* Botones de alto contraste */
    .stButton>button { 
        border: 3px solid #FFFF00 !important; 
        color: #000000 !important; 
        background-color: #FFFF00 !important;
        font-weight: bold !important;
        font-size: 18px !important;
    }
    .stButton>button:hover { 
        background-color: #ffffff !important;
        color: #000000 !important;
        border-color: #ffffff !important;
    }
    </style>
    """
else:
    font_css = """
    <style>
    .stApp { background-color: #1a1a1a !important; color: #e5e5e5 !important; }
    .stButton>button {
        border: 2px solid white !important;
        border-radius: 15px !important;
        background-color: transparent !important;
        color: white !important;
        font-size: 18px !important;
        transition: 0.3s;
    }
    .stButton>button:hover { border-color: #a855f7 !important; color: #a855f7 !important; }
    </style>
    """
st.markdown(font_css, unsafe_allow_html=True)


# --- 5. INTERFAZ GRÁFICA ---
st.markdown("<h1 style='text-align: center; font-size: 40px;'>Modo Entrenamiento (IA Activa)</h1>", unsafe_allow_html=True)

# --- SIMULADOR EN LA BARRA LATERAL ---
st.sidebar.markdown("### 🛠️ Simulador de Constantes")
sim_ppm = st.sidebar.slider("Pulso (PPM)", min_value=60, max_value=200, value=120, step=5)
sim_o2 = st.sidebar.slider("Saturación O2 (%)", min_value=80, max_value=100, value=98, step=1)
st.session_state.discapacidad = st.sidebar.text_input("Perfil de Discapacidad:", value=st.session_state.discapacidad)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏋️ Selección de Rutina")

grupo_seleccionado = st.sidebar.selectbox(
    "Selecciona Grupo Muscular:", 
    options=list(RUTINAS.keys()),
    index=list(RUTINAS.keys()).index(st.session_state.grupo_seleccionado)
)

if grupo_seleccionado != st.session_state.grupo_seleccionado:
    st.session_state.grupo_seleccionado = grupo_seleccionado
    st.session_state.ejercicio_idx = 0

ejercicios_disponibles = list(RUTINAS[st.session_state.grupo_seleccionado].keys())
ejercicio_actual = ejercicios_disponibles[st.session_state.ejercicio_idx]

if st.sidebar.button("Siguiente ejercicio ➡️", use_container_width=True):
    with st.spinner("Groq adaptando carga para el siguiente ejercicio..."):
        st.session_state.ejercicio_idx = (st.session_state.ejercicio_idx + 1) % len(ejercicios_disponibles)
        ejercicio_actual = ejercicios_disponibles[st.session_state.ejercicio_idx]
        
        nuevo_val, motivo = consultar_ia_resistencia(
            sim_ppm, sim_o2, st.session_state.discapacidad, 
            st.session_state.resistencia, ejercicio_actual, st.session_state.grupo_seleccionado
        )
        st.session_state.resistencia = nuevo_val
        st.session_state.explicacion_ia = motivo
        st.session_state.historial_fatiga.append(nuevo_val)
        st.rerun()

# --- ALERTAS DINÁMICAS ---
# Si está activado el alto contraste, anulamos los colores suaves para mantener la accesibilidad visual estricta
if st.session_state.alto_contraste:
    alerta_style = "border: 3px solid #FFFF00; color: #FFFF00;"
    texto_alerta = "⚠️ Verificar Estado"
else:
    alerta_style = "border: 2px solid #22c55e; color: #4ade80;"
    texto_alerta = "✅ Estado General: Estable"
    if sim_ppm > 150:
        alerta_style = "border: 2px solid #ef4444; background-color: rgba(239, 68, 68, 0.1); color: #f87171;"
        texto_alerta = "⚠️ Alerta de emergencia:<br>PPM demasiado elevadas"
    elif sim_o2 < 93:
        alerta_style = "border: 2px solid #f59e0b; background-color: rgba(245, 158, 11, 0.1); color: #fbbf24;"
        texto_alerta = "⚠️ Alerta de Hipoxia:<br>Saturación de O2 baja"

vitals_html = f"""
<div style="border: 2px solid { '#FFFF00' if st.session_state.alto_contraste else '#fff' }; border-radius: 25px; padding: 20px; text-align: center; margin-bottom: 30px; margin-top: 10px;">
    <h3 style="margin-top: 0; font-size: 24px; margin-bottom: 20px;">Constantes vitales en tiempo real</h3>
    <div style="display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap; gap: 15px;">
        <div style="border: 2px solid { '#FFFF00' if st.session_state.alto_contraste else '#3b82f6' }; border-radius: 15px; padding: 10px 25px; color: { '#FFFF00' if st.session_state.alto_contraste else '#60a5fa' };">
            🫁 o2 -> {sim_o2}%
        </div>
        <div style="border: 2px solid { '#FFFF00' if st.session_state.alto_contraste else '#22c55e' }; border-radius: 15px; padding: 10px 25px; color: { '#FFFF00' if st.session_state.alto_contraste else '#4ade80' };">
            ❤️ PPM -> {sim_ppm}
        </div>
        <div style="{alerta_style} border-radius: 15px; padding: 10px 25px;">
            {texto_alerta}
        </div>
    </div>
</div>
"""
st.markdown(vitals_html, unsafe_allow_html=True)

# --- LAYOUT DE COLUMNAS ---
col_izq, col_der = st.columns([1, 1], gap="large")

with col_izq:
    st.markdown("<h3>Parámetros del entrenamiento:</h3>", unsafe_allow_html=True)
    st.write(f"**Paciente:** {st.session_state.discapacidad}")
    st.write(f"**Grupo Muscular Activo:** {st.session_state.grupo_seleccionado}")
    
    # --- RESALTADO DEL EJERCICIO ACTUAL (Diseño de Ingeniería de Interfaz) ---
    color_resaltado = "#FFFF00" if st.session_state.alto_contraste else "#a855f7"
    color_texto_resaltado = "#000000" if st.session_state.alto_contraste else "#ffffff"
    bg_resaltado = "#000000" if st.session_state.alto_contraste else "rgba(168, 85, 247, 0.1)"
    border_width = "3px" if st.session_state.alto_contraste else "1px"

    ejercicio_html = f"""
    <div style="
        background-color: {bg_resaltado}; 
        border: {border_width} solid {color_resaltado}; 
        border-radius: 15px; 
        padding: 15px; 
        margin-top: 15px; 
        margin-bottom: 15px;
        text-align: center;
    ">
        <span style="font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: {'#FFFF00' if st.session_state.alto_contraste else '#9ca3af'};">Ejercitando ahora:</span>
        <h2 style="margin: 5px 0 0 0; font-size: 32px; color: {color_resaltado} !important; font-weight: 800;">
            {ejercicio_actual}
        </h2>
    </div>
    """
    st.markdown(ejercicio_html, unsafe_allow_html=True)
    
    st.write("Nivel de resistencia adaptada por IA:", unsafe_allow_html=True)
    st.slider("", min_value=0, max_value=100, value=st.session_state.resistencia, step=5, format="%d%%", label_visibility="collapsed", disabled=True)
    
    st.markdown(f"<span style='color: { '#FFFF00' if st.session_state.alto_contraste else '#fbbf24' }; font-size: 20px;'>⚡ Resistencia fijada en **{st.session_state.resistencia}%**</span>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 18px; font-style: italic; color: { '#FFFF00' if st.session_state.alto_contraste else '#a855f7' };'>{st.session_state.explicacion_ia}</p>", unsafe_allow_html=True)
with col_der:
    st.markdown("<h3>Tendencia de adaptación:</h3>", unsafe_allow_html=True)
    
    df = pd.DataFrame({'Tiempo': range(len(st.session_state.historial_fatiga)), 'Fatiga': st.session_state.historial_fatiga})
    promedio = df['Fatiga'].mean()
    
    # Adaptar colores de gráficos Altair para daltonismo/bajo contraste
    color_linea = '#FFFF00' if st.session_state.alto_contraste else '#22c55e'
    color_promedio = '#ffffff' if st.session_state.alto_contraste else '#a855f7'
    
    base = alt.Chart(df).encode(
        x=alt.X('Tiempo', axis=alt.Axis(title='Tiempo', grid=False, labels=False, ticks=False, domainColor='white')), 
        y=alt.Y('Fatiga', axis=alt.Axis(title='Esfuerzo', grid=False, labels=False, ticks=False, domainColor='white'))
    )
    
    linea_principal = base.mark_line(color=color_linea, strokeWidth=4, interpolate='monotone')
    linea_promedio = alt.Chart(pd.DataFrame({'mean': [promedio]})).mark_rule(
        color=color_promedio, strokeDash=[10, 10], strokeWidth=2
    ).encode(y='mean')
    
    chart = (linea_principal + linea_promedio).properties(height=220).configure_view(strokeWidth=0).configure(background='transparent')
    st.altair_chart(chart, use_container_width=True)

# --- PIE DE PÁGINA ---
st.write("<br>", unsafe_allow_html=True)
foot1, foot2, foot3 = st.columns([1, 1, 1])

with foot1:
    st.markdown(f"""
    <div style="border: 2px solid { '#FFFF00' if st.session_state.alto_contraste else 'white' }; border-radius: 15px; padding: 10px; text-align: center; width: 70%; margin: auto;">
        ♻️ {int(st.session_state.resistencia * 1.5)} vatios<br>generados
    </div>
    """, unsafe_allow_html=True)

with foot2:
    url_imagen_musculo = RUTINAS[st.session_state.grupo_seleccionado][ejercicio_actual]["imagen"]
    try:
        st.image(url_imagen_musculo, caption=f"Objetivo: {ejercicio_actual}", use_container_width=True)    
    except:
        st.markdown("<div style='text-align: center; padding-top: 10px;'>[ 🧍 Error al cargar imagen del músculo ]</div>", unsafe_allow_html=True)

with foot3:
    # Vinculamos la función al trigger del click
    st.button("Modo alto\ncontraste", on_click=toggle_contraste, use_container_width=True)