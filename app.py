import streamlit as st
import pandas as pd
import time 
import io
import datetime # <-- NUEVA LIBRERÍA PARA LA HORA EXACTA
from sqlalchemy import create_engine, text

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y CONEXIÓN A BASE DE DATOS
# ---------------------------------------------------------
st.set_page_config(
    page_title="SIGED",
    page_icon="🎓", 
    layout="wide"
)

# 🚀 AQUI VA TU CONTRASEÑA DE POSTGRESQL 🚀
CADENA_CONEXION = st.secrets["CONEXION_BD"]
engine = create_engine(CADENA_CONEXION)

# ---------------------------------------------------------
# 2. LOGIN CON PERMISOS Y CARRERAS
# ---------------------------------------------------------
if 'logueado' not in st.session_state:
    st.session_state['logueado'] = False
    st.session_state['rol'] = None  
    st.session_state['carreras_permitidas'] = [] 
    st.session_state['usuario_actual'] = None # <-- RASTREADOR DE USUARIO

if not st.session_state['logueado']:
    st.write("")
    st.write("")
    col1, col2, col3 = st.columns([1, 0.8, 1]) 
    with col2:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center;'>🎓</h1>", unsafe_allow_html=True)
            st.markdown("<h2 style='text-align: center;'>Sistema Dual</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center;'>Inicia sesión para continuar</p>", unsafe_allow_html=True)
            st.divider() 
            usuario = st.text_input("Usuario")
            contrasena = st.text_input("Contraseña", type="password")
            st.write("") 
            if st.button("Ingresar", use_container_width=True, type="primary"):
                usuarios_validos = {
                    "admin": {"pass": "1234", "rol": "editor", "carreras": ["TODAS"]},
                    "MKMRDUAL": {"pass": "siged2026MKMR", "rol": "editor", "carreras": ["TODAS"]},
                    "director": {"pass": "escuela2026", "rol": "editor", "carreras": ["TODAS"]},
                    "coord_merca": {
                        "pass": "merca123", 
                        "rol": "editor", 
                        "carreras": ["TSU. MERCADOTECNIA", "LIC. NEGOCIOS Y MERCADOTECNIA "]
                    },
                    "coord_tics": {
                        "pass": "tics123", 
                        "rol": "editor", 
                        "carreras": ["TSU. DESARROLLO DE SOFTWARE MULTIPLATAFORMA", "LIC. INGENIERÍA EN TECNOLOGÍAS DE LA INFORMACIÓN E INNOVACIÓN DIGITAL"]
                    },
                    "coord_logis": {
                        "pass": "logis123", 
                        "rol": "editor", 
                        "carreras": ["TSU. CADENA DE SUMINISTRO", "LIC. INGENIERÍA EN LOGÍSTICA"]
                    },
                    "profe_juan": {"pass": "python", "rol": "lector", "carreras": []} 
                }
                
                if usuario in usuarios_validos and usuarios_validos[usuario]["pass"] == contrasena:
                    st.success(f"✅ ¡Bienvenido!") 
                    time.sleep(0.5)
                    st.session_state['logueado'] = True
                    st.session_state['rol'] = usuarios_validos[usuario]["rol"] 
                    st.session_state['carreras_permitidas'] = usuarios_validos[usuario]["carreras"]
                    st.session_state['usuario_actual'] = usuario # <-- GUARDAMOS QUIÉN ENTRÓ
                    st.rerun()
                else:
                    st.error("❌ Datos incorrectos")
    st.stop() 

st.sidebar.button("🔒 Cerrar Sesión", on_click=lambda: st.session_state.update({'logueado': False, 'rol': None, 'carreras_permitidas': [], 'usuario_actual': None}))

es_editor = st.session_state['rol'] == 'editor'
carreras_permitidas = st.session_state['carreras_permitidas']

# ---------------------------------------------------------
# 3. CARGA DE DATOS (DESDE POSTGRESQL)
# ---------------------------------------------------------
st.title("🎓 Sistema de Alumnos Dual")

