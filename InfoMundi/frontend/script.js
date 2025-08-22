// ========= Config dinámico según dónde estás (HTTPS Nginx vs local) =========
const isHttpsNginx = window.location.protocol === "https:" && window.location.port === "8443";
const API_BASE = isHttpsNginx ? "" : "http://127.0.0.1:8000";
const API_PAISES = "https://restcountries.com/v3.1/name/";
const API_LOCAL = `${API_BASE}/favoritos`;
const API_CLEANED = `${API_BASE}/api/cleaned_data`;

// ========= Búsqueda de país (API pública) =========
async function buscarPais() {
  const nombre = document.getElementById("input-pais").value.trim();
  if (!nombre) return alert("Escribí un nombre de país");

  try {
    const res = await fetch(`${API_PAISES}${encodeURIComponent(nombre)}`);
    if (!res.ok) throw new Error("Falla al consultar RestCountries");
    const data = await res.json();
    mostrarResultados(data);
  } catch (error) {
    alert("No se pudo buscar el país 😢");
    console.error(error);
  }
}

// ========= Render de resultados =========
function mostrarResultados(paises) {
  const cont = document.getElementById("resultados");
  cont.innerHTML = "";

  paises.forEach((pais) => {
    const nombre = pais.name?.common ?? "Desconocido";
    const capital = pais.capital?.[0] ?? "Desconocida";
    const continente = pais.continents?.[0] ?? "Desconocido";
    const bandera = pais.flags?.png || pais.flags?.svg || "";

    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <img src="${bandera}" alt="Bandera de ${nombre}" />
      <div class="card__body">
        <h3>${nombre}</h3>
        <p><strong>Capital:</strong> ${capital}</p>
        <p><strong>Continente:</strong> ${continente}</p>
        <button class="btn btn--primary" onclick="guardarFavorito('${nombre.replace(/'/g,"\\'")}', '${bandera.replace(/'/g,"\\'")}')">💾 Guardar favorito</button>
      </div>
    `;
    cont.appendChild(card);
  });
}

// ========= CRUD Favoritos =========
async function guardarFavorito(nombre, imagen_url) {
  const comentario = prompt(`¿Por qué te gusta ${nombre}? 📝`);
  if (!comentario) return;

  try {
    const res = await fetch(API_LOCAL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre, comentario, imagen_url }),
    });
    if (!res.ok) throw new Error("Error al guardar favorito");
    cargarFavoritos();
    cargarDatosLimpios();
  } catch (e) {
    console.error(e);
    alert("No se pudo guardar 😓");
  }
}

async function cargarFavoritos() {
  try {
    const res = await fetch(API_LOCAL);
    const favoritos = await res.json();
    const cont = document.getElementById("favoritos");
    cont.innerHTML = "";

    favoritos.forEach((fav) => {
      const card = document.createElement("div");
      card.className = "card";
      card.innerHTML = `
        <img src="${fav.imagen_url}" alt="Imagen de ${fav.nombre}" />
        <div class="card__body">
          <h3>${fav.nombre}</h3>
          <p><strong>Comentario:</strong> ${fav.comentario}</p>
        </div>
      `;
      cont.appendChild(card);
    });
  } catch (error) {
    console.error("Error al cargar favoritos", error);
  }
}

// ========= Tabla cleaned_data =========
async function cargarDatosLimpios() {
  try {
    const res = await fetch(API_CLEANED);
    const data = await res.json();
    const tbody = document.querySelector("#cleanedTable tbody");
    tbody.innerHTML = "";

    data.forEach((row) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${row.id}</td>
        <td>${row.nombre}</td>
        <td>${row.pais}</td>
        <td>${row.fecha ?? "-"}</td>
        <td>${row.valor ?? "-"}</td>
        <td>${row.fuente ?? "-"}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (error) {
    console.error("Error al cargar datos limpios", error);
  }
}

// ========= Tema (oscuro/claro) =========
(function setupThemeToggle(){
  const toggle = document.getElementById("themeToggle");
  if (!toggle) return;

  // estado inicial
  const saved = localStorage.getItem("infomundi-theme");
  if (saved === "light") {
    document.body.classList.add("theme-light");
    toggle.textContent = "☀️";
  } else {
    toggle.textContent = "🌙";
  }

  toggle.addEventListener("click", () => {
    const isLight = document.body.classList.toggle("theme-light");
    localStorage.setItem("infomundi-theme", isLight ? "light" : "dark");
    toggle.textContent = isLight ? "☀️" : "🌙";
  });
})();

// ========= Boot =========
window.addEventListener("load", () => {
  cargarFavoritos();
  cargarDatosLimpios();
});
