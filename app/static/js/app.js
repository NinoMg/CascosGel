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

  const order = ['login', 'dashboard', 'pacientes', 'cascos', 'prestamo', 'historial'];
  const tabBtn = document.querySelectorAll('.nav-tab')[order.indexOf(name)];
  if (tabBtn) tabBtn.classList.add('active');

  window.scrollTo(0, 0);

  if (name === 'dashboard') cargarDashboard();
  if (name === 'pacientes') cargarPacientes();
  if (name === 'cascos') cargarStock();
  if (name === 'prestamo') prepararPrestamo();

}


let pacientesCache = [];

// Evita que un nombre con símbolos rompa o inyecte HTML
function esc(texto) {
  const d = document.createElement('div');
  d.textContent = texto ?? '';
  return d.innerHTML;
}

async function cargarPacientes() {
  if (!localStorage.getItem('token')) return;
  try {
    const res = await fetch(`${API_BASE}/pacientes`, { headers: getHeaders() });
    if (res.status === 401 || res.status === 422) {
      localStorage.removeItem('token');
      show('login');
      return;
    }
    if (!res.ok) return;
    pacientesCache = await res.json();
    renderPacientes();
  } catch (err) {
    console.error(err);
  }
}

function renderPacientes() {
  const tbody = document.getElementById('tabla-pacientes-body');
  if (!tbody) return;

  const q = (document.getElementById('paciente-buscar').value || '').trim().toLowerCase();
  const lista = pacientesCache.filter(p =>
    !q ||
    p.nombre.toLowerCase().includes(q) ||
    (p.telefono1 || '').includes(q) ||
    (p.telefono2 || '').includes(q)
  );

  if (!lista.length) {
    tbody.innerHTML = '<tr><td colspan="6">No hay pacientes para mostrar.</td></tr>';
    return;
  }

  tbody.innerHTML = lista.map(p => `
    <tr>
      <td><strong>${esc(p.nombre)}</strong></td>
      <td>${esc(p.direccion)}</td>
      <td>${esc(p.telefono1)}${p.telefono2 ? ' / ' + esc(p.telefono2) : ''}</td>
      <td><span class="badge badge-accent">${p.cantidad_cascos_prestados} prestados</span></td>
      <td>${esc(p.periodo)}</td>
      <td>
        <div class="row-actions">
          <button class="btn btn-sm" onclick="editarPaciente(${p.id})">Editar</button>
          <button class="btn btn-sm" onclick="show('historial')">Ver</button>
          <button class="btn btn-sm btn-wsp" onclick="enviarWhatsAppPaciente(${p.id})">💬 WhatsApp</button>
        </div>
      </td>
    </tr>
  `).join('');
}

