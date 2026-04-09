/**
 * Admin UI — JSON from /admin/* routes (see views.py). Depends on api.js + common.js.
 */
(function () {
  'use strict';

  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }

  function escapeHtml(s) {
    var d = document.createElement('div');
    d.textContent = s == null ? '' : String(s);
    return d.innerHTML;
  }

  /** API returns ticker as string PK or nested; normalize to display string */
  function rowTicker(v) {
    if (v == null) return '';
    if (typeof v === 'object' && v.ticker) return v.ticker;
    return String(v);
  }

  async function loadAdminDashboard() {
    var ok = await window.requireAdminSession();
    if (!ok) return;
    var r = await window.apiGet('/admin/');
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    var d = r.data;
    var a = qs('#statCompanies');
    var b = qs('#statInvestors');
    var c = qs('#statPending');
    if (a) a.textContent = d.total_companies != null ? String(d.total_companies) : '—';
    if (b) b.textContent = d.total_investors != null ? String(d.total_investors) : '—';
    if (c) c.textContent = d.pending_approvals != null ? String(d.pending_approvals) : '—';
  }

  async function loadAdminCompanies() {
    var ok = await window.requireAdminSession();
    if (!ok) return;
    var r = await window.apiGet('/admin/companies/');
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    var rows = (r.data && r.data.companies) || [];
    var tbody = qs('#acTableBody');
    var empty = qs('#acEmpty');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (rows.length === 0) {
      if (empty) empty.classList.remove('d-none');
      return;
    }
    if (empty) empty.classList.add('d-none');
    rows.forEach(function (row) {
      var t = row.ticker;
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td>' +
        escapeHtml(t) +
        '</td><td>' +
        escapeHtml(row.company_name) +
        '</td><td class="text-end"><a class="btn btn-sm btn-outline-primary" href="/ui/admin/companies/' +
        encodeURIComponent(t) +
        '/edit/">Edit</a> <button type="button" class="btn btn-sm btn-outline-danger btn-ac-delete" data-ticker="' +
        escapeHtml(t) +
        '">Delete</button></td>';
      tbody.appendChild(tr);
    });
    tbody.querySelectorAll('.btn-ac-delete').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var ticker = btn.getAttribute('data-ticker');
        var modal = document.getElementById('modalDeleteCompany');
        if (modal) {
          modal.querySelector('.sm-delete-ticker').textContent = ticker;
          modal.dataset.ticker = ticker;
          new bootstrap.Modal(modal).show();
        }
      });
    });
  }

  async function confirmDeleteCompany() {
    var modal = document.getElementById('modalDeleteCompany');
    var ticker = modal && modal.dataset.ticker;
    if (!ticker) return;
    var r = await window.apiPost('/admin/companies/' + encodeURIComponent(ticker) + '/delete/', {});
    if (modal) bootstrap.Modal.getInstance(modal).hide();
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    window.smShowAlert(r.data.message || 'Deleted.', 'success');
    loadAdminCompanies();
  }

  async function submitAddCompany(e) {
    e.preventDefault();
    var form = qs('#formAddCompany');
    var body = {
      ticker: (qs('#acTicker') && qs('#acTicker').value) || '',
      company_name: (qs('#acName') && qs('#acName').value) || '',
    };
    var r = await window.apiPost('/admin/companies/add/', body);
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    window.smShowAlert('Company created.', 'success');
    window.location.href = '/ui/admin/companies/';
  }

  async function loadEditCompanyForm() {
    var ok = await window.requireAdminSession();
    if (!ok) return;
    var ticker = document.body.getAttribute('data-ticker');
    var r = await window.apiGet('/admin/companies/');
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    var rows = (r.data && r.data.companies) || [];
    var row = rows.find(function (c) {
      return c.ticker === ticker;
    });
    if (row && qs('#ecName')) qs('#ecName').value = row.company_name;
  }

  async function submitEditCompany(e) {
    e.preventDefault();
    var ticker = document.body.getAttribute('data-ticker');
    var body = { company_name: (qs('#ecName') && qs('#ecName').value) || '' };
    var r = await window.apiPost('/admin/companies/' + encodeURIComponent(ticker) + '/edit/', body);
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    window.smShowAlert('Company updated.', 'success');
    window.location.href = '/ui/admin/companies/';
  }

  async function loadInvestors() {
    var ok = await window.requireAdminSession();
    if (!ok) return;
    var r = await window.apiGet('/admin/investors/');
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    var rows = (r.data && r.data.investors) || [];
    var tbody = qs('#invTableBody');
    var empty = qs('#invEmpty');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (rows.length === 0) {
      if (empty) empty.classList.remove('d-none');
      return;
    }
    if (empty) empty.classList.add('d-none');
    rows.forEach(function (u) {
      var badge = u.is_active
        ? '<span class="badge rounded-pill bg-success">Active</span>'
        : '<span class="badge rounded-pill bg-secondary">Pending</span>';
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td>' +
        u.user_id +
        '</td><td>' +
        escapeHtml(u.first_name + ' ' + u.last_name) +
        '</td><td>' +
        escapeHtml(u.email) +
        '</td><td>' +
        badge +
        '</td><td><button type="button" class="btn btn-sm btn-success btn-inv-approve" data-id="' +
        u.user_id +
        '"' +
        (u.is_active ? ' disabled' : '') +
        '>Approve</button> <button type="button" class="btn btn-sm btn-warning text-white btn-inv-deact" data-id="' +
        u.user_id +
        '"' +
        (!u.is_active ? ' disabled' : '') +
        '>Deactivate</button> <button type="button" class="btn btn-sm btn-outline-danger btn-inv-del" data-id="' +
        u.user_id +
        '">Delete</button></td>';
      tbody.appendChild(tr);
    });
    tbody.querySelectorAll('.btn-inv-approve').forEach(function (b) {
      b.addEventListener('click', async function () {
        var id = b.getAttribute('data-id');
        var r = await window.apiPost('/admin/investors/' + id + '/approve/', {});
        if (!r.ok) window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
        else {
          window.smShowAlert(r.data.message || 'OK', 'success');
          loadInvestors();
        }
      });
    });
    tbody.querySelectorAll('.btn-inv-deact').forEach(function (b) {
      b.addEventListener('click', async function () {
        var id = b.getAttribute('data-id');
        var r = await window.apiPost('/admin/investors/' + id + '/deactivate/', {});
        if (!r.ok) window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
        else {
          window.smShowAlert(r.data.message || 'OK', 'success');
          loadInvestors();
        }
      });
    });
    tbody.querySelectorAll('.btn-inv-del').forEach(function (b) {
      b.addEventListener('click', async function () {
        if (!confirm('Delete this investor user?')) return;
        var id = b.getAttribute('data-id');
        var r = await window.apiPost('/admin/investors/' + id + '/delete/', {});
        if (!r.ok) window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
        else {
          window.smShowAlert(r.data.message || 'Deleted.', 'success');
          loadInvestors();
        }
      });
    });
  }

  async function loadFinmetrics() {
    var ok = await window.requireAdminSession();
    if (!ok) return;
    var r = await window.apiGet('/admin/finmetrics/');
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    var rows = (r.data && r.data.finmetrics) || [];
    var tbody = qs('#fmTableBody');
    var empty = qs('#fmEmpty');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (rows.length === 0) {
      if (empty) empty.classList.remove('d-none');
      return;
    }
    if (empty) empty.classList.add('d-none');
    rows.forEach(function (row) {
      var t = rowTicker(row.ticker);
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td>' +
        escapeHtml(t) +
        '</td><td>' +
        window.smNum(row.aisc, 2) +
        '</td><td>' +
        window.smNum(row.peg, 2) +
        '</td><td>' +
        window.smNum(row.total_debt, 2) +
        '</td><td>' +
        window.smNum(row.debt_to_equity, 2) +
        '</td><td>' +
        window.smNum(row.revenue, 2) +
        '</td><td>' +
        window.smNum(row.ebitda, 2) +
        '</td><td class="text-end"><a class="btn btn-sm btn-outline-primary" href="/ui/admin/finmetrics/' +
        encodeURIComponent(t) +
        '/edit/">Edit</a> <button type="button" class="btn btn-sm btn-outline-danger btn-fm-del" data-ticker="' +
        escapeHtml(t) +
        '">Delete</button></td>';
      tbody.appendChild(tr);
    });
    tbody.querySelectorAll('.btn-fm-del').forEach(function (btn) {
      btn.addEventListener('click', async function () {
        var ticker = btn.getAttribute('data-ticker');
        if (!confirm('Delete financial metrics for ' + ticker + '?')) return;
        var r = await window.apiPost('/admin/finmetrics/' + encodeURIComponent(ticker) + '/delete/', {});
        if (!r.ok) window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
        else {
          window.smShowAlert(r.data.message || 'Deleted.', 'success');
          loadFinmetrics();
        }
      });
    });
  }

  async function submitAddFinmetrics(e) {
    e.preventDefault();
    var body = {
      ticker: qs('#fmAddTicker').value,
      aisc: qs('#fmAddAisc').value,
      peg: qs('#fmAddPeg').value,
      total_debt: qs('#fmAddDebt').value,
      debt_to_equity: qs('#fmAddDe').value,
      revenue: qs('#fmAddRev').value,
      ebitda: qs('#fmAddEbitda').value,
    };
    var r = await window.apiPost('/admin/finmetrics/add/', body);
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    window.smShowAlert('Metrics added.', 'success');
    window.location.href = '/ui/admin/finmetrics/';
  }

  async function loadFinmetricsEditForm() {
    var ok = await window.requireAdminSession();
    if (!ok) return;
    var ticker = document.body.getAttribute('data-ticker');
    var r = await window.apiGet('/admin/finmetrics/');
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    var rows = (r.data && r.data.finmetrics) || [];
    var row = rows.find(function (x) {
      return rowTicker(x.ticker) === ticker;
    });
    if (!row) {
      window.smShowAlert('Metrics not found for ticker.', 'warning');
      return;
    }
    qs('#feAisc').value = row.aisc;
    qs('#fePeg').value = row.peg;
    qs('#feDebt').value = row.total_debt;
    qs('#feDe').value = row.debt_to_equity;
    qs('#feRev').value = row.revenue;
    qs('#feEbitda').value = row.ebitda;
  }

  async function submitEditFinmetrics(e) {
    e.preventDefault();
    var ticker = document.body.getAttribute('data-ticker');
    var body = {
      aisc: qs('#feAisc').value,
      peg: qs('#fePeg').value,
      total_debt: qs('#feDebt').value,
      debt_to_equity: qs('#feDe').value,
      revenue: qs('#feRev').value,
      ebitda: qs('#feEbitda').value,
    };
    var r = await window.apiPost('/admin/finmetrics/' + encodeURIComponent(ticker) + '/edit/', body);
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    window.smShowAlert('Metrics updated.', 'success');
    window.location.href = '/ui/admin/finmetrics/';
  }

  async function loadStockprices() {
    var ok = await window.requireAdminSession();
    if (!ok) return;
    var r = await window.apiGet('/admin/stockprices/');
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    var rows = (r.data && r.data.stockprices) || [];
    var tbody = qs('#spTableBody');
    var empty = qs('#spEmpty');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (rows.length === 0) {
      if (empty) empty.classList.remove('d-none');
      return;
    }
    if (empty) empty.classList.add('d-none');
    rows.forEach(function (row) {
      var t = rowTicker(row.ticker);
      var d = row.date_updated;
      var dStr = typeof d === 'string' ? d : d && d.toISOString ? d.toISOString().slice(0, 10) : String(d);
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td>' +
        escapeHtml(t) +
        '</td><td>' +
        escapeHtml(dStr) +
        '</td><td>' +
        window.smNum(row.previous_open, 2) +
        '</td><td>' +
        window.smNum(row.previous_close, 2) +
        '</td><td>' +
        window.smNum(row.fifty_two_week_high, 2) +
        '</td><td>' +
        window.smNum(row.fifty_two_week_low, 2) +
        '</td><td class="text-end"><a class="btn btn-sm btn-outline-primary" href="/ui/admin/stockprices/' +
        encodeURIComponent(t) +
        '/' +
        encodeURIComponent(dStr) +
        '/edit/">Edit</a> <button type="button" class="btn btn-sm btn-outline-danger btn-sp-del" data-ticker="' +
        escapeHtml(t) +
        '" data-date="' +
        escapeHtml(dStr) +
        '">Delete</button></td>';
      tbody.appendChild(tr);
    });
    tbody.querySelectorAll('.btn-sp-del').forEach(function (btn) {
      btn.addEventListener('click', async function () {
        var ticker = btn.getAttribute('data-ticker');
        var date = btn.getAttribute('data-date');
        if (!confirm('Delete this stock price row?')) return;
        var r = await window.apiPost(
          '/admin/stockprices/' + encodeURIComponent(ticker) + '/' + encodeURIComponent(date) + '/delete/',
          {}
        );
        if (!r.ok) window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
        else {
          window.smShowAlert(r.data.message || 'Deleted.', 'success');
          loadStockprices();
        }
      });
    });
  }

  async function submitAddStockprice(e) {
    e.preventDefault();
    var body = {
      ticker: qs('#spTicker').value,
      date_updated: qs('#spDate').value,
      previous_open: qs('#spOpen').value,
      previous_close: qs('#spClose').value,
      fifty_two_week_high: qs('#spHigh').value,
      fifty_two_week_low: qs('#spLow').value,
    };
    var r = await window.apiPost('/admin/stockprices/add/', body);
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    window.smShowAlert('Stock price added.', 'success');
    window.location.href = '/ui/admin/stockprices/';
  }

  async function loadStockpriceEditForm() {
    var ok = await window.requireAdminSession();
    if (!ok) return;
    var ticker = document.body.getAttribute('data-ticker');
    var date = document.body.getAttribute('data-date');
    var r = await window.apiGet('/admin/stockprices/');
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    var rows = (r.data && r.data.stockprices) || [];
    var row = rows.find(function (x) {
      var d = x.date_updated;
      var dStr = typeof d === 'string' ? d : d && d.toISOString ? d.toISOString().slice(0, 10) : String(d);
      return rowTicker(x.ticker) === ticker && dStr === date;
    });
    if (!row) {
      window.smShowAlert('Row not found.', 'warning');
      return;
    }
    qs('#seOpen').value = row.previous_open;
    qs('#seClose').value = row.previous_close;
    qs('#seHigh').value = row.fifty_two_week_high;
    qs('#seLow').value = row.fifty_two_week_low;
  }

  async function submitEditStockprice(e) {
    e.preventDefault();
    var ticker = document.body.getAttribute('data-ticker');
    var date = document.body.getAttribute('data-date');
    var body = {
      previous_open: qs('#seOpen').value,
      previous_close: qs('#seClose').value,
      fifty_two_week_high: qs('#seHigh').value,
      fifty_two_week_low: qs('#seLow').value,
    };
    var r = await window.apiPost(
      '/admin/stockprices/' + encodeURIComponent(ticker) + '/' + encodeURIComponent(date) + '/edit/',
      body
    );
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    window.smShowAlert('Stock price updated.', 'success');
    window.location.href = '/ui/admin/stockprices/';
  }

  async function loadProduction() {
    var ok = await window.requireAdminSession();
    if (!ok) return;
    var r = await window.apiGet('/admin/production/');
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    var rows = (r.data && r.data.productiondata) || [];
    var tbody = qs('#pdTableBody');
    var empty = qs('#pdEmpty');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (rows.length === 0) {
      if (empty) empty.classList.remove('d-none');
      return;
    }
    if (empty) empty.classList.add('d-none');
    rows.forEach(function (row) {
      var t = rowTicker(row.ticker);
      var p = row.period;
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td>' +
        escapeHtml(t) +
        '</td><td>' +
        escapeHtml(p) +
        '</td><td>' +
        window.smNum(row.silver_ounces_produced, 2) +
        '</td><td>' +
        escapeHtml(row.notes || '') +
        '</td><td class="text-end"><a class="btn btn-sm btn-outline-primary" href="/ui/admin/production/' +
        encodeURIComponent(t) +
        '/' +
        encodeURIComponent(p) +
        '/edit/">Edit</a> <button type="button" class="btn btn-sm btn-outline-danger btn-pd-del" data-ticker="' +
        escapeHtml(t) +
        '" data-period="' +
        escapeHtml(p) +
        '">Delete</button></td>';
      tbody.appendChild(tr);
    });
    tbody.querySelectorAll('.btn-pd-del').forEach(function (btn) {
      btn.addEventListener('click', async function () {
        var ticker = btn.getAttribute('data-ticker');
        var period = btn.getAttribute('data-period');
        if (!confirm('Delete this production row?')) return;
        var r = await window.apiPost(
          '/admin/production/' + encodeURIComponent(ticker) + '/' + encodeURIComponent(period) + '/delete/',
          {}
        );
        if (!r.ok) window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
        else {
          window.smShowAlert(r.data.message || 'Deleted.', 'success');
          loadProduction();
        }
      });
    });
  }

  async function submitAddProduction(e) {
    e.preventDefault();
    var body = {
      ticker: qs('#pdTicker').value,
      period: qs('#pdPeriod').value,
      silver_ounces_produced: qs('#pdOz').value,
      notes: qs('#pdNotes').value,
    };
    var r = await window.apiPost('/admin/production/add/', body);
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    window.smShowAlert('Production row added.', 'success');
    window.location.href = '/ui/admin/production/';
  }

  async function loadProductionEditForm() {
    var ok = await window.requireAdminSession();
    if (!ok) return;
    var ticker = document.body.getAttribute('data-ticker');
    var period = document.body.getAttribute('data-period');
    var r = await window.apiGet('/admin/production/');
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    var rows = (r.data && r.data.productiondata) || [];
    var row = rows.find(function (x) {
      return rowTicker(x.ticker) === ticker && x.period === period;
    });
    if (!row) {
      window.smShowAlert('Row not found.', 'warning');
      return;
    }
    qs('#peOz').value = row.silver_ounces_produced;
    qs('#peNotes').value = row.notes || '';
  }

  async function submitEditProduction(e) {
    e.preventDefault();
    var ticker = document.body.getAttribute('data-ticker');
    var period = document.body.getAttribute('data-period');
    var body = {
      silver_ounces_produced: qs('#peOz').value,
      notes: qs('#peNotes').value,
    };
    var r = await window.apiPost(
      '/admin/production/' + encodeURIComponent(ticker) + '/' + encodeURIComponent(period) + '/edit/',
      body
    );
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    window.smShowAlert('Production updated.', 'success');
    window.location.href = '/ui/admin/production/';
  }

  async function submitRegister(e) {
    e.preventDefault();
    var body = {
      first_name: qs('#fname').value,
      last_name: qs('#lname').value,
      email: qs('#rEmail').value,
      password: qs('#rPassword').value,
      confirm_password: qs('#rcPassword').value,
    };
    var r = await window.apiPost('/register/', body);
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    window.smShowAlert('Registration successful. Please wait for admin approval before logging in.', 'success');
  }

  async function submitLogin(e) {
    e.preventDefault();
    var body = {
      email: qs('#liEmail').value,
      password: qs('#liPassword').value,
    };
    var r = await window.apiPost('/login/', body);
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    window.smShowAlert('Logged in.', 'success');
    
    if (r.data && r.data.permission_level === 'Admin') {
      window.location.href = '/ui/admin/';
    } else {
      window.location.href = '/ui/dashboard/';
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (qs('#adminAccessDenied')) {
      window.requireAdminSession();
    }
    var page = document.body.getAttribute('data-page');
    if (page === 'admin_dashboard') loadAdminDashboard();
    if (page === 'admin_companies') {
      loadAdminCompanies();
      var m = qs('#modalDeleteCompany');
      if (m) {
        var btn = m.querySelector('.btn-confirm-delete');
        if (btn) btn.addEventListener('click', confirmDeleteCompany);
      }
    }
    if (page === 'add_company') {
      var f = qs('#formAddCompany');
      if (f) f.addEventListener('submit', submitAddCompany);
    }
    if (page === 'edit_company') {
      loadEditCompanyForm();
      var f2 = qs('#formEditCompany');
      if (f2) f2.addEventListener('submit', submitEditCompany);
    }
    if (page === 'admin_investors') loadInvestors();
    if (page === 'admin_finmetrics') loadFinmetrics();
    if (page === 'add_finmetrics') {
      var fa = qs('#formAddFinmetrics');
      if (fa) fa.addEventListener('submit', submitAddFinmetrics);
    }
    if (page === 'edit_finmetrics') {
      loadFinmetricsEditForm();
      var fe = qs('#formEditFinmetrics');
      if (fe) fe.addEventListener('submit', submitEditFinmetrics);
    }
    if (page === 'admin_stockprices') loadStockprices();
    if (page === 'add_stockprice') {
      var fs = qs('#formAddStockprice');
      if (fs) fs.addEventListener('submit', submitAddStockprice);
    }
    if (page === 'edit_stockprice') {
      loadStockpriceEditForm();
      var fse = qs('#formEditStockprice');
      if (fse) fse.addEventListener('submit', submitEditStockprice);
    }
    if (page === 'admin_production') loadProduction();
    if (page === 'add_production') {
      var fp = qs('#formAddProduction');
      if (fp) fp.addEventListener('submit', submitAddProduction);
    }
    if (page === 'edit_production') {
      loadProductionEditForm();
      var fpe = qs('#formEditProduction');
      if (fpe) fpe.addEventListener('submit', submitEditProduction);
    }
    if (page === 'ui_register') {
      var fr = qs('#formRegister');
      if (fr) fr.addEventListener('submit', submitRegister);
    }
    if (page === 'ui_login') {
      var fl = qs('#formLogIn');
      if (fl) fl.addEventListener('submit', submitLogin);
    }
  });
})();
