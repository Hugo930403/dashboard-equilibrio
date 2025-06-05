import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
import plotly.express as px

st.set_page_config(page_title="Proyección de Punto de Equilibrio", layout="wide")
st.title("Punto de Equilibrio por Licenciatura")

def calcular_colegiatura(num_aulas, capacidad_aula, estudiantes_actuales, costo_fijo, costo_variable, incluir_utilidad, utilidad_pct, colegiatura_manual):
    capacidad_total = num_aulas * capacidad_aula
    costo_variable_unitario = costo_variable / capacidad_total if capacidad_total > 0 else 0
    if incluir_utilidad:
        colegiatura = (costo_fijo + costo_variable) / capacidad_total
        colegiatura = colegiatura / (1 - (utilidad_pct / 100))
    else:
        colegiatura = colegiatura_manual
    return colegiatura, capacidad_total, costo_variable_unitario

def verificar_punto_equilibrio(
    colegiatura_final,
    costo_variable_estudiante,
    costo_fijo_total,
    capacidad_total,
    estudiantes_final,
    clave_base=""
):
    if colegiatura_final <= costo_variable_estudiante:
        st.error("❌ La colegiatura es menor o igual al costo variable por estudiante. No hay rentabilidad.")
        if st.checkbox("¿Deseas recalcular la colegiatura para cubrir al menos el costo variable?", key=f"{clave_base}_recalculo_costo_variable"):
            diferencia = costo_variable_estudiante - colegiatura_final
            colegiatura_final += diferencia + 1
            st.info(f"📈 Nueva colegiatura sugerida: ${colegiatura_final:.2f}")
        else:
            st.stop()

    punto_equilibrio = costo_fijo_total / (colegiatura_final - costo_variable_estudiante)
    punto_equilibrio_redondo = int(np.ceil(punto_equilibrio))

    if punto_equilibrio_redondo > capacidad_total:
        st.warning("⚠️ El punto de equilibrio es mayor a la capacidad máxima.")
    if punto_equilibrio_redondo > estudiantes_final:
        st.warning("⚠️ El punto de equilibrio es mayor al número de estudiantes actuales.")
        if st.checkbox("¿Deseas recalcular la colegiatura para mejorar la rentabilidad?", key=f"{clave_base}_recalculo_rentabilidad"):
            colegiatura_final, punto_equilibrio_redondo = recalcular_colegiatura_para_rentabilidad(
                costo_variable_estudiante, costo_fijo_total, estudiantes_final
            )

    return colegiatura_final, punto_equilibrio_redondo

def recalcular_colegiatura_para_rentabilidad(costo_variable_estudiante, costo_fijo_total, estudiantes_final):
    nueva_colegiatura = costo_variable_estudiante + (costo_fijo_total / estudiantes_final)
    nueva_colegiatura = np.ceil(nueva_colegiatura)
    st.info(f"📈 Nueva colegiatura sugerida para rentabilidad mínima: ${nueva_colegiatura:.2f}")
    nuevo_pe = int(np.ceil(costo_fijo_total / (nueva_colegiatura - costo_variable_estudiante)))
    st.markdown(f"🔁 Nuevo punto de equilibrio: **{nuevo_pe} alumnos**")
    return nueva_colegiatura, nuevo_pe

if "licenciaturas_pe" not in st.session_state:
    st.session_state.licenciaturas_pe = pd.DataFrame(columns=[
        "Licenciatura", "Estudiantes", "Colegiatura", "Costo Fijo", "Costo Variable",
        "PE Alumnos", "Ingresos Totales", "Egresos Totales", "Utilidad Neta"
    ])

if "formulario_pe_calculado" not in st.session_state:
    st.session_state.formulario_pe_calculado = False

seccion = st.sidebar.radio("Secciones", ["📊 Punto de Equilibrio", "🧪 Simulaciones", "📈 Proyección"])