@st.cache_data
def cargar_datos():
    try:
        df_alumnos = pd.read_sql_table('alumnos', engine)
        df_plan = pd.read_sql_table('plan_estudios', engine)
        df_maestros = pd.read_sql_table('asignacion_maestros', engine)
        df_calif = pd.read_sql_table('calificaciones', engine)

        map_alumnos = {'matricula': 'Matricula', 'nombre_completo': 'Nombre_Completo', 'carrera': 'Carrera', 'cuatrimestre': 'Cuatrimestre', 'empresa_dual': 'Empresa_Dual', 'modalidad': 'Modalidad', 'materias_empresa': 'Materias_Empresa', 'turno': 'Turno', 'correo': 'Correo', 'telefono': 'Telefono', 'curp': 'CURP', 'nss': 'NSS'}
        df_alumnos.rename(columns=map_alumnos, inplace=True)

        map_plan = {'carrera': 'Carrera', 'cuatrimestre': 'Cuatrimestre', 'nombre_materia': 'Nombre_Materia'}
        df_plan.rename(columns=map_plan, inplace=True)

        map_maestros = {'carrera': 'Carrera', 'cuatrimestre': 'Cuatrimestre', 'nombre_materia': 'Nombre_Materia', 'nombre_maestro': 'Nombre_Maestro'}
        df_maestros.rename(columns=map_maestros, inplace=True)

        map_calif = {'matricula': 'Matricula', 'nombre_completo': 'Nombre_Completo', 'cuatrimestre': 'Cuatrimestre', 'nombre_maestro': 'Nombre_Maestro', 'materia': 'Materia', 's1': 'S1', 's2': 'S2', 's3': 'S3', 's4': 'S4', 's5': 'S5', 's6': 'S6', 's7': 'S7', 's8': 'S8', 's9': 'S9', 's10': 'S10', 's11': 'S11', 's12': 'S12', 's13': 'S13', 's14': 'S14', 's15': 'S15', 'u1': 'U1', 'u2': 'U2', 'u3': 'U3', 'promedio_final': 'Promedio_Final'}
        df_calif.rename(columns=map_calif, inplace=True)

        df_maestros_completo = pd.merge(
            df_plan[['Carrera', 'Cuatrimestre', 'Nombre_Materia']], 
            df_maestros, 
            on=['Carrera', 'Cuatrimestre', 'Nombre_Materia'], 
            how='left'
        )
        df_maestros_completo['Nombre_Maestro'] = df_maestros_completo['Nombre_Maestro'].fillna("").astype(str)

        return df_alumnos, df_plan, df_calif, df_maestros_completo

    except Exception as e:
        st.error(f"❌ Error al conectar a la base de datos PostgreSQL: {e}")
        st.stop()

try:
    df_alumnos, df_plan, df_calif, df_maestros = cargar_datos()
except Exception as e:
    st.error(f"Error general: {e}")
    st.stop() 

# ---------------------------------------------------------
# 4. BUSCADOR
# ---------------------------------------------------------
st.sidebar.header("🔍 Buscar Alumno")
lista_carreras = ["Todas"] + list(df_alumnos['Carrera'].unique())
carrera_seleccionada = st.sidebar.selectbox("Filtro de Carrera:", lista_carreras)

df_filtrado = df_alumnos[df_alumnos['Modalidad'] == 'Dual']
if carrera_seleccionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado['Carrera'] == carrera_seleccionada]

if df_filtrado.empty:
    st.sidebar.warning("No hay alumnos Dual en esta carrera.")
    st.stop() 

opciones_alumnos = ["📊 Ver Resumen General"] + (df_filtrado['Matricula'].astype(str) + " - " + df_filtrado['Nombre_Completo']).tolist()
seleccion = st.sidebar.selectbox("Selecciona o escribe el nombre:", opciones_alumnos)

