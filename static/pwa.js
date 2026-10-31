(function () {
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(function () {});
    });
  }

  var KEY = "pwa_install_dismissed_until";
  var tombol = document.getElementById("pasang-pwa");
  var petunjuk = document.getElementById("petunjuk-ios");
  var sheet = document.getElementById("pwa-sheet");
  var btnLater = document.getElementById("pwa-sheet-later");
  var btnInstall = document.getElementById("pwa-sheet-install");
  var deferred = null;
  var sudahDitawar = false;
  var isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
  var standalone =
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true;

  function dismissed() {
    try {
      return Number(localStorage.getItem(KEY) || 0) > Date.now();
    } catch (e) {
      return false;
    }
  }

  function dismiss(days) {
    try {
      localStorage.setItem(KEY, String(Date.now() + days * 24 * 60 * 60 * 1000));
    } catch (e) {}
  }

  function tutupSheet() {
    if (!sheet) return;
    sheet.classList.remove("is-open");
    window.setTimeout(function () {
      sheet.hidden = true;
    }, 180);
  }

  function bukaSheet() {
    if (!sheet || standalone || dismissed() || sudahDitawar) return;
    sudahDitawar = true;
    sheet.hidden = false;
    if (isIOS) sheet.classList.add("is-ios");
    requestAnimationFrame(function () {
      sheet.classList.add("is-open");
    });
  }

  if (standalone) {
    if (tombol) tombol.hidden = true;
    if (petunjuk) petunjuk.hidden = true;
    return;
  }

  if (isIOS && petunjuk) petunjuk.hidden = false;

  window.addEventListener("beforeinstallprompt", function (event) {
    event.preventDefault();
    deferred = event;
    if (tombol) tombol.hidden = false;
  });

  function pasang() {
    if (!deferred) return;
    deferred.prompt();
    deferred.userChoice.finally(function () {
      deferred = null;
      if (tombol) tombol.hidden = true;
      dismiss(30);
      tutupSheet();
    });
  }

  if (tombol) tombol.addEventListener("click", pasang);
  if (btnInstall) btnInstall.addEventListener("click", pasang);
  if (btnLater) {
    btnLater.addEventListener("click", function () {
      dismiss(7);
      tutupSheet();
    });
  }
  if (sheet) {
    sheet.addEventListener("click", function (event) {
      if (event.target === sheet) {
        dismiss(7);
        tutupSheet();
      }
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && sheet.classList.contains("is-open")) {
        dismiss(7);
        tutupSheet();
      }
    });
  }

  window.setTimeout(function () {
    if (standalone || dismissed()) return;
    if (isIOS || deferred) bukaSheet();
  }, 2800);
})();