with st.sidebar.expander("🧹 Borrar historial de datos"):
    if st.button("🗑️ Borrar historial de licenciaturas, simulaciones y proyecciones"):
        st.session_state.confirmar_borrado = True

    if st.session_state.get("confirmar_borrado", False):
        with st.warning("⚠️ Esta acción eliminará todos los datos de las licenciaturas, simulaciones y proyecciones. ¿Deseas continuar?"):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Sí, borrar todo"):

                    st.session_state.licenciaturas_pe = pd.DataFrame(columns=st.session_state.licenciaturas_pe.columns)
                    if "nueva_licenciatura" in st.session_state:
                        del st.session_state["nueva_licenciatura"]

                    for key in list(st.session_state.keys()):
                        if key.startswith("sim_") or key.startswith("proy_") or key in [
                            "simulacion_data", "proyeccion_resultados", "grafico_proyeccion"
                        ]:
                            del st.session_state[key]

                    del st.session_state["confirmar_borrado"]

                    st.success("✅ Datos eliminados correctamente.")

            with col2:
                if st.button("❌ Cancelar"):
                    del st.session_state["confirmar_borrado"]
                    st.info("Cancelado. Los datos no se han borrado.")

if seccion == "📊 Punto de Equilibrio":
    st.subheader("📝 Parámetros del Análisis")

    with st.form("formulario_pe"):
        nombre_licenciatura = st.text_input("Nombre de la licenciatura", value=st.session_state.get("nombre_licenciatura", "Nueva Licenciatura"), key="nombre_licenciatura")
        incluir_utilidad = st.checkbox("¿Incluir porcentaje de utilidad?", value=st.session_state.get("incluir_utilidad", False), key="incluir_utilidad")
        num_aulas = st.number_input("Número de aulas", min_value=1, value=st.session_state.get("num_aulas", 1), key="num_aulas")
        capacidad_aula = st.number_input("Capacidad por aula", min_value=1, value=st.session_state.get("capacidad_aula", 1), key="capacidad_aula")
        estudiantes_actuales = st.number_input("Estudiantes actuales", min_value=0, value=st.session_state.get("estudiantes_actuales", 0), key="estudiantes_actuales")
        costo_fijo_total = st.number_input("Costos", min_value=0.0, value=st.session_state.get("costo_fijo_total", 0.0), key="costo_fijo_total", format="%0.2f")
        costo_variable = st.number_input("Gastos", min_value=0.0, value=st.session_state.get("costo_variable", 0.0), key="costo_variable", format="%0.2f")

        col_utilidad, col_colegiatura = st.columns(2)

        with col_utilidad:
            utilidad = st.number_input(
                "Porcentaje de utilidad (%)",
                min_value=0.0,
                value=st.session_state.get("utilidad", 30.0),
                format="%.2f",
                disabled=not incluir_utilidad,
                key="utilidad"
            )

        with col_colegiatura:
            colegiatura_manual = st.number_input(
                "Colegiatura estimada",
                min_value=0.0,
                value=st.session_state.get("colegiatura_manual", 0.0),
                format="%.2f",
                disabled=incluir_utilidad,
                key="colegiatura_manual"
            )

        submitted = st.form_submit_button("Calcular Punto de Equilibrio")

    if submitted:
        st.session_state.formulario_pe_calculado = True

    if st.session_state.get("formulario_pe_calculado", False):
        colegiatura_final, capacidad_total, costo_variable_estudiante = calcular_colegiatura(
            st.session_state.num_aulas, st.session_state.capacidad_aula, st.session_state.estudiantes_actuales,
            st.session_state.costo_fijo_total, st.session_state.costo_variable,
            st.session_state.incluir_utilidad, st.session_state.utilidad, st.session_state.colegiatura_manual
        )

        if st.session_state.incluir_utilidad:
            estudiantes_final = capacidad_total
            ingreso_actual = estudiantes_final * colegiatura_final
        else:
            estudiantes_final = st.session_state.estudiantes_actuales
            ingreso_actual = estudiantes_final * colegiatura_final

        colegiatura_final, punto_equilibrio_redondo = verificar_punto_equilibrio(
            colegiatura_final,
            costo_variable_estudiante,
            st.session_state.costo_fijo_total,
            capacidad_total,
            estudiantes_final,
            clave_base="formulario_pe"
        )

        ingreso_actual = estudiantes_final * colegiatura_final
        egresos_actuales = st.session_state.costo_fijo_total + (estudiantes_final * costo_variable_estudiante)

        df_equilibrio = pd.DataFrame({
            "Alumnos": list(range(1, int(capacidad_total) + 1)),
            "Ingresos": [i * colegiatura_final for i in range(1, int(capacidad_total) + 1)],
            "Egresos": [st.session_state.costo_fijo_total + (i * costo_variable_estudiante) for i in range(1, int(capacidad_total) + 1)],
        })

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_equilibrio["Alumnos"], y=df_equilibrio["Ingresos"], mode='lines', name='Ingresos', line=dict(color='green')))
        fig.add_trace(go.Scatter(x=df_equilibrio["Alumnos"], y=df_equilibrio["Egresos"], mode='lines', name='Egresos', line=dict(color='red')))
        fig.add_trace(go.Scatter(x=[punto_equilibrio_redondo], y=[punto_equilibrio_redondo * colegiatura_final], mode='markers+text', name="Punto de Equilibrio", text=["PE"], marker=dict(size=10, color='blue')))
        fig.add_trace(go.Scatter(x=[estudiantes_final], y=[ingreso_actual], mode='markers+text', name="Ingreso Actual", text=["IA"], textposition="bottom center", marker=dict(size=10, color='orange')))

        fig.update_layout(title="Gráfico de Rentabilidad", xaxis_title="Cantidad de Alumnos", yaxis_title="Monto ($)", legend=dict(orientation="h"))
        st.plotly_chart(fig, use_container_width=True)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Punto de Equilibrio", f"{punto_equilibrio_redondo} alumnos")
        col2.metric("Ingreso Actual", f"${ingreso_actual:,.2f}")
        col3.metric("Egresos Actuales", f"${egresos_actuales:,.2f}")
        col4.metric("Colegiatura", f"${colegiatura_final:,.2f}")

        st.success("Rentabilidad: RENTABLE" if ingreso_actual >= egresos_actuales else "Rentabilidad: NO RENTABLE")

        nueva_licenciatura = pd.DataFrame([{
            "Licenciatura": st.session_state.nombre_licenciatura,
            "Estudiantes": estudiantes_final,
            "Colegiatura": colegiatura_final,
            "Costo Fijo": st.session_state.costo_fijo_total,
            "Costo Variable": st.session_state.costo_variable,
            "PE Alumnos": punto_equilibrio_redondo,
            "Ingresos Totales": ingreso_actual,
            "Egresos Totales": egresos_actuales,
            "Utilidad Neta": ingreso_actual - egresos_actuales
        }])

        st.session_state.licenciaturas_pe = pd.concat([
            st.session_state.get("licenciaturas_pe", pd.DataFrame()), nueva_licenciatura
        ], ignore_index=True)

        st.session_state.nueva_licenciatura = st.session_state.licenciaturas_pe.copy()

        st.markdown("Licenciaturas analizadas")
        st.dataframe(st.session_state.licenciaturas_pe, use_container_width=True)

        def generar_excel():
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df_equilibrio.to_excel(writer, sheet_name="Rentabilidad", index=False)
                resumen = pd.DataFrame({
                    "Concepto": ["Punto Equilibrio", "Estudiantes Actuales", "Capacidad Total", "Colegiatura", "Ingreso Actual", "Egresos Actuales", "Rentabilidad"],
                    "Valor": [punto_equilibrio_redondo, estudiantes_final, capacidad_total, colegiatura_final, ingreso_actual, egresos_actuales, "Rentable" if ingreso_actual >= egresos_actuales else "No Rentable"]
                })
                resumen.to_excel(writer, sheet_name="Resumen", index=False)
            return output.getvalue()

        if st.button("🔄 Realizar nuevo análisis"):
            st.session_state.formulario_pe_calculado = False

        st.download_button("📥 Descargar Excel", generar_excel(), file_name=f"{st.session_state.nombre_licenciatura}_analisis.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

elif seccion == "🧪 Simulaciones":
    st.subheader("🔍 Simulación de Escenarios")

    if "nueva_licenciatura" not in st.session_state:
        st.warning("Primero carga los datos de licenciaturas.")
    else:
        df = st.session_state.nueva_licenciatura
        opciones = ["Todas"] + sorted(df["Licenciatura"].unique())
        seleccion = st.selectbox("Selecciona una licenciatura", opciones)

        if seleccion == "Todas":
            rango = st.slider("Rango de variación de estudiantes (%)", min_value=-100, max_value=300, value=100, step=10)
            valores = list(range(-rango, rango + 10, 10))

            resultados = []
            for _, fila in df.iterrows():
                nombre = fila["Licenciatura"]
                estudiantes_iniciales = fila["Estudiantes"]
                colegiatura = fila["Colegiatura"]
                costo_fijo = fila["Costo Fijo"]
                costo_variable = fila["Costo Variable"]
                costo_variable_unitario = costo_variable / estudiantes_iniciales if estudiantes_iniciales > 0 else 0

                for v in valores:
                    cambio_pct = v
                    estudiantes_simulados = max(0, int(estudiantes_iniciales * (1 + cambio_pct / 100)))
                    ingresos = estudiantes_simulados * colegiatura
                    egresos = costo_fijo + (estudiantes_simulados * costo_variable_unitario)
                    utilidad = ingresos - egresos
                    rentabilidad = "Rentable" if utilidad >= 0 else "No Rentable"

                    resultados.append({
                        "Licenciatura": nombre,
                        "Cambio (%)": cambio_pct,
                        "Estudiantes": estudiantes_simulados,
                        "Ingresos": ingresos,
                        "Egresos": egresos,
                        "Utilidad Neta": utilidad,
                        "Rentabilidad": rentabilidad
                    })

            df_simulacion = pd.DataFrame(resultados)

            st.dataframe(df_simulacion, use_container_width=True)

            fig = px.line(
                df_simulacion,
                x="Cambio (%)",
                y="Utilidad Neta",
                color="Licenciatura",
                markers=True,
                title="Utilidad Neta por Licenciatura según Variación de Estudiantes"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            fila = df[df["Licenciatura"] == seleccion].iloc[0]
            estudiantes_iniciales = fila["Estudiantes"]
            colegiatura = fila["Colegiatura"]
            costo_fijo = fila["Costo Fijo"]
            costo_variable = fila["Costo Variable"]

        capacidad_total = estudiantes_iniciales if estudiantes_iniciales > 0 else 1
        costo_variable_unitario = costo_variable / capacidad_total

        if seleccion == "Todas":
            rango = st.slider("Rango de variación de estudiantes (%)", min_value=-100, max_value=300, value=100, step=10, key="slider_todas")
            ...
        else:
            rango = st.slider("Rango de variación de estudiantes (%)", min_value=-100, max_value=300, value=100, step=10, key="slider_una")
            ...
        valores = list(range(-rango, rango + 10, 10))

        df_simulacion = pd.DataFrame({
            "Cambio (%)": valores,
            "Estudiantes": [max(0, int(estudiantes_iniciales * (1 + i / 100))) for i in valores],
        })

        df_simulacion["Ingresos"] = df_simulacion["Estudiantes"] * colegiatura
        df_simulacion["Egresos"] = costo_fijo + (df_simulacion["Estudiantes"] * costo_variable_unitario)
        df_simulacion["Utilidad Neta"] = df_simulacion["Ingresos"] - df_simulacion["Egresos"]
        df_simulacion["Rentabilidad"] = np.where(df_simulacion["Utilidad Neta"] >= 0, "Rentable", "No Rentable")

        st.dataframe(df_simulacion, use_container_width=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_simulacion["Cambio (%)"], y=df_simulacion["Utilidad Neta"], name="Utilidad", marker_color="green"))
        fig.add_trace(go.Scatter(x=df_simulacion["Cambio (%)"], y=df_simulacion["Ingresos"], mode="lines+markers", name="Ingresos", line=dict(color="blue")))
        fig.add_trace(go.Scatter(x=df_simulacion["Cambio (%)"], y=df_simulacion["Egresos"], mode="lines+markers", name="Egresos", line=dict(color="red")))

        fig.update_layout(title="Simulación de Ingresos vs Egresos", xaxis_title="Cambio en Estudiantes (%)", yaxis_title="Monto ($)")
        st.plotly_chart(fig, use_container_width=True)

        def exportar_simulacion():
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df_simulacion.to_excel(writer, sheet_name="Simulación", index=False)
            return output.getvalue()

        st.download_button("📥 Descargar Simulación", exportar_simulacion(), file_name="simulacion_estudiantes.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

elif seccion == "📈 Proyección":
    st.subheader("📈 Proyección de Rentabilidad")

    if "nueva_licenciatura" not in st.session_state:
        st.warning("Primero carga los datos de licenciaturas.")
    else:
        df = st.session_state.nueva_licenciatura
        opciones = ["Todas"] + sorted(df["Licenciatura"].unique())
        seleccion = st.selectbox("Selecciona una licenciatura", opciones)

        col1, col2, col3 = st.columns(3)
        horizonte = col1.selectbox("Horizonte de meses", [6, 12, 24], index=1)
        tasa_matricula = col2.number_input("Crecimiento mensual de matrícula (%)", value=0.0, step=0.5)
        tasa_costos = col3.number_input("Inflación mensual de costos (%)", value=2.0, step=0.5)

        if seleccion == "Todas":
            rango_meses = list(range(1, horizonte + 1))
            resultados = []

            for _, fila in df.iterrows():
                nombre = fila["Licenciatura"]
                est = fila["Estudiantes"]
                colegiatura = fila["Colegiatura"]
                c_fijo = fila["Costo Fijo"]
                c_var_unit = fila["Costo Variable"] / est if est > 0 else 0

                for mes in rango_meses:
                    est *= (1 + tasa_matricula / 100)
                    c_fijo *= (1 + tasa_costos / 100)
                    c_var_unit *= (1 + tasa_costos / 100)

                    ingresos = est * colegiatura
                    c_var_total = est * c_var_unit
                    egresos = c_fijo + c_var_total
                    utilidad = ingresos - egresos

                    resultados.append({
                        "Licenciatura": nombre,
                        "Mes": f"Mes {mes}",
                        "Estudiantes": est,
                        "Ingresos": ingresos,
                        "Costos Fijos": c_fijo,
                        "Costos Variables": c_var_total,
                        "Egresos Totales": egresos,
                        "Utilidad Neta": utilidad
                    })

            df_proyeccion = pd.DataFrame(resultados)

            st.dataframe(df_proyeccion, use_container_width=True)

            fig = px.line(
                df_proyeccion,
                x="Mes",
                y="Utilidad Neta",
                color="Licenciatura",
                title="📊 Proyección de Utilidad Neta por Licenciatura",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)

            utilidad_total = df_proyeccion["Utilidad Neta"].sum()
            meses_rentables = df_proyeccion[df_proyeccion["Utilidad Neta"] > 0]["Mes"].nunique()
            estudiantes_finales = df_proyeccion.groupby("Licenciatura")["Estudiantes"].last().sum()

            st.subheader("📌 Resumen de Proyección (Total)")
            st.markdown(f"""
            - 👥 Matrícula total final: **{int(estudiantes_finales)}** estudiantes
            - 📈 Meses con utilidad positiva (al menos una carrera): **{meses_rentables} de {horizonte}**
            - 💰 Utilidad acumulada total: **${utilidad_total:,.2f}**
            - 📉 Inflación mensual: **{tasa_costos:.1f}%**
            - 🔄 Crecimiento de matrícula mensual: **{tasa_matricula:.1f}%**
            """)
        else:
            fila = df[df["Licenciatura"] == seleccion].iloc[0]
            estudiantes_iniciales = fila["Estudiantes"]
            colegiatura = fila["Colegiatura"]
            costo_fijo = fila["Costo Fijo"]
            costo_variable_total = fila["Costo Variable"]

            capacidad_total = estudiantes_iniciales if estudiantes_iniciales > 0 else 1
            costo_variable_unitario = costo_variable_total / capacidad_total

            meses = list(range(1, horizonte + 1))
            estudiantes_mes, ingresos_mes, costos_fijos_mes, costos_variables_mes, egresos_mes, utilidad_mes = [], [], [], [], [], []

            est = estudiantes_iniciales
            c_fijo = costo_fijo
            c_var = costo_variable_unitario

            for mes in meses:
                est *= (1 + tasa_matricula / 100)
                c_fijo *= (1 + tasa_costos / 100)
                c_var *= (1 + tasa_costos / 100)

                ingresos = est * colegiatura
                c_var_total = est * c_var
                egresos = c_fijo + c_var_total
                utilidad = ingresos - egresos

                estudiantes_mes.append(est)
                ingresos_mes.append(ingresos)
                costos_fijos_mes.append(c_fijo)
                costos_variables_mes.append(c_var_total)
                egresos_mes.append(egresos)
                utilidad_mes.append(utilidad)

            df_proyeccion = pd.DataFrame({
                "Mes": [f"Mes {m}" for m in meses],
                "Estudiantes": estudiantes_mes,
                "Ingresos": ingresos_mes,
                "Costos Fijos": costos_fijos_mes,
                "Costos Variables": costos_variables_mes,
                "Egresos Totales": egresos_mes,
                "Utilidad Neta": utilidad_mes
            })

            st.dataframe(df_proyeccion, use_container_width=True)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_proyeccion["Mes"], y=df_proyeccion["Ingresos"], mode="lines+markers", name="Ingresos", line=dict(color="green")))
            fig.add_trace(go.Scatter(x=df_proyeccion["Mes"], y=df_proyeccion["Egresos Totales"], mode="lines+markers", name="Egresos", line=dict(color="red")))
            fig.add_trace(go.Bar(x=df_proyeccion["Mes"], y=df_proyeccion["Utilidad Neta"], name="Utilidad", marker_color="blue", opacity=0.5))

            fig.update_layout(title="📊 Proyección de Rentabilidad", xaxis_title="Mes", yaxis_title="Monto ($)", legend=dict(orientation="h"))
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📌 Resumen de Proyección")
            utilidad_total = sum(utilidad_mes)
            meses_rentables = sum([u > 0 for u in utilidad_mes])
            estudiantes_finales = estudiantes_mes[-1]

            st.markdown(f"""
            - 👥 Matrícula: **{int(estudiantes_iniciales)} → {int(estudiantes_finales)}** estudiantes
            - 📈 Meses con utilidad positiva: **{meses_rentables} de {horizonte}**
            - 💰 Utilidad acumulada: **${utilidad_total:,.2f}**
            - 📉 Inflación mensual: **{tasa_costos:.1f}%**
            - 🔄 Crecimiento de matrícula mensual: **{tasa_matricula:.1f}%**
            """)

            def exportar_proyeccion():
                output = BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    df_proyeccion.to_excel(writer, sheet_name="Proyección", index=False)
                return output.getvalue()

            st.download_button("📥 Descargar Proyección", exportar_proyeccion(), file_name="proyeccion_mensual.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
