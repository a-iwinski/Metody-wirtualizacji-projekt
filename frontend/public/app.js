// AI: plik przygotowany z pomocą Claude (Anthropic) – szkielet frontendu KM1
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
        td.textContent = v ?? "";
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6">Nie udało się pobrać danych</td></tr>`;
  }
}

loadHealth();
loadDevices();
