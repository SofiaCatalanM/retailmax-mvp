
import sqlite3
from datetime import datetime

def seed_database():
    conn = sqlite3.connect("retailmax.db")
    cursor = conn.cursor()
    
    # Productos de ejemplo (categoría abarrotes)
    productos = [
        ("SKU001", "Aceite Vegetal 1L", "Abarrotes", 10),
        ("SKU002", "Arroz 1kg", "Abarrotes", 15),
        ("SKU003", "Fideos 500g", "Abarrotes", 20),
        ("SKU004", "Azúcar 1kg", "Abarrotes", 12),
        ("SKU005", "Sal 500g", "Abarrotes", 25),
        ("SKU006", "Leche 1L", "Lácteos", 30),
        ("SKU007", "Yogurt 1L", "Lácteos", 20),
        ("SKU008", "Queso 250g", "Lácteos", 15),
        ("SKU009", "Pan de molde", "Panadería", 40),
        ("SKU010", "Galletas 200g", "Snacks", 50),
    ]
    
    for sku_id, descripcion, categoria, stock_minimo in productos:
        cursor.execute("""
            INSERT OR REPLACE INTO productos (sku_id, descripcion, categoria, stock_minimo)
            VALUES (?, ?, ?, ?)
        """, (sku_id, descripcion, categoria, stock_minimo))
        
        # Inicializar inventario con stock aleatorio
        import random
        stock_inicial = random.randint(0, 100)
        cursor.execute("""
            INSERT OR REPLACE INTO inventario_perpetuo (sku_id, tienda_id, cantidad_actual, fecha_actualizacion, operador_id)
            VALUES (?, 'TIENDA_001', ?, ?, 'SYSTEM')
        """, (sku_id, stock_inicial, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    print(f"Base de datos inicializada con {len(productos)} productos")

if __name__ == "__main__":
    seed_database()