# ---------------------------------------------------------
# 5. LÓGICA PRINCIPAL
# ---------------------------------------------------------
if seleccion == "📊 Ver Resumen General":
    st.header("📊 Resumen del Programa Dual")
    col_dash1, col_dash2 = st.columns(2)
    with col_dash1:
        st.subheader("Alumnos por Empresa")
        st.bar_chart(df_alumnos['Empresa_Dual'].value_counts())
    with col_dash2:
        st.subheader("Alumnos por Carrera")
        st.bar_chart(df_alumnos['Carrera'].value_counts())

    st.divider()
    
    if "TODAS" in carreras_permitidas:
        st.subheader("📥 Exportación Global (Modo Seguro)")
        st.write("Descarga el historial completo de calificaciones de todas las carreras. Esta acción NO borra ningún registro.")
        
        if df_calif.empty:
            st.info("Aún no hay calificaciones registradas en la base de datos.")
        else:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_calif.to_excel(writer, index=False, sheet_name='Reporte_Calificaciones')
            
            st.download_button(
                label="📊 Descargar Excel Completo",
                data=buffer.getvalue(),
                file_name=f"Reporte_Global_Dual_{time.strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
            
        st.divider()
        st.subheader("🕵️ Panel de Auditoría (Exclusivo Dirección)")
        st.write("Descarga la bitácora de registros eliminados para revisar quién realizó los cortes de ciclo y en qué momento.")
        
        try:
            # Traemos la tabla de historial solo si el admin hace clic en este botón
            df_historial = pd.read_sql_table('historial_calificaciones', engine)
            
            if df_historial.empty:
                st.info("No hay registros en la bitácora de auditoría. Aún no se han borrado calificaciones.")
            else:
                buffer_auditoria = io.BytesIO()
                with pd.ExcelWriter(buffer_auditoria, engine='openpyxl') as writer:
                    df_historial.to_excel(writer, index=False, sheet_name='Auditoria_Eliminados')
                
                st.download_button(
                    label="🕵️ Descargar Bitácora de Auditoría",
                    data=buffer_auditoria.getvalue(),
                    file_name=f"Auditoria_Dual_{time.strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="secondary"
                )
        except Exception as e:
            st.info("La tabla de historial aún no ha sido creada o está vacía. Se creará en cuanto un coordinador borre un registro.")

    else:
        st.subheader("📥 Exportación y Corte de Ciclo")
        st.write("Genera el reporte de calificaciones de las carreras a tu cargo.")
        
        matriculas_permitidas = df_alumnos[df_alumnos['Carrera'].isin(carreras_permitidas)]['Matricula'].tolist()
        df_calif_export = df_calif[df_calif['Matricula'].isin(matriculas_permitidas)]
        matriculas_a_borrar = df_calif_export['Matricula'].unique().tolist()
        
        if df_calif_export.empty:
            st.info("Aún no hay calificaciones registradas para las carreras a tu cargo.")
        else:
            st.warning("⚠️ **ATENCIÓN EDITOR:** Al descargar este archivo, las calificaciones de tus alumnos se **eliminarán** de la base de datos para iniciar el nuevo ciclo. Esta acción es irreversible y quedará registrada en el sistema de auditoría.")
            
            check_purga = st.checkbox("Entiendo la advertencia y confirmo el corte de ciclo.")
            
            if check_purga:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_calif_export.to_excel(writer, index=False, sheet_name='Reporte_Calificaciones')
                
                def purgar_base_datos():
                    try:
                        # 1. Creamos la copia de los datos
                        df_historial = df_calif_export.copy()
                        
                        # 2. Le pegamos el usuario y la fecha
                        df_historial['eliminado_por'] = st.session_state.get('usuario_actual', 'Desconocido')
                        df_historial['fecha_eliminacion'] = datetime.datetime.now()
                        
                        # 3. Guardamos la copia en la bóveda
                        df_historial.columns = df_historial.columns.str.lower()
                        df_historial.to_sql('historial_calificaciones', engine, if_exists='append', index=False)

                        # 4. Procedemos a borrar de la tabla principal
                        with engine.begin() as conn:
                            for mat in matriculas_a_borrar:
                                conn.execute(text("DELETE FROM calificaciones WHERE matricula = :m"), {"m": mat})
                                
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"❌ Error al respaldar en auditoría: {e}")
                
                st.download_button(
                    label="📊 Descargar Excel y Limpiar Registros",
                    data=buffer.getvalue(),
                    file_name=f"Corte_Dual_{time.strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    on_click=purgar_base_datos
                )