async function guardarPaciente() {
  const id = document.getElementById('paciente-id').value;
  const body = {
    nombre: document.getElementById('paciente-nombre').value,
    direccion: document.getElementById('paciente-direccion').value,
    telefono1: document.getElementById('paciente-tel1').value,
    telefono2: document.getElementById('paciente-tel2').value,
    periodo: document.getElementById('paciente-periodo').value
  };

  try {
    const res = await fetch(`${API_BASE}/pacientes${id ? '/' + id : ''}`, {
      method: id ? 'PUT' : 'POST',
      headers: getHeaders(),
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (res.ok) {
      alert(id ? '✅ Paciente actualizado.' : '✅ Paciente registrado.');
      cancelarEdicionPaciente();
      cargarPacientes();
    } else {
      alert(data.error || 'Ocurrió un error.');
    }
  } catch (err) {
    console.error(err);
    alert('No se pudo conectar con el servidor.');
  }
}

function editarPaciente(id) {
  const p = pacientesCache.find(x => x.id === id);
  if (!p) return;
  document.getElementById('paciente-id').value = p.id;
  document.getElementById('paciente-nombre').value = p.nombre;
  document.getElementById('paciente-direccion').value = p.direccion;
  document.getElementById('paciente-tel1').value = p.telefono1;
  document.getElementById('paciente-tel2').value = p.telefono2 || '';
  document.getElementById('paciente-periodo').value = p.periodo;
  document.getElementById('paciente-form-titulo').innerText = '✏️ Editar paciente';
  document.getElementById('paciente-cancelar').style.display = '';
  window.scrollTo(0, 0);
}

function cancelarEdicionPaciente() {
  ['paciente-id', 'paciente-nombre', 'paciente-direccion', 'paciente-tel1', 'paciente-tel2']
    .forEach(i => document.getElementById(i).value = '');
  document.getElementById('paciente-periodo').value = '6 meses';
  document.getElementById('paciente-form-titulo').innerText = '➕ Nuevo paciente';
  document.getElementById('paciente-cancelar').style.display = 'none';
}

function enviarWhatsApp(telefono, nombre, fechaVencimiento) {
  if (!telefono) {
    alert('El paciente no tiene un número de teléfono registrado.');
    return;
  }
  let num = telefono.replace(/\D/g, '');
  if (num.startsWith('0')) num = num.substring(1);
  if (!num.startsWith('549')) num = '549' + num;

  const vence = fechaVencimiento ? `, cuyo vencimiento es el ${fechaVencimiento}` : '';
  const mensaje = encodeURIComponent(
    `Hola ${nombre}, te escribimos de la Fundación Oncológica para coordinar el seguimiento/devolución del casco de gel prestado${vence}. ¡Muchas gracias!`
  );
  window.open(`https://wa.me/${num}?text=${mensaje}`, '_blank');
}

function enviarWhatsAppPaciente(id) {
  const p = pacientesCache.find(x => x.id === id);
  if (p) enviarWhatsApp(p.telefono1, p.nombre, null);
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

// ---- Nuevo préstamo ----
const DIAS_PERIODO = { '1 mes': 30, '3 meses': 90, '6 meses': 180, '12 meses': 365 };

// Fecha local en formato AAAA-MM-DD (evita desfases de zona horaria)
function fechaISO(f) {
  const m = String(f.getMonth() + 1).padStart(2, '0');
  const d = String(f.getDate()).padStart(2, '0');
  return `${f.getFullYear()}-${m}-${d}`;
}

async function prepararPrestamo() {
  if (!localStorage.getItem('token')) return;
  try {
    const [resP, resS] = await Promise.all([
      fetch(`${API_BASE}/pacientes`, { headers: getHeaders() }),
      fetch(`${API_BASE}/stock`, { headers: getHeaders() })
    ]);
    if (resP.status === 401 || resP.status === 422) {
      localStorage.removeItem('token');
      show('login');
      return;
    }
    if (!resP.ok || !resS.ok) return;

    pacientesCache = await resP.json();
    const stock = await resS.json();
    document.getElementById('prestamo-disponibles').innerText = stock.disponibles;
    document.getElementById('prestamo-cantidad').max = stock.disponibles;

    const lista = document.getElementById('lista-pacientes');
    lista.innerHTML = '';
    pacientesCache.forEach(p => {
      const op = document.createElement('option');
      op.value = etiquetaPaciente(p);
      lista.appendChild(op);
    });
    document.getElementById('prestamo-paciente-input').value = '';
    document.getElementById('prestamo-paciente').value = '';
    document.getElementById('prestamo-vencimiento').value = '';
  } catch (err) {
    console.error(err);
  }
}

// Texto que se ve en el buscador: nombre + teléfono (distingue a dos pacientes con el mismo nombre)
function etiquetaPaciente(p) {
  return p.telefono1 ? `${p.nombre} — ${p.telefono1}` : p.nombre;
}

function seleccionarPacientePrestamo() {
  const texto = document.getElementById('prestamo-paciente-input').value;
  const p = pacientesCache.find(x => etiquetaPaciente(x) === texto);
  document.getElementById('prestamo-paciente').value = p ? p.id : '';
  actualizarVencimientoSugerido();
}

function actualizarVencimientoSugerido() {
  const id = parseInt(document.getElementById('prestamo-paciente').value, 10);
  const p = pacientesCache.find(x => x.id === id);
  const campo = document.getElementById('prestamo-vencimiento');
  if (!p) { campo.value = ''; return; }
  const f = new Date();
  f.setDate(f.getDate() + (DIAS_PERIODO[p.periodo] || 180));
  campo.value = fechaISO(f);
}

async function guardarPrestamo() {
  const paciente_id = parseInt(document.getElementById('prestamo-paciente').value, 10);
  const cantidad = parseInt(document.getElementById('prestamo-cantidad').value, 10);
  const fecha_vencimiento = document.getElementById('prestamo-vencimiento').value;
  const observaciones = document.getElementById('prestamo-obs').value;

  if (!paciente_id) { alert('Elegí un paciente de la lista de sugerencias.'); return; }
  if (!cantidad || cantidad < 1) { alert('Ingresá una cantidad válida (1 o más).'); return; }

  try {
    const res = await fetch(`${API_BASE}/prestamos`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ paciente_id, cantidad, fecha_vencimiento, observaciones })
    });
    if (res.status === 401 || res.status === 422) {
      localStorage.removeItem('token');
      alert('Tu sesión expiró. Volvé a iniciar sesión.');
      show('login');
      return;
    }
    const data = await res.json();
    if (res.ok) {
      alert('✅ Préstamo registrado.');
      document.getElementById('prestamo-cantidad').value = 1;
      document.getElementById('prestamo-obs').value = '';
      prepararPrestamo();
      cargarDashboard();
    } else {
      alert(data.error || 'Ocurrió un error.');
    }
  } catch (err) {
    console.error(err);
    alert('No se pudo conectar con el servidor.');
  }
}