import pandas as pd
import plotly.express as px
import streamlit as st
import re 

st.title('Graficación de Archivos')
pd.options.display.float_format = '{:.0f}'.format

# Función para procesar y renombrar columnas en los DataFrames
def process_dataframe(df, is_principal=True, is_df3=False):
    df_columns = df.columns.tolist()
    df_columns[df_columns.index('Price')] = 'Open Price'
    df_columns[df_columns.index('Price', df_columns.index('Open Price') + 1)] = 'Close Price'
    df.columns = df_columns

    # Renombrar 'Volume' a 'Size' en archivos secundarios
    if not is_principal:
        if 'Volume' in df.columns:
            df.rename(columns={'Volume': 'Size'}, inplace=True)
        else:
            df['Size'] = None  # Crear columna 'Size' vacía si 'Volume' no está presente

    # Agregar columna 'Source' para identificar el origen del archivo
    if is_df3:
        df['Source'] = 'df3'
    else:
        df['Source'] = 'Principal' if is_principal else 'df2'

    return df

# Función para actualizar los nombres de 'Type' según el archivo principal o secundario
def update_type_column(df, is_principal=True, is_df3=False, file_id=None):
    if is_principal:
        df['Type'] = df['Type'].replace({
            'Open df1': 'Open Transactions - Main',
            'Close df1': 'Closed Transactions - Main',
            'Open df2': 'Open Trades - Main'
        })
    else:
        df['Type'] = df['Type'].replace({
            'Open df3': f'Open Transactions - {file_id}',
            'Close df3': f'Closed Transactions - {file_id}'
        })
    return df


def add_copy_to_hover(df, is_principal=False):
    # Asegurar que 'copy_in_hover' se inicializa en todas las filas
    if is_principal:
        df['copy_in_hover'] = "no aplica"  # Para archivos principales
    else:
        df['copy_in_hover'] = "null"  # Inicializa como 'null' para archivos secundarios

    # Asumir que la columna 'Profit' puede contener datos en varios formatos
    for i in range(1, len(df)):
        # Considerar que 'copy' puede estar en diferentes partes del DataFrame
        cell_values = df.iloc[i].tolist()  # Tomar toda la fila como una lista
        copy_info = [val for val in cell_values if 'copy' in str(val)]  # Buscar 'copy' en cualquier celda

        if copy_info:
            # Usar expresiones regulares para extraer el número entre '#' y '/'
            match = re.search(r'#(\d+)/', copy_info[0])
            if match:
                copy_number = match.group(1)  # El número entre '#' y '/'
                df.at[i - 1, 'copy_in_hover'] = f"Copy: {copy_number}"

    return df



def add_copy_column(df, is_principal=False):
    if 'copy_in_hover' not in df.columns:
        df['copy_in_hover'] = None  # Asegurarse de que la columna exista
    
    if is_principal:
        df['copy_in_hover'] = "no aplica"  # Establecer 'no aplica' para todos los registros del archivo principal

    return df



