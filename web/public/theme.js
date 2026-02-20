// Prevent theme flash (respect saved preference).
// Kept as a separate static file so we can keep a strict CSP (no inline scripts).
;(function () {
  try {
    var t = localStorage.getItem('theme')
    if (t === 'dark') document.documentElement.classList.add('dark')
  } catch (e) {
    // no-op
  }
})()
