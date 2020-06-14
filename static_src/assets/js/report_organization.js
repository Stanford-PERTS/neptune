/* eslint-disable */

window.PERTS = (function(PERTS) {
  var EMPTY_INDICATOR = '&mdash;';
  var MIN_GOOD_PPN = 80;
  var MAX_BAD_PPN = 50;

  // Turn jQuery's deferreds into promises we can use like the real thing.
  function jPromise(callback) {
    var dfd = $.Deferred();
    var resolve = function(resolveValue) {
      dfd.resolve(resolveValue);
    };
    var reject = function(error) {
      dfd.reject(error);
    };
    callback(resolve, reject);
    return dfd.promise();
  }

  jPromise.all = function all(promises) {
    return jPromise(function(resolve, reject) {
      var values = promises instanceof Array ? [] : {};
      var numPromises = 0;
      var numResolved = 0;
      $.each(promises, function(i, p) {
        numPromises += 1;
        p.then(function(v) {
          values[i] = v;
          numResolved += 1;
          if (numResolved === numPromises) {
            resolve(values);
          }
        }).catch(function(error) {
          reject(error);
        });
      });
    });
  };

  function getNeptuneDomain(currentUrl) {
    var a = window.document.createElement('a');
    a.href = currentUrl;
    return a.origin;
  }

  function getTritonDomain(neptuneDomain) {
    if (neptuneDomain.indexOf('localhost') === -1) {
      return 'https://copilot.perts.net';
    }
    return 'http://localhost:10080';
  }

  function ajaxGet(url, token) {
    return $.ajax({
      method: 'GET',
      url: url,
      headers: token ? { Authorization: 'Bearer ' + token } : {},
      dataType: 'json',
    });
  }

  function loadOrg(token, tritonDomain, orgId) {
    var shortOrgId = orgId.replace('Organization_', '');
    var url = tritonDomain + '/api/organizations/' + shortOrgId;
    return ajaxGet(url, token);
  }

  function loadOrgReportData(token, tritonDomain, orgId) {
    var shortOrgId = orgId.replace('Organization_', '');
    var url =
      tritonDomain + '/api/organizations/' + shortOrgId + '/report_data';
    return ajaxGet(url, token);
  }

  function loadData(token, neptuneDomain, tritonDomain, orgId) {
    return jPromise.all({
      organization: loadOrg(token, tritonDomain, orgId),
      reportData: loadOrgReportData(token, tritonDomain, orgId),
    });
  }

  function getParticipationPct(team, cycle) {
    if (!(team.participation_base > 0)) {
      return null;
    }
    var pct = ((cycle.students_completed || 0) / team.participation_base) * 100;
    return Math.round(pct);
  }

  function getDisplayCycles(team, cycles) {
    var recent;
    var previous; // always before recent, if it exists

    // Sort all cycles into one of: past, present, or future.
    var pastCycles = [];
    var presentCycle;
    var futureCycles = [];
    var now = moment();
    cycles.forEach(function(c) {
      if (now.isAfter(c.end_date)) {
        pastCycles.push(c);
      } else if (now.isBefore(c.start_date)) {
        futureCycles.push(c);
      } else {
        if (presentCycle !== undefined) {
          console.error("Multiple 'present' cycles.");
          console.info(cycles);
        }
        presentCycle = c;
      }
    });

    recent = presentCycle
      ? presentCycle
      : // May be undefined, if all cycles are in the future.
        pastCycles[pastCycles.length - 1];

    // Gather stats of the current/recent cycle if there is one.
    if (recent) {
      // Days until the cycle ends.
      var diff = moment(recent.end_date).diff(now);
      recent.daysLeft = moment.duration(diff).days();

      // Participation.
      recent.ppnPct = getParticipationPct(team, recent);
      recent.ppnStr =
        recent.ppnPct === null ? 'empty roster' : recent.ppnPct + '%';
      recent.displayStatus =
        recent.ppnPct >= MAX_BAD_PPN
          ? recent.ppnPct >= MIN_GOOD_PPN
            ? 'good'
            : ''
          : 'bad';

      // Only do logic for the previous cycle if there's a recent one.
      if (recent.ordinal > 1) {
        // Find the previous cycle.
        previous = cycles.find(function(c) {
          return c.ordinal === recent.ordinal - 1;
        });

        // Gather stats of the previous cycle if there is one.
        if (previous) {
          // Participation.
          previous.ppnPct = getParticipationPct(team, previous);
          previous.ppnStr =
            previous.ppnPct === null ? 'empty roster' : previous.ppnPct + '%';
          previous.displayStatus =
            previous.ppnPct >= MAX_BAD_PPN
              ? previous.ppnPct >= MIN_GOOD_PPN
                ? 'good'
                : ''
              : 'bad';
        }
      }
    }

    return { current: recent, previous: previous };
  }

  function wrangleForTable(loaded) {
    var teams = loaded.reportData.teams.sort(function(a, b) {
      return a.name > b.name ? 1 : -1;
    });
    $.each(teams, function(i, team) {
      // Filter cycles to this team.
      var teamCycles = loaded.reportData.cycles.filter(function(c) {
        return c.team_id === team.uid;
      });

      var displayCycles = getDisplayCycles(team, teamCycles);

      team.currentCycle = displayCycles.current;
      team.previousCycle = displayCycles.previous;
    });

    loaded.reportData.teams = teams;

    return loaded;
  }

  function populateTable(loaded, tritonDomain) {
    var table = $('#participation-summary-table');

    $.each(loaded.reportData.teams, function(i, team) {
      var tr = $('<tr>');
      var teamUrl = tritonDomain + '/teams/' + team.short_uid + '/steps';
      var teamLink =
        '<a href="' + teamUrl + '" target="_blank">' + team.name + '</a>';
      tr.append(
        '<td>' +
          teamLink +
          '<br />' +
          team.num_users +
          ' <span class="member_term_plural"></span>' +
          '<br />' +
          team.num_classrooms +
          ' <span class="classroom_term_plural"></span>' +
          '</td>',
      );
      tr.append(
        '<td><div class="truncate">' +
          team.captain_name +
          '<br />' +
          '<a href="mailto:' +
          team.captain_email +
          '">' +
          team.captain_email +
          '</a></div></td>',
      );

      if (team.currentCycle) {
        $('<td>')
          .addClass(team.currentCycle.displayStatus)
          .html(team.currentCycle.ordinal)
          .appendTo(tr);
        $('<td>')
          .addClass(team.currentCycle.displayStatus)
          .html(team.currentCycle.daysLeft)
          .appendTo(tr);
        $('<td>')
          .addClass(team.currentCycle.displayStatus)
          .html(team.currentCycle.ppnStr)
          .appendTo(tr);
      } else {
        $('<td>' + EMPTY_INDICATOR + '</td>').appendTo(tr);
        $('<td>' + EMPTY_INDICATOR + '</td>').appendTo(tr);
        $('<td>' + EMPTY_INDICATOR + '</td>').appendTo(tr);
      }

      if (team.previousCycle) {
        $('<td>')
          .addClass(team.previousCycle.displayStatus)
          .html(team.previousCycle.ppnStr)
          .appendTo(tr);
      } else {
        $('<td>' + EMPTY_INDICATOR + '</td>').appendTo(tr);
      }

      $('tbody', table).append(tr);
    });

    // https://datatables.net/reference/option/
    table.DataTable({
      // https://datatables.net/reference/option/lengthMenu
      lengthMenu: [[50, 100, -1], [50, 100, 'All']],
    });

    return loaded;
  }

  function insertTerms(loaded) {
    var terms = ['team_term', 'captain_term', 'member_term', 'classroom_term'];

    terms.forEach(function(termKey) {
      var term = loaded.reportData.program[termKey];
      $('.' + termKey).html(term);

      var termPlural = term[term.length - 1] === 's' ? term + 'es' : term + 's';

      $('.' + termKey + '_plural').html(termPlural);
    });
  }

  PERTS.buildTable = function buildTable(location, orgId) {
    var parsedPath = '/organizations/([A-Za-z0-9_-]+)/';
    var parsedQs = /token=([^&]+)/.exec(location.search);
    var token = parsedQs ? parsedQs[1] : null;
    var nep = getNeptuneDomain(location.href);
    var tri = getTritonDomain(nep);
    return loadData(token, nep, tri, orgId)
      .then(wrangleForTable)
      .then(function(loaded) {
        return populateTable(loaded, tri);
      })
      .then(insertTerms)
      .then(function() {
        $('.empty-indicator').html(EMPTY_INDICATOR);
        $('.min-good-ppn').html(MIN_GOOD_PPN);
      });
  };

  return PERTS;
})(window.PERTS || {});
