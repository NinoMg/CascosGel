const API_BASE = '/api';

// Función auxiliar para generar encabezados con el Token JWT
function getHeaders() {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : ''
  };
}

// Navegación entre vistas
function show(name) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));

  const targetScreen = document.getElementById('screen-' + name);
  if (targetScreen) targetScreen.classList.add('active');
  const tabBtn = document.querySelectorAll('.nav-tab')[order.indexOf(name)];
  if (tabBtn) tabBtn.classList.add('active');

  window.scrollTo(0, 0);

  if (name === 'dashboard') cargarDashboard();
  if (name === 'pacientes') cargarPacientes();
  if (name === 'cascos') cargarStock();
// borrar: if (name === 'prestamo') cargarCascosDisponibles();
  if (name === 'prestamo') cargarCascosDisponibles();
}

// Botón de WhatsApp dinámico
function enviarWhatsApp(telefono, nombrePaciente, codigoCasco, fechaVencimiento) {
  if (!telefono) {
    alert("El paciente no tiene un número de teléfono registrado.");
    return;
  }
  let num = telefono.replace(/\D/g, '');
  if (num.startsWith('0')) num = num.substring(1);
  if (!num.startsWith('549')) num = '549' + num;

  const mensaje = encodeURIComponent(
    `Hola ${nombrePaciente}, te escribimos de la Fundación Oncológica para coordinar el seguimiento/devolución del casco de gel (${codigoCasco || 'asignado'}) prestado, cuyo vencimiento es el ${fechaVencimiento || 'próximo'}. ¡Muchas gracias!`
  );
  window.open(`https://wa.me/${num}?text=${mensaje}`, '_blank');
}

// Iniciar sesión
async function iniciarSesion() {
  const userInp = document.getElementById('login-username').value;
  const passInp = document.getElementById('login-password').value;

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: userInp, password: passInp })
    });

    const data = await res.json();

    if (res.ok && (data.access_token || data.token)) {
      localStorage.setItem('token', data.access_token || data.token);
      show('dashboard');
    } else {
      alert(data.error || 'Credenciales inválidas');
    }
  } catch (err) {
    console.error('Error en login:', err);
    alert('No se pudo conectar con el servidor.');
  }
}

// Cargar indicadores del Dashboard
async function cargarDashboard() {
  const token = localStorage.getItem('token');
  if (!token) return;

  try {
    const res = await fetch(`${API_BASE}/cascos/resumen`, {
      method: 'GET',
      headers: getHeaders()
    });

    if (res.status === 422 || res.status === 401) {
      localStorage.removeItem('token');
      show('login');
      return;
    }

    if (!res.ok) return;

    const data = await res.json();
    document.getElementById('kpi-activos').innerText = data.prestados;
    document.getElementById('kpi-vencidos').innerText = data.vencidos;
    document.getElementById('kpi-disponibles').innerText = data.disponibles;
  } catch (err) {
    console.error(err);
  }
}

// Cargar Pacientes desde la API
async function cargarPacientes() {
  const token = localStorage.getItem('token');
  if (!token) return;

  try {
    const res = await fetch(`${API_BASE}/pacientes`, {
      headers: getHeaders()
    });
    if (!res.ok) return;

    const pacientes = await res.json();
    const tbody = document.getElementById('tabla-pacientes-body');
    if (!tbody) return;

    tbody.innerHTML = pacientes.map(p => `
      <tr>
        <td><strong>${p.nombre}</strong></td>
        <td>${p.direccion}</td>
        <td>${p.telefono1} ${p.telefono2 ? ' / ' + p.telefono2 : ''}</td>
        <td><span class="badge badge-accent">${p.cantidad_cascos_prestados} prestados</span></td>
        <td>${p.periodo}</td>
        <td>
          <div class="row-actions">
            <button class="btn btn-sm" onclick="show('historial')">Ver</button>
            <button class="btn btn-sm btn-wsp" onclick="enviarWhatsApp('${p.telefono1}', '${p.nombre}', 'C-001', 'Próximo')">💬 WhatsApp</button>
          </div>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}


async function cargarStock() {
  if (!localStorage.getItem('token')) return;
  try {
    const res = await fetch(`${API_BASE}/stock`, { headers: getHeaders() });
    if (res.status === 422 || res.status === 401) {
      localStorage.removeItem('token');
      show('login');
      return;
    }
    if (!res.ok) return;
    const s = await res.json();
    document.getElementById('stock-total').innerText = s.total;
    document.getElementById('stock-disponibles').innerText = s.disponibles;
    document.getElementById('stock-prestados').innerText = s.prestados;
    document.getElementById('stock-mantenimiento').innerText = s.mantenimiento;
    document.getElementById('stock-baja').innerText = s.baja;
  } catch (err) {
    console.error('Error cargando stock:', err);
  }
}

function leerCantidad(idInput) {
  const n = parseInt(document.getElementById(idInput).value, 10);
  if (!n || n < 1) {
    alert('Ingresá una cantidad válida (1 o más).');
    return null;
  }
  return n;
}

async function accionStock(url, body, mensajeOk) {
  try {
    const res = await fetch(`${API_BASE}${url}`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (res.ok) {
      alert(mensajeOk);
      cargarStock();
      cargarDashboard();
    } else {
      alert(data.error || 'Ocurrió un error.');
    }
  } catch (err) {
    console.error(err);
    alert('No se pudo conectar con el servidor.');
  }
}

function ingresarCascos() {
  const cantidad = leerCantidad('stock-ingreso-cant');
  if (cantidad) accionStock('/stock/ingreso', { cantidad }, '✅ Cascos agregados al stock.');
}

function moverMantenimiento(accion) {
  const cantidad = leerCantidad('stock-mant-cant');
  if (cantidad) accionStock('/stock/mantenimiento', { cantidad, accion }, '✅ Stock actualizado.');
}

function darDeBaja() {
  const cantidad = leerCantidad('stock-baja-cant');
  const origen = document.getElementById('stock-baja-origen').value;
  if (cantidad && confirm(`¿Dar de baja ${cantidad} casco(s)? No se puede deshacer.`)) {
    accionStock('/stock/baja', { cantidad, origen }, '✅ Baja registrada.');
  }
}