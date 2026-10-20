
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Variables globales
let productoSeleccionado = null;

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initEventListeners();
    cargarInventario();
});

// Tabs
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remover active de todos
            tabs.forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
            
            // Activar el seleccionado
            tab.classList.add('active');
            const tabName = tab.dataset.tab;
            document.getElementById(`tab-${tabName}`).classList.add('active');
            
            // Cargar datos si es necesario
            if (tabName === 'consulta') {
                cargarInventario();
            }
        });
    });
}

// Event listeners
function initEventListeners() {
    // Input SKU
    document.getElementById('sku-input').addEventListener('input', validarSKU);
    
    // Botón escanear (simulado)
    document.getElementById('scan-btn').addEventListener('click', () => {
        alert('📷 En un MVP real, aquí se abriría la cámara para escanear el código de barras.\n\nPara esta demo, ingresa manualmente: SKU001, SKU002, etc.');
    });
    
    // Input cantidad
    document.getElementById('cantidad-input').addEventListener('input', validarFormulario);
    
    // Botón registrar
    document.getElementById('registrar-btn').addEventListener('click', registrarConteo);
    
    // Filtro categoría
    document.getElementById('filtro-categoria').addEventListener('change', cargarInventario);
}

// Validar SKU
async function validarSKU() {
    const skuInput = document.getElementById('sku-input');
    const sku = skuInput.value.trim();
    
    if (sku.length < 3) {
        ocultarInfoProducto();
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/inventory/stock/${sku}`);
        
        if (response.ok) {
            const data = await response.json();
            mostrarInfoProducto(data);
            productoSeleccionado = data;
        } else {
            ocultarInfoProducto();
            productoSeleccionado = null;
        }
    } catch (error) {
        console.error('Error al validar SKU:', error);
        ocultarInfoProducto();
    }
    
    validarFormulario();
}

// Mostrar info del producto
function mostrarInfoProducto(data) {
    const infoDiv = document.getElementById('producto-info');
    document.getElementById('producto-nombre').textContent = data.descripcion;
    document.getElementById('producto-categoria').textContent = `Categoría: ${data.categoria}`;
    document.getElementById('stock-actual').textContent = data.stock_actual;
    
    infoDiv.classList.remove('hidden');
}

// Ocultar info del producto
function ocultarInfoProducto() {
    document.getElementById('producto-info').classList.add('hidden');
}

// Validar formulario
function validarFormulario() {
    const sku = document.getElementById('sku-input').value.trim();
    const cantidad = document.getElementById('cantidad-input').value;
    const btn = document.getElementById('registrar-btn');
    
    if (sku && cantidad && productoSeleccionado) {
        btn.disabled = false;
    } else {
        btn.disabled = true;
    }
}

// Registrar conteo
async function registrarConteo() {
    const sku = document.getElementById('sku-input').value.trim();
    const cantidad = parseInt(document.getElementById('cantidad-input').value);
    
    const data = {
        sku_id: sku,
        tienda_id: 'TIENDA_001',
        cantidad: cantidad,
        operador_id: 'OPERADOR_001'
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/inventory/sync`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const result = await response.json();
            mostrarMensaje('✅ Conteo registrado exitosamente', 'success');
            
            // Limpiar formulario
            document.getElementById('sku-input').value = '';
            document.getElementById('cantidad-input').value = '';
            ocultarInfoProducto();
            productoSeleccionado = null;
            validarFormulario();
            
            // Actualizar info del producto
            setTimeout(() => validarSKU(), 500);
        } else {
            const error = await response.json();
            mostrarMensaje(`❌ Error: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error al registrar conteo:', error);
        mostrarMensaje('❌ Error de conexión con el servidor', 'error');
    }
}

// Mostrar mensaje
function mostrarMensaje(texto, tipo) {
    const mensajeDiv = document.getElementById('mensaje-exito');
    mensajeDiv.textContent = texto;
    mensajeDiv.className = `mensaje ${tipo}`;
    mensajeDiv.classList.remove('hidden');
    
    setTimeout(() => {
        mensajeDiv.classList.add('hidden');
    }, 3000);
}

// Cargar inventario
async function cargarInventario() {
    const listaDiv = document.getElementById('inventario-lista');
    listaDiv.innerHTML = '<p class="loading">Cargando inventario...</p>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/inventory/all`);
        
        if (response.ok) {
            const data = await response.json();
            
            // Filtrar por categoría si es necesario
            const filtro = document.getElementById('filtro-categoria').value;
            const filtrado = filtro ? data.filter(p => p.categoria === filtro) : data;
            
            if (filtrado.length === 0) {
                listaDiv.innerHTML = '<p class="empty">No hay productos en esta categoría</p>';
                return;
            }
            
            listaDiv.innerHTML = filtrado.map(producto => `
                <div class="producto-item estado-${producto.estado.toLowerCase()}">
                    <div class="producto-header">
                        <strong>${producto.sku_id}</strong>
                        <span class="estado-badge">${producto.estado}</span>
                    </div>
                    <div class="producto-body">
                        <p>${producto.descripcion}</p>
                        <p class="categoria">${producto.categoria}</p>
                    </div>
                    <div class="producto-footer">
                        <span class="stock">Stock: ${producto.stock_actual}</span>
                        <span class="minimo">Mín: ${producto.stock_minimo}</span>
                    </div>
                </div>
            `).join('');
        } else {
            listaDiv.innerHTML = '<p class="error">Error al cargar el inventario</p>';
        }
    } catch (error) {
        console.error('Error al cargar inventario:', error);
        listaDiv.innerHTML = '<p class="error">Error de conexión con el servidor</p>';
    }
}

// Service Worker registration
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js')
        .then(reg => console.log('Service Worker registrado'))
        .catch(err => console.error('Error al registrar Service Worker:', err));
}