# Función para leer y procesar el archivo HTML
def load_and_process_file(uploaded_file, is_principal=True, is_df3=False):
    tabs = pd.read_html(uploaded_file)
    df_combined = tabs[0].iloc[2:]
    df_combined.columns = df_combined.iloc[0]
    split_index = df_combined[df_combined.iloc[:, -1] == 'Open Trades:'].index[0]

    df1 = df_combined.iloc[:split_index + 1].reset_index(drop=True)
    if is_principal:
        df1 = df1.iloc[1:-1].reset_index(drop=True)  # Filtrado para df1 si es archivo principal

    df2 = df_combined.iloc[split_index + 0:].reset_index(drop=True)
    df2 = df2[~df2.iloc[:, 0].str.contains("Closed P/L:", na=False)].reset_index(drop=True)
    
    # Aplicamos la detección del copy solo si no es el archivo principal
    if not is_principal:
        df2 = add_copy_to_hover(df2)  # Solo aplicamos esta función en los archivos secundarios

    
    if is_principal:
        df2 = df2.iloc[0:-10].reset_index(drop=True)  # Filtrado para df2 si es archivo principal

    # Convertir los tiempos, ignorando errores y valores inválidos
    df1['Open Time'] = pd.to_datetime(df1['Open Time'].str.replace('.', '-'), errors='coerce')
    df1['Close Time'] = pd.to_datetime(df1['Close Time'].str.replace('.', '-'), errors='coerce')
    df2['Open Time'] = pd.to_datetime(df2['Open Time'].str.replace('.', '-'), errors='coerce')

    # Procesar los DataFrames, agregando la columna 'Ticket'
    df1 = process_dataframe(df1, is_principal=is_principal, is_df3=is_df3)
    df2 = process_dataframe(df2, is_principal=is_principal, is_df3=is_df3)

    df1_open = df1[['Open Time', 'Open Price', 'Profit', 'T / P', 'Size', 'Ticket', 'Source']].copy()
    df1_open['Type'] = 'Open df1' if not is_df3 else 'Open df3'
    df1_open.columns = ['Time', 'Price', 'Profit', 'T/P', 'Size', 'Ticket', 'Source', 'Type']

    df1_close = df1[['Close Time', 'Close Price', 'Profit', 'T / P', 'Size', 'Ticket', 'Source']].copy()
    df1_close['Type'] = 'Close df1' if not is_df3 else 'Close df3'
    df1_close.columns = ['Time', 'Price', 'Profit', 'T/P', 'Size', 'Ticket', 'Source', 'Type']

    if not is_principal:
        df2_open = df2[['Open Time', 'Open Price', 'Profit', 'T / P', 'Size', 'Ticket', 'Source']].copy()
        df2_open['Type'] = 'Open df2' if not is_df3 else 'Open df3'
        df2_open.columns = ['Time', 'Price', 'Profit', 'T/P', 'Size', 'Ticket', 'Source', 'Type']

    else:
        df2_open = df2[['Open Time', 'Open Price', 'Profit', 'T / P', 'Size', 'Ticket', 'Source']].copy()
        df2_open['Type'] = 'Open df2' if not is_df3 else 'Open df3'
        df2_open.columns = ['Time', 'Price', 'Profit', 'T/P', 'Size', 'Ticket', 'Source', 'Type']

    df_combined_final = pd.concat([df1_open, df1_close, df2_open], ignore_index=True)
    df_combined_final['Price'] = pd.to_numeric(df_combined_final['Price'], errors='coerce')

    df_combined_final['Day'] = df_combined_final['Time'].dt.day.astype('Int64')
    df_combined_final['Month'] = df_combined_final['Time'].dt.month.astype('Int64')
    df_combined_final['Year'] = df_combined_final['Time'].dt.year.astype('Int64')

    #df_combined_final = df_combined_final.sort_values(by='Time')

    return df_combined_final




# Cargar archivo principal
uploaded_file_principal = st.file_uploader("Cargar archivo principal HTML", type="htm")
df_combined_final_principal = None

if uploaded_file_principal is not None:
    try:
        df_combined_final_principal = load_and_process_file(uploaded_file_principal, is_principal=True)
        st.success("Archivo principal cargado y procesado correctamente.")
    except Exception as e:
        st.error(f"Error al procesar el archivo principal: {e}")

# Cargar archivo adicional (df3)
uploaded_file_adicional = st.file_uploader("Cargar archivo adicional HTML (df3)", type="htm", key="file2")
df_combined_final_df3 = None

if uploaded_file_adicional is not None:
    try:
        df_combined_final_df3 = load_and_process_file(uploaded_file_adicional, is_principal=False, is_df3=True)
        st.success("Archivo adicional cargado y procesado correctamente.")
    except Exception as e:
        st.error(f"Error al procesar el archivo adicional: {e}")

