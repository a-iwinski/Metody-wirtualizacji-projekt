// AI: plik przygotowany z pomocą Claude (Anthropic) – logika widoku dodawania / edycji
// device.html          → dodawanie (POST)
// device.html?id=3     → edycja urządzenia 3 (GET + PUT)

const id = new URLSearchParams(location.search).get("id");
const form = document.getElementById("form");
const msg = document.getElementById("msg");

function show(text, ok) {
  msg.textContent = text;
  msg.className = ok ? "ok" : "err";
}

async function fillSelect(name, url) {
  const items = await (await fetch(url)).json();
  const select = form.elements[name];
  for (const it of items) select.add(new Option(it.name, it.id));
}

async function init() {
  await fillSelect("category_id", "/api/categories");
  await fillSelect("location_id", "/api/locations");

  if (id) {
    document.getElementById("title").textContent = `Edycja urządzenia #${id}`;
    const res = await fetch(`/api/devices/${id}`);
    if (!res.ok) return show("Urządzenie nie istnieje", false);
    const d = await res.json();
    for (const f of ["name", "serial_number", "category_id", "location_id", "status"]) {
      form.elements[f].value = d[f];
    }
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = Object.fromEntries(new FormData(form));
  body.category_id = Number(body.category_id);
  body.location_id = Number(body.location_id);

  const res = await fetch(id ? `/api/devices/${id}` : "/api/devices", {
    method: id ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();

  if (res.ok) {
    show(`Zapisano urządzenie #${data.id}`, true);
    if (!id) form.reset();
  } else {
    show(data.detail || "Błąd zapisu", false);
  }
});

init();
