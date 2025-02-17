import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image
import requests
from io import BytesIO
from datetime import datetime

# Configuración de credenciales
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
client = gspread.authorize(creds)

# Abre la hoja de cálculo
spreadsheet = client.open_by_key("1TE9IPz-7T_vcWx-MbBNGZzdVGnXkggTNWAbLbx1_39Q")
worksheet = spreadsheet.sheet1
logs_worksheet = spreadsheet.worksheet("Logs")  # Hoja de logs

# Contraseña predefinida (puedes cambiarla por una más segura)
PASSWORD = "ikarox"

def get_data():
    """Obtiene todos los registros de la hoja."""
    return worksheet.get_all_records()

def update_stock(row_index, new_stock):
    """Actualiza el stock en una fila específica"""
    # La columna A (1) es UNIDADES, sumamos 2 al índice (fila 1 = headers)
    worksheet.update_cell(row_index + 2, 1, new_stock)

def log_transaction(product, operation, quantity, old_stock, new_stock):
    """Registra una transacción en la hoja de logs."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Fecha y hora actual
    logs_worksheet.append_row([timestamp, product, operation, quantity, old_stock, new_stock])

# Interfaz de Streamlit
st.title("Gestión de Inventario 📦")

# ------------------------------------------
# Sección 1: Filtro de stock
# ------------------------------------------
st.header("🔍 Verificar stock")
data = get_data()
product_list = [item["DESCRIPCION"] for item in data]
search_term = st.selectbox("Seleccionar producto:", product_list, key="selectbox_search")
if search_term:
    data = get_data()
    filtered_items = [item for item in data if search_term.lower() in item["DESCRIPCION"].lower()]
    
    if filtered_items:
        st.subheader("Resultados de búsqueda:")
        for item in filtered_items:
            status = "✅ En stock" if item["UNIDADES"] > 0 else "❌ Agotado"
            # Mostrar descripción y estado
            st.write(f"{status} - {item['DESCRIPCION']}")
            
            # Mostrar unidades con st.markdown (más grandes)
            st.markdown(
                f"<h1 style='text-align: center; color: red; font-size: 300px;'>{item['UNIDADES']}</h1>",
                unsafe_allow_html=True
            )
            
            # Mostrar imagen del producto
            image_url = item.get("URL", "")
            if image_url:
                try:
                    response = requests.get(image_url)
                    img = Image.open(BytesIO(response.content))
                    st.image(img, caption=item["DESCRIPCION"], use_container_width=True)
                except Exception as e:
                    st.error(f"No se pudo cargar la imagen: {str(e)}")
            else:
                st.warning(f"No hay imagen disponible para {item['DESCRIPCION']}.")
    else:
        st.warning("No se encontraron productos con esa descripción")

# ------------------------------------------
# Sección 2: Actualización de stock
# ------------------------------------------
st.header("🔄 Actualizar stock")
data = get_data()
product_list = [item["DESCRIPCION"] for item in data]
if product_list:
    selected_product = st.selectbox("Seleccionar producto:", product_list, key="selectbox_update")    
    # Encontrar el ítem seleccionado
    selected_item = next(item for item in data if item["DESCRIPCION"] == selected_product)
    current_stock = selected_item["UNIDADES"]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Stock actual", current_stock)
    
    with col2:
        operation = st.radio("Operación:", ["Venta", "Reabastecimiento"])
    
    delta = st.number_input(
        f"Unidades a {'restar' if operation == 'Venta' else 'sumar'}:",
        min_value=0,
        key="delta"
    )

    # Solicitar contraseña
    password = st.text_input("Ingrese la contraseña para actualizar el stock:", type="password")

    if st.button("Actualizar stock"):
        if password == PASSWORD:  # Validar contraseña
            try:
                # Calcular nuevo stock
                new_stock = current_stock - delta if operation == "Venta" else current_stock + delta
                
                if new_stock < 0:
                    st.error("No puedes tener stock negativo!")
                    st.stop()
                
                # Encontrar índice del producto
                row_index = next(i for i, item in enumerate(data) if item["DESCRIPCION"] == selected_product)
                
                # Registrar la transacción en los logs
                log_transaction(
                    product=selected_product,
                    operation=operation,
                    quantity=delta,
                    old_stock=current_stock,
                    new_stock=new_stock
                )
                
                # Actualizar en Google Sheets
                update_stock(row_index, new_stock)
                st.success(f"Stock actualizado exitosamente! Nuevo stock: {new_stock}")
                # st.experimental_rerun()
            
            except Exception as e:
                st.error(f"Error al actualizar: {str(e)}")
        else:
            st.error("Contraseña incorrecta. No se puede actualizar el stock.")
else:
    st.warning("No hay productos en el inventario")

# ------------------------------------------
# Sección 3: Vista completa del inventario
# ------------------------------------------
st.header("📋 Inventario completo")
st.dataframe(get_data())

# ------------------------------------------
# Sección 4: Añadir nuevo producto (existente)
# ------------------------------------------
# ... (mantén tu código existente para añadir nuevos productos)