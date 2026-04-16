/**
 * Shared fetch helpers - calls existing Django JSON endpoints with session cookie.
 */
(function () {
  'use strict';

  /**
   * @param {string} url
   * @param {RequestInit} options
   * @returns {Promise<{ok:boolean,status:number,data:any,text:string}>}
   */
  async function apiRequest(url, options) {
    const opts = Object.assign(
      {
        credentials: 'include',
        headers: {},
      },
      options || {}
    );
    if (!opts.headers) {
      opts.headers = {};
    }
    if (!opts.headers['Accept']) {
      opts.headers['Accept'] = 'application/json';
    }
    if (
      opts.body != null &&
      typeof opts.body === 'object' &&
      !(opts.body instanceof FormData) &&
      !(typeof opts.body === 'string')
    ) {
      opts.body = JSON.stringify(opts.body);
      if (!opts.headers['Content-Type']) {
        opts.headers['Content-Type'] = 'application/json';
      }
    }
    const res = await fetch(url, opts);
    const text = await res.text();
    let data = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch (_) {
        data = { _parse_error: true, raw: text };
      }
    }
    return { ok: res.ok, status: res.status, data: data, text: text };
  }

  window.apiGet = function (url) {
    return apiRequest(url, { method: 'GET' });
  };

  window.apiPost = function (url, body) {
    return apiRequest(url, { method: 'POST', body: body });
  };

  /**
   * Redirect to login UI if API returns 401.
   */
  window.requireAdminSession = async function () {
    var r = await window.apiGet('/admin/');
    if (r.status === 401) {
      window.location.href = '/ui/login/';
      return false;
    }
    if (r.status === 403) {
      var el = document.getElementById('adminAccessDenied');
      if (el) el.classList.remove('d-none');
      return false;
    }
    return true;
  };

  /**
   * Investor UI: session must be Investor; 401 → login, 403 → admin UI.
   */
  window.requireInvestorSession = async function () {
    var r = await window.apiGet('/companies/');
    if (r.status === 401) {
      window.location.href = '/ui/login/';
      return false;
    }
    if (r.status === 403) {
      window.location.href = '/ui/admin/';
      return false;
    }
    return true;
  };

  document.addEventListener('click', function (e) {
    var t = e.target;
    if (t && t.id === 'btnLogout') {
      e.preventDefault();
      window.apiPost('/logout/', {}).then(function () {
        window.location.href = '/ui/login/';
      });
    }
  });
})();
