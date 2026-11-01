// Mobile menu
const burger = document.getElementById("burger"), menu = document.getElementById("menu");
burger.addEventListener("click", () => { const open = menu.classList.toggle("open"); burger.setAttribute("aria-expanded", open); });
// Confirm before destructive forms
document.querySelectorAll("form[data-confirm]").forEach(f => f.addEventListener("submit", e => { if (!confirm(f.dataset.confirm)) e.preventDefault(); }));
// Live character counters
document.querySelectorAll("[data-count]").forEach(inp => {
  const out = document.createElement("div"); out.className = "count"; inp.parentElement.append(out);
  const update = () => { out.textContent = `${inp.value.length} / ${inp.maxLength}`; };
  inp.addEventListener("input", update); update();
});
// Auto-hide flash messages
setTimeout(() => document.querySelectorAll(".flash").forEach(f => { f.style.transition = "opacity .5s"; f.style.opacity = "0"; setTimeout(() => f.remove(), 600); }), 5000);
