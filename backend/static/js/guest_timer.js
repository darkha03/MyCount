(function() {
  function pad(n) { return String(n).padStart(2, '0'); }
  function formatRemaining(ms) {
    if (ms <= 0) return '00:00:00';
    var s = Math.floor(ms / 1000);
    var hrs = Math.floor(s / 3600);
    var mins = Math.floor((s % 3600) / 60);
    var secs = s % 60;
    return pad(hrs) + ':' + pad(mins) + ':' + pad(secs);
  }

  function startTimer(el) {
    if (!el) return;
    var iso = el.dataset.expire;
    if (!iso) return;
    var end = new Date(iso);
    if (isNaN(end.getTime())) return;

    function tick() {
      var now = new Date();
      var diff = end.getTime() - now.getTime();
      if (diff <= 0) {
        el.textContent = 'Expired';
        clearInterval(interval);
        // reload to let server-side decorator handle logout/cleanup
        setTimeout(function(){ window.location.reload(); }, 2000);
        return;
      }
      el.textContent = formatRemaining(diff);
    }

    tick();
    var interval = setInterval(tick, 1000);
  }

  document.addEventListener('DOMContentLoaded', function(){
    var el = document.getElementById('guest-timer');
    if (el) startTimer(el);
  });
})();
