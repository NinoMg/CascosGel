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

  const order = ['login', 'dashboard', 'pacientes', 'cascos', 'prestamo', 'historial', 'pitch'];
  const tabBtn = document.querySelectorAll('.nav-tab')[order.indexOf(name)];
  if (tabBtn) tabBtn.classList.add('active');

  window.scrollTo(0, 0);

  if (name === 'dashboard') cargarDashboard();
  if (name === 'pacientes') cargarPacientes();
  if (name === 'cascos') cargarTablaCascos();
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

// Obtener y renderizar la lista completa de cascos
async function cargarTablaCascos() {
  const token = localStorage.getItem('token');
  if (!token) return;

  try {
    const res = await fetch(`${API_BASE}/cascos`, {
      headers: getHeaders()
    });
    if (!res.ok) return;

    const cascos = await res.json();
    const tbody = document.getElementById('tabla-cascos-body');
    if (!tbody) return;

    tbody.innerHTML = cascos.map(c => {
      let badgeClase = 'badge-success';
      if (c.estado === 'prestado') badgeClase = 'badge-accent';
      if (c.estado === 'mantenimiento' || c.estado === 'baja') badgeClase = 'badge-danger';

      return `
        <tr>
          <td><strong>${c.codigo_identificador}</strong></td>
          <td><span class="badge badge-neutral">${c.origen === 'donacion' ? '🎁 Donación' : '🏛️ Fundación'}</span></td>
          <td><span class="badge ${badgeClase}">${c.estado.toUpperCase()}</span></td>
          <td>${c.observaciones || '—'}</td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error('Error cargando cascos:', err);
  }
}

// Enviar nuevo casco al Backend
async function guardarNuevoCasco() {
  const codigo = document.getElementById('casco-codigo').value.trim();
  const origen = document.getElementById('casco-origen').value;
  const obs = document.getElementById('casco-obs').value.trim();

  if (!codigo) {
    alert("Por favor, ingresa el código del casco (ej: C-015).");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/cascos`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        codigo_identificador: codigo,
        origen: origen,
        observaciones: obs
      })
    });

    const data = await res.json();

    if (res.ok) {
      alert("✅ Casco cargado con éxito al inventario.");
      document.getElementById('casco-codigo').value = '';
      document.getElementById('casco-obs').value = '';
      cargarTablaCascos();
      cargarDashboard();
    } else {
      alert(data.error || "Ocurrió un error al guardar el casco.");
    }
  } catch (err) {
    console.error('Error guardando casco:', err);
  }
}

// Cargar Cascos disponibles en el selector de nuevo préstamo
async function cargarCascosDisponibles() {
  const token = localStorage.getItem('token');
  if (!token) return;

  try {
    const res = await fetch(`${API_BASE}/cascos`, {
      headers: getHeaders()
    });
    if (!res.ok) return;
    const cascos = await res.json();
    const select = document.getElementById('select-casco');
    if (!select) return;

    select.innerHTML = cascos
      .filter(c => c.estado === 'disponible')
      .map(c => `<option value="${c.id}">${c.codigo_identificador} · ${c.origen}</option>`)
      .join('');
  } catch (err) {
    console.error(err);
  }
}
