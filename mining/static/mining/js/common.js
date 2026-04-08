/**
 * Shared UI helpers (alerts, formatting). Depends on api.js for apiGet/apiPost.
 */
(function () {
  'use strict';

  function el(id) {
    return document.getElementById(id);
  }

  /**
   * Show a Bootstrap alert in #globalAlert or a target element.
   * type: 'success' | 'danger' | 'warning' | 'info'
   */
  window.smShowAlert = function (message, type, targetId) {
    var holder = targetId ? el(targetId) : el('globalAlert');
    if (!holder) return;
    holder.className =
      'container pt-3 alert alert-' + (type || 'info') + ' alert-dismissible fade show';
    holder.setAttribute('role', 'alert');
    holder.innerHTML =
      message +
      '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
    holder.classList.remove('d-none');
  };

  window.smHideAlert = function (targetId) {
    var holder = targetId ? el(targetId) : el('globalAlert');
    if (!holder) return;
    holder.classList.add('d-none');
    holder.innerHTML = '';
  };

  /** Format API error payload { errors: {}, error: str } for display */
  window.smFormatApiErrors = function (data) {
    if (!data) return 'Request failed.';
    if (data.error) return data.error;
    if (data.errors) {
      var parts = [];
      for (var k in data.errors) {
        if (Object.prototype.hasOwnProperty.call(data.errors, k)) {
          parts.push(k + ': ' + (Array.isArray(data.errors[k]) ? data.errors[k].join(', ') : data.errors[k]));
        }
      }
      return parts.join(' ') || 'Validation failed.';
    }
    return 'Request failed.';
  };

  window.smNum = function (v, decimals) {
    if (v === null || v === undefined) return '—';
    var n = Number(v);
    if (Number.isNaN(n)) return String(v);
    if (decimals !== undefined) return n.toFixed(decimals);
    return String(n);
  };

  window.smSetLoading = function (rootEl, loading) {
    if (!rootEl) return;
    if (loading) rootEl.classList.add('sm-loading');
    else rootEl.classList.remove('sm-loading');
  };

  async function submitRegister(e) {
    e.preventDefault();
    var body = {
      first_name: qs('#first_name').value,
      last_name: qs('#last_name').value,
      email: qs('#email').value,
      password: qs('#password').value,
      confirm_password: qs('#confirm_password').value,
    };
    var r = await window.apiPost('/register/', body);
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    window.smShowAlert('Registration successful. Please wait for admin approval before logging in.', 'success');
    window.location.href = '/ui/register/';
  }

  document.addEventListener('DOMContentLoaded', function () {
    var page = document.body.getAttribute('data-page');
    // if (page === 'admin_production') loadProduction();
    if (page === 'ui_register') {
      var fp = qs('#formRegister');
      if (fp) fp.addEventListener('submit', submitRegister);
    }
    // if (page === 'edit_production') {
    //   loadProductionEditForm();
    //   var fpe = qs('#formEditProduction');
    //   if (fpe) fpe.addEventListener('submit', submitEditProduction);
    // }
  });
})();
