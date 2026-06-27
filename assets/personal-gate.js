// Lightweight client-side gate for the personal-projects pages.
// NOTE: static hosting has no server, so this keeps pages out of search and
// behind a friendly prompt; it is not strong protection (content is in source).
(function () {
  var HASH = "bccb6abb625eaf092db278759e99f3e5ac90fc721b21990b09c751279d7a79ea"; // sha256("manessestrasse97")
  try { if (sessionStorage.getItem('pp_ok') === '1') return; } catch (e) {}

  function build() {
    var ov = document.createElement('div');
    ov.id = 'pp-gate';
    ov.style.cssText = 'position:fixed;inset:0;z-index:99999;background:#11160f;display:flex;align-items:center;justify-content:center;padding:2rem;';
    ov.innerHTML =
      '<div style="max-width:460px;text-align:center;font-family:Inter,Arial,sans-serif;color:#e8e8e6;">' +
        '<div style="font-size:.72rem;letter-spacing:.22em;text-transform:uppercase;color:#9bb87a;margin-bottom:1rem;">Personal &middot; private</div>' +
        '<h2 style="font-size:1.5rem;margin:0 0 1rem;font-weight:700;">A little password-protected</h2>' +
        '<p style="color:#a8a8a8;line-height:1.55;margin:0 0 1.5rem;">These are my personal projects, kept semi-private. If you&rsquo;d like the password, just write me and I&rsquo;ll happily share it: <a href="mailto:erika.freeman@igb-berlin.de" style="color:#9bb87a;">erika.freeman@igb-berlin.de</a>.</p>' +
        '<div><input id="pp-pw" type="password" placeholder="Password" autocomplete="off" style="padding:.6rem .9rem;border-radius:8px;border:1px solid #333;background:#1a1f18;color:#fff;font-size:1rem;width:190px;">' +
        '<button id="pp-go" style="margin-left:.5rem;padding:.62rem 1.1rem;border-radius:8px;border:none;background:#9bb87a;color:#11160f;font-weight:600;cursor:pointer;">Enter</button></div>' +
        '<div id="pp-err" style="color:#d08a8a;font-size:.85rem;margin-top:.8rem;min-height:1rem;"></div>' +
        '<div style="margin-top:1.5rem;"><a href="index.html" style="color:#8a8a8a;font-size:.85rem;">&larr; back to the main site</a></div>' +
      '</div>';
    document.body.appendChild(ov);
    document.documentElement.style.overflow = 'hidden';
    var pw = document.getElementById('pp-pw'), go = document.getElementById('pp-go'), err = document.getElementById('pp-err');
    async function check() {
      var buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(pw.value));
      var hex = Array.from(new Uint8Array(buf)).map(function (b) { return b.toString(16).padStart(2, '0'); }).join('');
      if (hex === HASH) {
        try { sessionStorage.setItem('pp_ok', '1'); } catch (e) {}
        ov.remove();
        document.documentElement.style.overflow = '';
      } else { err.textContent = 'Not quite — try again, or email me for the password.'; pw.value = ''; pw.focus(); }
    }
    go.addEventListener('click', check);
    pw.addEventListener('keydown', function (e) { if (e.key === 'Enter') check(); });
    pw.focus();
  }
  if (document.body) build(); else document.addEventListener('DOMContentLoaded', build);
})();
