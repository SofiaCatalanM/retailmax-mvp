
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import sqlite3
#import jwt
import os

app = FastAPI(title="RetailMax Inventory API", version="1.0.0")

# CORS para permitir acceso desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración
SECRET_KEY = os.getenv("SECRET_KEY", "retailmax_secret_key_2026")
DATABASE = "retailmax.db"

# Modelos de datos
class Producto(BaseModel):
    sku_id: str
    descripcion: str
    categoria: str
    stock_inicial: int
    stock_minimo: int = 10

class ConteoInventario(BaseModel):
    sku_id: str
    tienda_id: str
    cantidad: int
    operador_id: str

class StockResponse(BaseModel):
    sku_id: str
    descripcion: str
    categoria: str
    stock_actual: int
    stock_minimo: int
    fecha_actualizacion: str
    estado: str  # "OK", "BAJO", "CRITICO"

# Conexión a base de datos
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Inicializar base de datos
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Tabla de productos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            sku_id TEXT PRIMARY KEY,
            descripcion TEXT NOT NULL,
            categoria TEXT NOT NULL,
            stock_minimo INTEGER DEFAULT 10
        )
    """)
    
    # Tabla de inventario perpetuo
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario_perpetuo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku_id TEXT NOT NULL,
            tienda_id TEXT NOT NULL,
            cantidad_actual INTEGER NOT NULL,
            fecha_actualizacion TEXT NOT NULL,
            operador_id TEXT NOT NULL,
            FOREIGN KEY (sku_id) REFERENCES productos(sku_id)
        )
    """)
    
    # Tabla de movimientos (auditoría)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku_id TEXT NOT NULL,
            tienda_id TEXT NOT NULL,
            tipo TEXT NOT NULL,  -- 'conteo', 'ajuste', 'venta'
            cantidad INTEGER NOT NULL,
            fecha_hora TEXT NOT NULL,
            operador_id TEXT NOT NULL,
            origen TEXT DEFAULT 'manual'
        )
    """)
    
    conn.commit()
    conn.close()

# Endpoint: Cargar productos desde CSV (simplificado)
@app.post("/api/v1/products/load")
async def cargar_productos(productos: List[Producto]):
    conn = get_db()
    cursor = conn.cursor()
    
    cargados = 0
    errores = 0
    
    for prod in productos:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO productos (sku_id, descripcion, categoria, stock_minimo)
                VALUES (?, ?, ?, ?)
            """, (prod.sku_id, prod.descripcion, prod.categoria, prod.stock_minimo))
            
            # Inicializar inventario con stock_inicial
            cursor.execute("""
                INSERT OR REPLACE INTO inventario_perpetuo (sku_id, tienda_id, cantidad_actual, fecha_actualizacion, operador_id)
                VALUES (?, 'TIENDA_001', ?, ?, 'SYSTEM')
            """, (prod.sku_id, prod.stock_inicial, datetime.now().isoformat()))
            
            cargados += 1
        except Exception as e:
            errores += 1
    
    conn.commit()
    conn.close()
    
    return {
        "mensaje": "Productos cargados exitosamente",
        "cargados": cargados,
        "errores": errores
    }

# Endpoint: Registrar conteo físico
@app.post("/api/v1/inventory/sync")
async def sincronizar_conteo(conteo: ConteoInventario):
    conn = get_db()
    cursor = conn.cursor()
    
    # Validar que el SKU existe
    cursor.execute("SELECT sku_id FROM productos WHERE sku_id = ?", (conteo.sku_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"SKU {conteo.sku_id} no encontrado")
    
    # Actualizar inventario perpetuo
    cursor.execute("""
        INSERT OR REPLACE INTO inventario_perpetuo (sku_id, tienda_id, cantidad_actual, fecha_actualizacion, operador_id)
        VALUES (?, ?, ?, ?, ?)
    """, (conteo.sku_id, conteo.tienda_id, conteo.cantidad, datetime.now().isoformat(), conteo.operador_id))
    
    # Registrar movimiento en auditoría
    cursor.execute("""
        INSERT INTO movimientos (sku_id, tienda_id, tipo, cantidad, fecha_hora, operador_id, origen)
        VALUES (?, ?, 'conteo', ?, ?, ?, 'pwa')
    """, (conteo.sku_id, conteo.tienda_id, conteo.cantidad, datetime.now().isoformat(), conteo.operador_id))
    
    conn.commit()
    conn.close()
    
    return {
        "mensaje": "Conteo registrado exitosamente",
        "sku_id": conteo.sku_id,
        "cantidad": conteo.cantidad,
        "timestamp": datetime.now().isoformat()
    }

# Endpoint: Consultar stock actual
@app.get("/api/v1/inventory/stock/{sku_id}", response_model=StockResponse)
async def consultar_stock(sku_id: str, tienda_id: str = "TIENDA_001"):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.sku_id, p.descripcion, p.categoria, p.stock_minimo,
               i.cantidad_actual, i.fecha_actualizacion
        FROM productos p
        LEFT JOIN inventario_perpetuo i ON p.sku_id = i.sku_id AND i.tienda_id = ?
        WHERE p.sku_id = ?
    """, (tienda_id, sku_id))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail=f"SKU {sku_id} no encontrado")
    
    stock_actual = result["cantidad_actual"] or 0
    stock_minimo = result["stock_minimo"]
    
    # Determinar estado
    if stock_actual == 0:
        estado = "CRITICO"
    elif stock_actual < stock_minimo:
        estado = "BAJO"
    else:
        estado = "OK"
    
    return StockResponse(
        sku_id=result["sku_id"],
        descripcion=result["descripcion"],
        categoria=result["categoria"],
        stock_actual=stock_actual,
        stock_minimo=stock_minimo,
        fecha_actualizacion=result["fecha_actualizacion"] or "Nunca",
        estado=estado
    )

# Endpoint: Listar todos los productos con stock
@app.get("/api/v1/inventory/all", response_model=List[StockResponse])
async def listar_inventario(tienda_id: str = "TIENDA_001"):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.sku_id, p.descripcion, p.categoria, p.stock_minimo,
               i.cantidad_actual, i.fecha_actualizacion
        FROM productos p
        LEFT JOIN inventario_perpetuo i ON p.sku_id = i.sku_id AND i.tienda_id = ?
        ORDER BY p.categoria, p.descripcion
    """, (tienda_id,))
    
    results = cursor.fetchall()
    conn.close()
    
    inventory = []
    for r in results:
        stock_actual = r["cantidad_actual"] or 0
        stock_minimo = r["stock_minimo"]
        
        if stock_actual == 0:
            estado = "CRITICO"
        elif stock_actual < stock_minimo:
            estado = "BAJO"
        else:
            estado = "OK"
        
        inventory.append(StockResponse(
            sku_id=r["sku_id"],
            descripcion=r["descripcion"],
            categoria=r["categoria"],
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
            fecha_actualizacion=r["fecha_actualizacion"] or "Nunca",
            estado=estado
        ))
    
    return inventory

# Endpoint: Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Inicializar BD al arrancar
@app.on_event("startup")
async def startup_event():
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)