else:
    matricula_actual = int(seleccion.split(" - ")[0])
    alumno = df_alumnos[df_alumnos['Matricula'] == matricula_actual].iloc[0]
    
    puede_editar_este_alumno = False
    if es_editor:
        if "TODAS" in carreras_permitidas or alumno['Carrera'] in carreras_permitidas:
            puede_editar_este_alumno = True

    st.header(f"👤 {alumno['Nombre_Completo']}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Carrera", alumno['Carrera'])
    col2.metric("Cuatrimestre", str(alumno['Cuatrimestre']))
    col3.metric("Empresa", alumno['Empresa_Dual'])
    
    with st.expander("📋 Ver Datos Personales del Alumno"):
        c_datos1, c_datos2 = st.columns(2)
        with c_datos1:
            st.write(f"**Turno:** {alumno.get('Turno', 'No registrado')}")
            st.write(f"**CURP:** {alumno.get('CURP', 'No registrado')}")
            st.write(f"**NSS:** {alumno.get('NSS', 'No registrado')}")
        with c_datos2:
            st.write(f"**Teléfono:** {alumno.get('Telefono', 'No registrado')}")
            st.write(f"**Correo:** {alumno.get('Correo', 'No registrado')}")

    st.divider() 

    plan_filtrado = df_plan[
        (df_plan['Carrera'] == alumno['Carrera']) & 
        (df_plan['Cuatrimestre'] == alumno['Cuatrimestre'])
    ]
    todas_las_materias = plan_filtrado['Nombre_Materia'].tolist()
    
    if pd.isna(alumno['Materias_Empresa']):
        materias_empresa = []
    else:
        materias_empresa = [m.strip() for m in str(alumno['Materias_Empresa']).split(',')]

    materias_escuela = [m for m in todas_las_materias if m not in materias_empresa]

    tab_empresa, tab_uni, tab_maestros, tab_editar = st.tabs(["🏢 Calificaciones Empresa", "🏫 Evalúa Universidad", "👨‍🏫 Asignación de Maestros", "✏️ Editar Alumno"])

    with tab_empresa:
        if not materias_empresa:
            st.info("Este alumno no tiene materias asignadas a la empresa.")
        else:
            col_lista, col_panel = st.columns([1, 2])
            with col_lista:
                st.subheader("Selecciona Materia:")
                materia_activa = st.radio("Lista de materias:", materias_empresa, label_visibility="collapsed")
            with col_panel:
                st.subheader(f"📝 Calificando: {materia_activa}")
                with st.container(border=True):
                    calif_existente = df_calif[
                        (df_calif['Matricula'] == matricula_actual) & 
                        (df_calif['Materia'] == materia_activa)
                    ]
                    notas_actuales = {}
                    for i in range(1, 16):
                        col_name = f"S{i}"
                        if not calif_existente.empty and col_name in calif_existente.columns:
                            try:
                                val = float(calif_existente.iloc[0][col_name])
                                notas_actuales[col_name] = val
                            except:
                                notas_actuales[col_name] = 0.0
                        else:
                            notas_actuales[col_name] = 0.0

                    tab_u1, tab_u2, tab_u3 = st.tabs(["U1 (Sem 1-5)", "U2 (Sem 6-10)", "U3 (Sem 11-15)"])
                    nuevas_notas = {}
                    
                    with tab_u1:
                        c1, c2, c3, c4, c5 = st.columns(5)
                        nuevas_notas['S1'] = c1.number_input("Sem 1", 0.0, 10.0, notas_actuales['S1'], key="s1", disabled=not puede_editar_este_alumno)
                        nuevas_notas['S2'] = c2.number_input("Sem 2", 0.0, 10.0, notas_actuales['S2'], key="s2", disabled=not puede_editar_este_alumno)
                        nuevas_notas['S3'] = c3.number_input("Sem 3", 0.0, 10.0, notas_actuales['S3'], key="s3", disabled=not puede_editar_este_alumno)
                        nuevas_notas['S4'] = c4.number_input("Sem 4", 0.0, 10.0, notas_actuales['S4'], key="s4", disabled=not puede_editar_este_alumno)
                        nuevas_notas['S5'] = c5.number_input("Sem 5", 0.0, 10.0, notas_actuales['S5'], key="s5", disabled=not puede_editar_este_alumno)
                        prom_u1 = (nuevas_notas['S1'] + nuevas_notas['S2'] + nuevas_notas['S3'] + nuevas_notas['S4'] + nuevas_notas['S5']) / 5
                        st.info(f"📊 Prom U1: {prom_u1:.2f}")

                    with tab_u2:
                        c6, c7, c8, c9, c10 = st.columns(5)
                        nuevas_notas['S6'] = c6.number_input("Sem 6", 0.0, 10.0, notas_actuales['S6'], key="s6", disabled=not puede_editar_este_alumno)
                        nuevas_notas['S7'] = c7.number_input("Sem 7", 0.0, 10.0, notas_actuales['S7'], key="s7", disabled=not puede_editar_este_alumno)
                        nuevas_notas['S8'] = c8.number_input("Sem 8", 0.0, 10.0, notas_actuales['S8'], key="s8", disabled=not puede_editar_este_alumno)
                        nuevas_notas['S9'] = c9.number_input("Sem 9", 0.0, 10.0, notas_actuales['S9'], key="s9", disabled=not puede_editar_este_alumno)
                        nuevas_notas['S10'] = c10.number_input("Sem 10", 0.0, 10.0, notas_actuales['S10'], key="s10", disabled=not puede_editar_este_alumno)
                        prom_u2 = (nuevas_notas['S6'] + nuevas_notas['S7'] + nuevas_notas['S8'] + nuevas_notas['S9'] + nuevas_notas['S10']) / 5
                        st.info(f"📊 Prom U2: {prom_u2:.2f}")

                    with tab_u3:
                        c11, c12, c13, c14, c15 = st.columns(5)
                        nuevas_notas['S11'] = c11.number_input("Sem 11", 0.0, 10.0, notas_actuales['S11'], key="s11", disabled=not puede_editar_este_alumno)
                        nuevas_notas['S12'] = c12.number_input("Sem 12", 0.0, 10.0, notas_actuales['S12'], key="s12", disabled=not puede_editar_este_alumno)
                        nuevas_notas['S13'] = c13.number_input("Sem 13", 0.0, 10.0, notas_actuales['S13'], key="s13", disabled=not puede_editar_este_alumno)
                        nuevas_notas['S14'] = c14.number_input("Sem 14", 0.0, 10.0, notas_actuales['S14'], key="s14", disabled=not puede_editar_este_alumno)
                        nuevas_notas['S15'] = c15.number_input("Sem 15", 0.0, 10.0, notas_actuales['S15'], key="s15", disabled=not puede_editar_este_alumno)
                        prom_u3 = (nuevas_notas['S11'] + nuevas_notas['S12'] + nuevas_notas['S13'] + nuevas_notas['S14'] + nuevas_notas['S15']) / 5
                        st.info(f"📊 Prom U3: {prom_u3:.2f}")
                    
                    promedio_final = (prom_u1 + prom_u2 + prom_u3) / 3
                    st.divider()
                    st.write(f"🎓 **Final:** {promedio_final:.2f}")
                    
                    if puede_editar_este_alumno:
                        if st.button("💾 Guardar Notas", type="primary"):
                            maestro_asignado = ""
                            filtro_m = df_maestros[
                                (df_maestros['Carrera'] == alumno['Carrera']) & 
                                (df_maestros['Cuatrimestre'] == alumno['Cuatrimestre']) & 
                                (df_maestros['Nombre_Materia'] == materia_activa)
                            ]
                            if not filtro_m.empty:
                                maestro_asignado = filtro_m.iloc[0]['Nombre_Maestro']
                            
                            datos_fila = {
                                "Matricula": matricula_actual,
                                "Nombre_Completo": alumno['Nombre_Completo'],
                                "Cuatrimestre": alumno['Cuatrimestre'],
                                "Nombre_Maestro": maestro_asignado,
                                "Materia": materia_activa,
                                **nuevas_notas,
                                "U1": round(prom_u1, 2), "U2": round(prom_u2, 2), "U3": round(prom_u3, 2),
                                "Promedio_Final": round(promedio_final, 2)
                            }
                            nuevo_df_fila = pd.DataFrame([datos_fila])
                            
                            try:
                                with engine.begin() as conn:
                                    conn.execute(text("DELETE FROM calificaciones WHERE matricula = :m AND materia = :mat"), {"m": matricula_actual, "mat": materia_activa})
                                
                                nuevo_df_sql = nuevo_df_fila.copy()
                                nuevo_df_sql.columns = nuevo_df_sql.columns.str.lower()
                                nuevo_df_sql.to_sql('calificaciones', engine, if_exists='append', index=False)

                                st.success("✅ Calificaciones guardadas en la Base de Datos")
                                st.cache_data.clear()
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error al guardar en PostgreSQL: {e}")
                    else:
                        st.info("👀 MODO LECTURA: No tienes asignada esta carrera para poder calificar.")

    with tab_uni:
        st.subheader("🏫 Materias Evaluadas por Universidad")
        if materias_escuela:
            st.table(pd.DataFrame(materias_escuela, columns=["Materia"]))
        else:
            st.success("¡Todo se evalúa en la empresa!")

    with tab_maestros:
        st.subheader(f"👨‍🏫 Plantilla Docente: {alumno['Carrera']} - {alumno['Cuatrimestre']}° Cuatrimestre")
        
        filtro_maestros = df_maestros[
            (df_maestros['Carrera'] == alumno['Carrera']) & 
            (df_maestros['Cuatrimestre'] == alumno['Cuatrimestre'])
        ].copy() 

        if puede_editar_este_alumno:
            st.markdown("Edita los maestros responsables de impartir las materias de este grupo.")
            cambios_maestros = st.data_editor(
                filtro_maestros, 
                hide_index=True, 
                column_config={
                    "Carrera": st.column_config.TextColumn(disabled=True), 
                    "Cuatrimestre": st.column_config.NumberColumn(disabled=True),
                    "Nombre_Materia": st.column_config.TextColumn(disabled=True),
                    "Nombre_Maestro": st.column_config.TextColumn("Nombre del Maestro (Editable)", required=True)
                },
                use_container_width=True
            )

            if st.button("💾 Actualizar Maestros"):
                try:
                    with engine.begin() as conn:
                        conn.execute(text("DELETE FROM asignacion_maestros WHERE carrera = :c AND cuatrimestre = :cu"), {"c": alumno['Carrera'], "cu": alumno['Cuatrimestre']})
                    
                    df_to_save = cambios_maestros.copy()
                    df_to_save.columns = df_to_save.columns.str.lower()
                    df_to_save.to_sql('asignacion_maestros', engine, if_exists='append', index=False)
                    
                    st.success("✅ Plantilla de maestros actualizada en la Base de Datos")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al guardar maestros en PostgreSQL: {e}")
        else:
            st.markdown("Lista de maestros asignados a este grupo.")
            st.dataframe(filtro_maestros, hide_index=True, use_container_width=True)
            st.info("👀 MODO LECTURA: No tienes asignada esta carrera para editar su plantilla docente.")

    with tab_editar:
        st.subheader("⚙️ Actualizar Datos del Alumno")
        
        if puede_editar_este_alumno:
            st.info("💡 Puedes actualizar el nivel, la empresa, y los datos de contacto del alumno.")
            
            c_acad, c_pers = st.columns(2)
            
            with c_acad:
                st.markdown("#### Datos Académicos")
                edit_cuatri = st.number_input("Cuatrimestre", min_value=1, max_value=12, value=int(alumno['Cuatrimestre']), step=1)
                edit_empresa = st.text_input("Empresa Dual", value=str(alumno['Empresa_Dual']))
                
                materias_disp_edit = df_plan[
                    (df_plan['Carrera'] == alumno['Carrera']) & 
                    (df_plan['Cuatrimestre'] == edit_cuatri)
                ]['Nombre_Materia'].tolist()
                
                current_mat = [m.strip() for m in str(alumno['Materias_Empresa']).split(',')] if not pd.isna(alumno['Materias_Empresa']) else []
                valid_defaults = [m for m in current_mat if m in materias_disp_edit]
                
                edit_materias = st.multiselect(
                    "Materias Empresa (Este cuatrimestre):", 
                    options=materias_disp_edit, 
                    default=valid_defaults
                )

            with c_pers:
                st.markdown("#### Datos Personales")
                current_turno = str(alumno.get('Turno', 'Matutino'))
                idx_turno = 0 if current_turno == "Matutino" else (1 if current_turno == "Nocturno" else 0)
                
                edit_turno = st.selectbox("Turno", ["Matutino", "Nocturno"], index=idx_turno)
                edit_correo = st.text_input("Correo", value=str(alumno.get('Correo', 'No registrado')))
                edit_telefono = st.text_input("Teléfono", value=str(alumno.get('Telefono', 'No registrado')))
                edit_curp = st.text_input("CURP", value=str(alumno.get('CURP', 'No registrado')))
                edit_nss = st.text_input("NSS", value=str(alumno.get('NSS', 'No registrado')))
            
            if st.button("💾 Guardar Cambios del Alumno", type="primary", use_container_width=True):
                materias_texto_edit = ", ".join(edit_materias)
                
                try:
                    with engine.begin() as conn:
                        comando_sql = text("""
                            UPDATE alumnos 
                            SET cuatrimestre = :cuatri, 
                                empresa_dual = :empresa, 
                                materias_empresa = :materias,
                                turno = :turno,
                                correo = :correo,
                                telefono = :telefono,
                                curp = :curp,
                                nss = :nss
                            WHERE matricula = :mat
                        """)
                        conn.execute(comando_sql, {
                            "cuatri": edit_cuatri,
                            "empresa": edit_empresa,
                            "materias": materias_texto_edit,
                            "turno": edit_turno,
                            "correo": edit_correo,
                            "telefono": edit_telefono,
                            "curp": edit_curp,
                            "nss": edit_nss,
                            "mat": matricula_actual
                        })
                        
                    st.success("✅ ¡Datos actualizados con éxito en la Base de Datos!")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al actualizar en PostgreSQL: {e}")
            
            st.divider()
            
            with st.expander("⚠️ Eliminar Alumno"):
                st.warning("Esta acción borrará permanentemente al alumno y todas sus calificaciones. No se puede deshacer.")
                check_seguridad = st.checkbox("Estoy seguro de que quiero eliminar a este alumno de la base de datos.")
                
                if check_seguridad:
                    if st.button("🗑️ Eliminar Alumno Definitivamente", type="primary"):
                        try:
                            with engine.begin() as conn:
                                conn.execute(text("DELETE FROM calificaciones WHERE matricula = :mat"), {"mat": matricula_actual})
                                conn.execute(text("DELETE FROM alumnos WHERE matricula = :mat"), {"mat": matricula_actual})
                            
                            st.success("✅ Alumno y calificaciones eliminados correctamente.")
                            st.cache_data.clear()
                            time.sleep(1.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al eliminar en PostgreSQL: {e}")
            
        else:
            st.warning("👀 MODO LECTURA: No tienes asignada esta carrera para modificar sus datos.")

    st.divider()
    texto_reporte = f"""
    REPORTE DE ASIGNACIÓN DUAL
    Fecha: {time.strftime("%d/%m/%Y")}
    Alumno: {alumno['Nombre_Completo']}
    Matrícula: {alumno['Matricula']}
    Turno: {alumno.get('Turno', 'N/A')}
    CURP: {alumno.get('CURP', 'N/A')}
    NSS: {alumno.get('NSS', 'N/A')}
    Correo: {alumno.get('Correo', 'N/A')}
    
    [MATERIAS EMPRESA]
    {', '.join(materias_empresa) if materias_empresa else 'Ninguna'}
    
    [MATERIAS UNIVERSIDAD]
    {', '.join(materias_escuela) if materias_escuela else 'Ninguna'}
    """
    st.download_button("📄 Descargar Ficha", texto_reporte, file_name=f"Ficha_{alumno['Matricula']}.txt")

# ---------------------------------------------------------
# AGREGAR NUEVO ALUMNO (SOLO VISIBLE PARA EDITORES)
# ---------------------------------------------------------
if es_editor:
    with st.sidebar.expander("➕ Agregar Nuevo Alumno"):
        st.write("Datos del alumno:")
        
        todas_carreras = list(df_plan['Carrera'].unique())
        if "TODAS" in carreras_permitidas:
            lista_carreras_form = todas_carreras
        else:
            lista_carreras_form = [c for c in todas_carreras if c in carreras_permitidas]

        if not lista_carreras_form:
            st.warning("No tienes carreras asignadas para agregar alumnos.")
        else:
            new_matricula = st.number_input("Matrícula", min_value=0, step=1)
            new_nombre = st.text_input("Nombre Completo")
            
            new_carrera = st.selectbox("Carrera", lista_carreras_form)
            new_cuatri = st.number_input("Cuatrimestre", min_value=1, max_value=12, step=1)
            new_empresa = st.text_input("Empresa Dual")
            
            new_turno = st.selectbox("Turno", ["Matutino", "Nocturno"])
            new_correo = st.text_input("Correo Electrónico")
            new_telefono = st.text_input("Teléfono")
            new_curp = st.text_input("CURP")
            new_nss = st.text_input("NSS (Seguro Social)")

            materias_disponibles = df_plan[
                (df_plan['Carrera'] == new_carrera) & 
                (df_plan['Cuatrimestre'] == new_cuatri)
            ]['Nombre_Materia'].tolist()

            materias_seleccionadas = st.multiselect("Materias Empresa:", options=materias_disponibles)
            
            if st.button("Guardar Alumno"):
                if not new_nombre or not new_empresa:
                    st.error("⚠️ Falta nombre o empresa.")
                else:
                    materias_texto = ", ".join(materias_seleccionadas)
                    nuevo_alumno = pd.DataFrame([{
                        "Matricula": new_matricula, 
                        "Nombre_Completo": new_nombre,
                        "Carrera": new_carrera, 
                        "Cuatrimestre": new_cuatri,
                        "Empresa_Dual": new_empresa, 
                        "Modalidad": "Dual",
                        "Materias_Empresa": materias_texto,
                        "Turno": new_turno,
                        "Correo": new_correo,
                        "Telefono": new_telefono,
                        "CURP": new_curp,
                        "NSS": new_nss
                    }])
                    
                    try:
                        nuevo_alumno_sql = nuevo_alumno.copy()
                        nuevo_alumno_sql.columns = nuevo_alumno_sql.columns.str.lower()
                        nuevo_alumno_sql.to_sql('alumnos', engine, if_exists='append', index=False)
                        
                        st.success("✅ Alumno agregado exitosamente a PostgreSQL")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al guardar en base de datos: {e}")