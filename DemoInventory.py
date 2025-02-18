import streamlit as st
from PIL import Image
import requests
from io import BytesIO
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Crear una conexión a Google Sheets
conn = st.connection("gsheets", type="GSheetsConnection")

# Leer datos de la hoja principal
def get_data():
    """Obtiene todos los registros de la hoja."""
    return conn.read(worksheet="Sheet1")  # Ajusta el nombre de la hoja si es necesario

# Función para actualizar el stock
def update_stock(row_index, new_stock):
    """Actualiza el stock en una fila específica."""
    data = get_data()
    data.iloc[row_index, 0] = new_stock  # Actualiza la columna UNIDADES
    conn.update(worksheet="Sheet1", data=data)

# Función para registrar transacciones en la hoja de logs
def log_transaction(product, operation, quantity, old_stock, new_stock):
    """Registra una transacción en la hoja de logs."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logs_data = [timestamp, product, operation, quantity, old_stock, new_stock]
    conn.append(worksheet="Logs", data=[logs_data])  # Añade una nueva fila a la hoja Logs

# Interfaz de Streamlit
st.title("Gestión de Inventario 📦")

# ------------------------------------------
# Sección 1: Filtro de stock
# ------------------------------------------
st.header("🔍 Verificar stock")
data = get_data()
product_list = data["DESCRIPCION"].tolist()

search_term = st.selectbox("Seleccionar producto:", product_list, key="selectbox_search")
if search_term:
    filtered_items = data[data["DESCRIPCION"].str.lower().str.contains(search_term.lower())]

    if not filtered_items.empty:
        st.subheader("Resultados de búsqueda:")
        for _, item in filtered_items.iterrows():
            status = "✅ En stock" if item["UNIDADES"] > 0 else "❌ Agotado"
            st.write(f"{status} - {item['DESCRIPCION']} - Unidades: {item['UNIDADES']}")

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
product_list = data["DESCRIPCION"].tolist()

if product_list:
    selected_product = st.selectbox("Seleccionar producto:", product_list, key="selectbox_update")
    selected_item = data[data["DESCRIPCION"] == selected_product].iloc[0]
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

    password = st.text_input("Ingrese la contraseña para actualizar el stock:", type="password")
    PASSWORD = "mi_contraseña_segura"

    if st.button("Actualizar stock"):
        if password == PASSWORD:
            try:
                new_stock = current_stock - delta if operation == "Venta" else current_stock + delta

                if new_stock < 0:
                    st.error("No puedes tener stock negativo!")
                    st.stop()

                row_index = data[data["DESCRIPCION"] == selected_product].index[0]
                log_transaction(
                    product=selected_product,
                    operation=operation,
                    quantity=delta,
                    old_stock=current_stock,
                    new_stock=new_stock
                )
                update_stock(row_index, new_stock)
                st.success(f"Stock actualizado exitosamente! Nuevo stock: {new_stock}")
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
