/**
 * Investor UI — loads JSON from /dashboard/, /companies/, /favourites/ (see views.py).
 */
(function () {
  'use strict';

  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }

  function buildCompanyListQuery() {
    var params = new URLSearchParams();
    var search = (qs('#filterSearch') && qs('#filterSearch').value) || '';
    var maxAisc = qs('#filterMaxAisc') && qs('#filterMaxAisc').value;
    var maxDe = qs('#filterMaxDe') && qs('#filterMaxDe').value;
    var maxPeg = qs('#filterMaxPeg') && qs('#filterMaxPeg').value;
    if (search.trim()) params.set('search', search.trim());
    if (maxAisc) params.set('max_aisc', maxAisc);
    if (maxDe) params.set('max_debt_equity', maxDe);
    if (maxPeg) params.set('max_peg', maxPeg);
    var s = params.toString();
    return s ? '?' + s : '';
  }

  async function loadInvestorDashboard() {
    await window.requireInvestorSession();
  }

  async function loadRankedCompanies() {
    var root = qs('#rankedRoot');
    var ok = await window.requireInvestorSession();
    if (!ok) return;
    if (root) window.smSetLoading(root, true);
    var url = '/companies/' + buildCompanyListQuery();
    var r = await window.apiGet(url);
    if (root) window.smSetLoading(root, false);
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    if (r.data.errors) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'warning');
    }
    var companies = (r.data && r.data.companies) || [];
    var tbody = qs('#companiesTableBody');
    var empty = qs('#rankedEmpty');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (companies.length === 0) {
      if (empty) empty.classList.remove('d-none');
      return;
    }
    if (empty) empty.classList.add('d-none');
    companies.forEach(function (c) {
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td><a href="/ui/companies/' +
        encodeURIComponent(c.ticker) +
        '/">' +
        escapeHtml(c.ticker) +
        '</a></td>' +
        '<td>' +
        escapeHtml(c.company_name) +
        '</td>' +
        '<td>' +
        escapeHtml(String(c.rank_position)) +
        '</td>' +
        '<td>' +
        window.smNum(c.score, 2) +
        '</td>';
      tbody.appendChild(tr);
    });
  }

  function escapeHtml(s) {
    var d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  async function loadCompanyDetails() {
    var ticker = document.body.getAttribute('data-ticker');
    if (!ticker) return;
    var ok = await window.requireInvestorSession();
    if (!ok) return;
    var r = await window.apiGet('/companies/' + encodeURIComponent(ticker) + '/');
    if (r.status === 404) {
      window.smShowAlert('Company not found.', 'warning');
      return;
    }
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    var d = r.data;
    var tEl = qs('#cdTitle');
    var tkEl = qs('#cdTicker');
    if (tEl) tEl.textContent = d.company_name || '';
    if (tkEl) tkEl.textContent = d.ticker || '';
    var rank = d.ranking;
    var rkEl = qs('#cdRank');
    var scEl = qs('#cdScore');
    if (rkEl) rkEl.textContent = rank ? String(rank.rank_position) : '—';
    if (scEl) scEl.textContent = rank ? window.smNum(rank.score, 2) : '—';

    var fm = d.fin_metrics;
    var fmBody = qs('#cdFinBody');
    if (fmBody) {
      fmBody.innerHTML = '';
      if (!fm) {
        fmBody.innerHTML = '<tr><td colspan="2" class="text-body-secondary">No financial metrics.</td></tr>';
      } else {
        [['AISC', fm.aisc], ['PEG', fm.peg], ['Total debt', fm.total_debt], ['D/E', fm.debt_to_equity], ['Revenue', fm.revenue], ['EBITDA', fm.ebitda]].forEach(function (row) {
          var tr = document.createElement('tr');
          tr.innerHTML = '<th>' + row[0] + '</th><td>' + window.smNum(row[1], 2) + '</td>';
          fmBody.appendChild(tr);
        });
      }
    }

    var sp = d.stock_prices || [];
    var spBody = qs('#cdStockBody');
    if (spBody) {
      spBody.innerHTML = '';
      if (sp.length === 0) {
        spBody.innerHTML = '<tr><td colspan="5" class="text-body-secondary">No stock price rows.</td></tr>';
      } else {
        sp.forEach(function (row) {
          var tr = document.createElement('tr');
          tr.innerHTML =
            '<td>' +
            escapeHtml(row.date_updated) +
            '</td><td>' +
            window.smNum(row.previous_open, 2) +
            '</td><td>' +
            window.smNum(row.previous_close, 2) +
            '</td><td>' +
            window.smNum(row.fifty_two_week_high, 2) +
            '</td><td>' +
            window.smNum(row.fifty_two_week_low, 2) +
            '</td>';
          spBody.appendChild(tr);
        });
      }
    }

    var pr = d.production_data || [];
    var prBody = qs('#cdProdBody');
    if (prBody) {
      prBody.innerHTML = '';
      if (pr.length === 0) {
        prBody.innerHTML = '<tr><td colspan="3" class="text-body-secondary">No production data.</td></tr>';
      } else {
        pr.forEach(function (row) {
          var tr = document.createElement('tr');
          tr.innerHTML =
            '<td>' +
            escapeHtml(row.period) +
            '</td><td>' +
            window.smNum(row.silver_ounces_produced, 2) +
            '</td><td>' +
            escapeHtml(row.notes || '') +
            '</td>';
          prBody.appendChild(tr);
        });
      }
    }

    var favBtn = qs('#btnFavourite');
    if (favBtn) {
      favBtn.dataset.fav = d.is_favourite ? '1' : '0';
      favBtn.textContent = d.is_favourite ? 'Remove from favourites' : 'Add to favourites';
    }
  }

  async function toggleFavourite() {
    var ticker = document.body.getAttribute('data-ticker');
    if (!ticker) return;
    var r = await window.apiPost('/companies/' + encodeURIComponent(ticker) + '/favourite/', {});
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    window.smShowAlert(r.data.message || 'Updated.', 'success');
    var favBtn = qs('#btnFavourite');
    if (favBtn && r.data) {
      favBtn.dataset.fav = r.data.is_favourite ? '1' : '0';
      favBtn.textContent = r.data.is_favourite ? 'Remove from favourites' : 'Add to favourites';
    }
  }

  async function loadFavourites() {
    var ok = await window.requireInvestorSession();
    if (!ok) return;
    var r = await window.apiGet('/favourites/');
    if (!r.ok) {
      window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
      return;
    }
    var rows = (r.data && r.data.favourites) || [];
    var tbody = qs('#favTableBody');
    var empty = qs('#favEmpty');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (rows.length === 0) {
      if (empty) empty.classList.remove('d-none');
      return;
    }
    if (empty) empty.classList.add('d-none');
    rows.forEach(function (f) {
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td>' +
        escapeHtml(f.ticker) +
        '</td><td>' +
        escapeHtml(f.company_name) +
        '</td><td>' +
        escapeHtml(f.date_favourited) +
        '</td><td><a class="btn btn-sm btn-outline-primary" href="/ui/companies/' +
        encodeURIComponent(f.ticker) +
        '/">View</a></td>' +
        '<td><button type="button" class="btn btn-sm btn-outline-danger btn-fav-remove" data-ticker="' +
        escapeHtml(f.ticker) + '" data-name="' + escapeHtml(f.company_name) + '">Remove</button></td>';
      tbody.appendChild(tr);
    });
    tbody.querySelectorAll('.btn-fav-remove').forEach(function (btn) {
      btn.addEventListener('click', async function () {
        var ticker = btn.getAttribute('data-ticker');
        var name = btn.getAttribute('data-name');
        var r = await window.apiPost('/companies/' + encodeURIComponent(ticker) + '/favourite/', {});
        if (!r.ok) {
          window.smShowAlert(window.smFormatApiErrors(r.data), 'danger');
          return;
        }
        window.smShowAlert((name || ticker) + ' removed from favourites.', 'success');
        loadFavourites();
      });
    });
  }

  function bindRankedFilters() {
    var form = qs('#rankedFilters');
    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        loadRankedCompanies();
      });
    }
    var reset = qs('#btnResetFilters');
    if (reset) {
      reset.addEventListener('click', function () {
        ['#filterSearch', '#filterMaxAisc', '#filterMaxDe', '#filterMaxPeg'].forEach(function (id) {
          var el = qs(id);
          if (el) el.value = '';
        });
        loadRankedCompanies();
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    var page = document.body.getAttribute('data-page');
    if (page === 'investor_dashboard') loadInvestorDashboard();
    if (page === 'ranked_companies') {
      bindRankedFilters();
      loadRankedCompanies();
    }
    if (page === 'company_details') {
      loadCompanyDetails();
      var favBtn = qs('#btnFavourite');
      if (favBtn) favBtn.addEventListener('click', toggleFavourite);
    }
    if (page === 'favourites') loadFavourites();
  });
})();