# Actualizar nombres de 'Type' después de procesar los archivos
if df_combined_final_principal is not None:
    df_combined_final_principal = update_type_column(df_combined_final_principal, is_principal=True)


hover_data = {
    'Profit': True,
    'T/P': True,
    'Source': True,
    'Size': True,
    'Ticket': True,  # Siempre mostrar el ticket
    'copy_in_hover': True
}






if df_combined_final_principal is not None:
    df_combined_final_principal = add_copy_column(df_combined_final_principal, is_principal=True)
    df_combined_final_principal = update_type_column(df_combined_final_principal, is_principal=True)


if df_combined_final_df3 is not None:
    df_combined_final_df3 = add_copy_to_hover(df_combined_final_df3)
    file_id = uploaded_file_adicional.name.split('.')[0]
    df_combined_final_df3 = update_type_column(df_combined_final_df3, is_principal=False, is_df3=True, file_id=file_id)


# Combinar y filtrar los datos si ambos archivos fueron cargados
if df_combined_final_principal is not None and df_combined_final_df3 is not None:
    # Asegurar que ambos DataFrames tienen la columna 'copy_in_hover'
    df_combined_final_principal = add_copy_column(df_combined_final_principal)
    df_combined_final_df3 = add_copy_column(df_combined_final_df3)
    
    # Combinar ambos DataFrames
    combined_df = pd.concat([df_combined_final_principal, df_combined_final_df3], ignore_index=True)

    # Inicializamos filtered_df con el DataFrame combinado por defecto
    filtered_df = combined_df

    
    # Inicializamos filtered_df con el DataFrame combinado por defecto
    filtered_df = combined_df


    
   # Selección de filtros
    filtro = st.selectbox('Selecciona el tipo de filtro', ['Día', 'Mes', 'Año', 'Rango de Días', 'Rango de Meses', 'Rango de Años', 'Ticket/Copy'])

    if filtro == 'Día':
        dia = st.number_input('Día:', min_value=1, max_value=31, value=1)
        mes = st.number_input('Mes:', min_value=1, max_value=12, value=1)
        año = st.number_input('Año:', min_value=2000, max_value=2100, value=2023)
        filtered_df = combined_df[(combined_df['Day'] == dia) & (combined_df['Month'] == mes) & (combined_df['Year'] == año)]
    elif filtro == 'Mes':
        mes = st.number_input('Mes:', min_value=1, max_value=12, value=1)
        año = st.number_input('Año:', min_value=2000, max_value=2100, value=2023)
        filtered_df = combined_df[(combined_df['Month'] == mes) & (combined_df['Year'] == año)]
    elif filtro == 'Año':
        año = st.number_input('Año:', min_value=2000, max_value=2100, value=2023)
        filtered_df = combined_df[combined_df['Year'] == año]
    elif filtro == 'Rango de Días':
        dia_inicio = st.number_input('Día Inicio:', min_value=1, max_value=31, value=1)
        dia_fin = st.number_input('Día Fin:', min_value=1, max_value=31, value=31)
        mes = st.number_input('Mes:', min_value=1, max_value=12, value=1)
        año = st.number_input('Año:', min_value=2000, max_value=2100, value=2023)
        filtered_df = combined_df[(combined_df['Day'] >= dia_inicio) & (combined_df['Day'] <= dia_fin) & (combined_df['Month'] == mes) & (combined_df['Year'] == año)]
    elif filtro == 'Rango de Meses':
        mes_inicio = st.number_input('Mes Inicio:', min_value=1, max_value=12, value=1)
        mes_fin = st.number_input('Mes Fin:', min_value=1, max_value=12, value=12)
        año_inicio = st.number_input('Año Inicio:', min_value=2000, max_value=2100, value=2022)
        año_fin = st.number_input('Año Fin:', min_value=2000, max_value=2100, value=2023)
        filtered_df = combined_df[((combined_df['Year'] > año_inicio) & (combined_df['Year'] < año_fin)) |
                                ((combined_df['Year'] == año_inicio) & (combined_df['Month'] >= mes_inicio)) |
                                ((combined_df['Year'] == año_fin) & (combined_df['Month'] <= mes_fin))]
    elif filtro == 'Rango de Años':
        año_inicio = st.number_input('Año Inicio:', min_value=2000, max_value=2100, value=2022)
        año_fin = st.number_input('Año Fin:', min_value=2000, max_value=2100, value=2023)
        filtered_df = combined_df[(combined_df['Year'] >= año_inicio) & (combined_df['Year'] <= año_fin)]

    elif filtro == 'Ticket/Copy':
        ticket_filtro = st.text_input('Ingrese el número de ticket o copy para filtrar').strip()

        if ticket_filtro:
            # Crear DataFrame vacío para acumular resultados
            filtered_df = pd.DataFrame()

            # Convertir todos los tickets a string y remover espacios extra para asegurar coincidencia
            combined_df['Ticket'] = combined_df['Ticket'].astype(str).str.strip()

            # Filtrar por 'Ticket' en los archivos principales
            principal_filter = combined_df[
                (combined_df['Source'] == 'Principal') & (combined_df['Ticket'] == ticket_filtro)
            ]

            # Filtrar por 'copy' en los archivos secundarios
            secondary_filter = combined_df[
                (combined_df['Source'] != 'Principal') & (combined_df['copy_in_hover'].str.contains(ticket_filtro, na=False))
            ]

            # Concatenar los resultados de ambos filtros
            filtered_df = pd.concat([principal_filter, secondary_filter], ignore_index=True)




    # Reemplazar NaN en 'Size' con 0
    if 'Size' in filtered_df.columns:
        filtered_df['Size'] = filtered_df['Size'].fillna(0)

    # Actualizar el mapa de símbolos y colores
    symbol_map = {
        'Open Transactions - Main': 'circle',
        'Closed Transactions - Main': 'x',
        'Open Trades - Main': 'square',
        f'Open Transactions - {file_id}': 'triangle-up',
        f'Closed Transactions - {file_id}': 'triangle-down'
    }

    color_discrete_map = {
        'Open Transactions - Main': 'blue',
        'Closed Transactions - Main': 'red',
        'Open Trades - Main': 'purple',
        f'Open Transactions - {file_id}': 'green',
        f'Closed Transactions - {file_id}': 'orange'
    }

    # Crear la gráfica con los nuevos mapas
    fig = px.scatter(filtered_df, x='Time', y='Price', color='Type',
                     symbol='Type', symbol_map=symbol_map, color_discrete_map=color_discrete_map,
                     title=f'Scatter Plot ordenado por Precio (Filtrado por {filtro})',
                     hover_data=hover_data, size_max=10)

    st.plotly_chart(fig)


# Botón para mostrar u ocultar las tablas de datos
if st.button('Mostrar/Ocultar Tablas de Datos'):
    st.subheader('Datos del Archivo Principal (sin columnas adicionales)')
    
    # Columnas que no queremos mostrar
    columnas_a_ocultar = ['Source', 'Type', 'Day', 'Month', 'Year']

    # Filtrar columnas que están en el DataFrame pero que no queremos mostrar
    if df_combined_final_principal is not None:
        columnas_principal = [col for col in df_combined_final_principal.columns if col not in columnas_a_ocultar]
        st.dataframe(df_combined_final_principal[columnas_principal])  # Mostrar solo las columnas filtradas

    # Mostrar la tabla del archivo adicional (df3) si está cargado
    if df_combined_final_df3 is not None:
        st.subheader('Datos del Archivo Adicional (df3) (sin columnas adicionales)')
        columnas_df3 = [col for col in df_combined_final_df3.columns if col not in columnas_a_ocultar]
        st.dataframe(df_combined_final_df3[columnas_df3])  # Mostrar solo las columnas filtradas
else:
    st.write("Por favor, carga un archivo HTML para comenzar.")    