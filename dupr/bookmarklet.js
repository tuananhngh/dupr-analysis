// "Sync to DUPR Analysis" bookmarklet - readable source.
//
// Why a bookmarklet: DUPR's API only trusts requests coming from a logged-in
// dashboard.dupr.com page (httpOnly session cookie). Logins from scripts or
// servers get blocked or time out. So this runs ON dashboard.dupr.com, using
// the session you already have (password + email code done in DUPR's own page),
// downloads your data, then opens the DUPR Analysis page with the data in the
// URL #fragment. A #fragment is never sent over the network: only your browser
// sees it. No password or token is ever copied.
//
// The page that installs the bookmark fills in __TARGET__ (where to send the data:
// the website, or the local app's /import page) and turns this file into a javascript: link.
// Rules for this file (lines are joined into one): full-line comments only,
// every statement ends with a semicolon.
(async () => {
  const TARGET = '__TARGET__';
  const API = 'https://api.dupr.com';
  if (!/(^|\.)dupr\.com$/.test(location.hostname)) {
    alert('Open dashboard.dupr.com (logged in), then click this bookmark there.');
    return;
  }
  if (document.getElementById('dupra-panel')) return;
  const box = document.createElement('div');
  box.id = 'dupra-panel';
  box.style.cssText = 'position:fixed;left:12px;right:12px;top:12px;z-index:2147483647;max-width:420px;margin:0 auto;'
    + 'background:#fcfcfb;color:#0b0b0b;border:1px solid #2a78d6;border-radius:12px;padding:16px 18px;'
    + 'font:15px/1.5 system-ui,sans-serif;box-shadow:0 10px 30px rgba(0,0,0,.25)';
  box.innerHTML = '<b>DUPR Analysis: sync</b><div id="dupra-msg" style="margin-top:6px">Starting…</div>';
  document.body.appendChild(box);
  const say = t => { box.querySelector('#dupra-msg').textContent = t; };
  const fail = t => {
    say(t);
    const b = document.createElement('button');
    b.textContent = 'Close';
    b.style.cssText = 'margin-top:10px;padding:6px 14px;border-radius:8px;border:1px solid #2a78d6;background:none;color:#2a78d6;font:inherit;font-weight:600;cursor:pointer';
    b.onclick = () => box.remove();
    box.appendChild(b);
  };
  const H = { 'Accept': 'application/json', 'Content-Type': 'application/json',
              'X-Dupr-Client-Capabilities': 'totp,webauthn' };
  const call = async (method, path, body) => {
    const r = await fetch(API + path, { method, headers: H, credentials: 'include',
                                        body: body ? JSON.stringify(body) : undefined });
    if (!r.ok) {
      const t = await r.text().catch(() => '');
      const err = new Error(method + ' ' + path + ' returned ' + r.status + ' ' + t.slice(0, 120));
      err.status = r.status;
      throw err;
    }
    return r.json();
  };

  try {
    say('Reading your DUPR profile…');
    const meResp = await call('GET', '/user/v1.0/profile');
    const me = meResp.result || meResp;
    if (!me.id) throw new Error('DUPR profile had no id (keys: ' + Object.keys(me).join(', ') + ').');
    const id = me.id;
    try { me._player = (await call('GET', '/player/v1.0/' + id)).result; } catch (e) { if (e.status === 401) throw e; }

    const matches = [];
    let off = 0, total = null, size = 25, legacy = false;
    for (;;) {
      let r = null;
      if (!legacy) {
        try {
          r = await call('POST', '/player/v1.0/' + id + '/history',
            { filters: { eventFormat: null }, limit: size, offset: off,
              sort: { order: 'DESC', parameter: 'MATCH_DATE' } });
        } catch (e) {
          if (e.status === 400 && off === 0 && size > 10) { size = 10; continue; }
          if (e.status === 404 || e.status === 405) legacy = true;
          else throw e;
        }
      }
      if (legacy) r = await call('POST', '/match/v1.0/history', { limit: size, offset: off });
      const res = r.result !== undefined ? r.result : r;
      const page = Array.isArray(res) ? res : (res && res.hits);
      if (!Array.isArray(page)) throw new Error('Unexpected match-history response (keys: ' + Object.keys(res || {}).join(', ') + ')');
      if (res && res.total != null) total = res.total;
      matches.push(...page);
      off += size;
      say('Downloading matches: ' + matches.length + (total != null ? ' of ' + total : ''));
      if (page.length < size || (total != null && off >= total)) break;
    }

    say('Downloading rating history…');
    const ratingHistory = {};
    for (const kind of ['DOUBLES', 'SINGLES']) {
      const bodies = [{ type: kind, sortBy: 'asc', limit: 1000, offset: 0 },
                      { type: kind, limit: 1000, offset: 0 }, { type: kind }];
      for (const b of bodies) {
        try { ratingHistory[kind.toLowerCase()] = await call('POST', '/player/v1.0/' + id + '/rating-history', b); break; }
        catch (e) { if (e.status === 401) throw e; }
      }
    }

    say('Packing ' + matches.length + ' matches…');
    const data = { v: 1, profile: me, matches, ratingHistory };
    let bytes = new TextEncoder().encode(JSON.stringify(data)), tag = 'j';
    if (window.CompressionStream) {
      bytes = new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer());
      tag = 'z';
    }
    let bin = '';
    for (let i = 0; i < bytes.length; i += 32768) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 32768));
    const payload = tag + btoa(bin).split('+').join('-').split('/').join('_').replace(/=+$/, '');
    say('Opening DUPR Analysis…');
    location.href = TARGET + '#d=' + payload;
  } catch (e) {
    if (e.status === 401 || e.status === 403) fail('DUPR says you are not logged in. Log in at dashboard.dupr.com (with your email code), then click the bookmark again.');
    else fail('Sync failed: ' + e.message);
  }
})();
