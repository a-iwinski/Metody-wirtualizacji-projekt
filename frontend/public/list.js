// AI: plik przygotowany z pomocą Claude (Anthropic) – logika widoku listy
// Frontend łączy się wyłącznie z backendem (przez /api, proxy w nginx).

async function loadHealth() {
  const el = document.getElementById("status");
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || res.status);
    el.textContent = `Backend: ${data.status}, baza: ${data.db}`;
    el.className = "ok";
  } catch (e) {
    el.textContent = `Błąd: ${e.message}`;
    el.className = "err";
  }
}

async function loadDevices() {
  const tbody = document.getElementById("devices");
  try {
    const res = await fetch("/api/devices");
    const devices = await res.json();
    tbody.innerHTML = "";
    for (const d of devices) {
      const tr = document.createElement("tr");
      for (const v of [d.id, d.name, d.serial_number, d.category, d.location, d.status]) {
        const td = document.createElement("td");
        td.textContent = v ?? ""; // textContent – ochrona przed XSS
        tr.appendChild(td);
      }
      const actions = document.createElement("td");
      const edit = document.createElement("a");
      edit.href = `device.html?id=${d.id}`;
      edit.textContent = "Edytuj";
      const del = document.createElement("button");
      del.textContent = "Usuń";
      del.onclick = () => deleteDevice(d.id);
      actions.append(edit, " ", del);
      tr.appendChild(actions);
      tbody.appendChild(tr);
    }
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7">Nie udało się pobrać danych</td></tr>`;
  }
}

async function deleteDevice(id) {
  const res = await fetch(`/api/devices/${id}`, { method: "DELETE" });
  if (res.ok) loadDevices();
}

loadHealth();
loadDevices();
