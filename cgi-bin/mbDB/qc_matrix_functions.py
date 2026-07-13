#!./cgi_runner.sh

# Builds the QC Status Matrix: every board x every test type, where a test counts as
# passed if the board cleared it at least once, failed only if every attempt failed, and
# not-yet-run if it was never tried. ECON / LDO chip IDs come from the photograph station
# (Board_component); the lpGBT ID is recovered from each board's most recent test-data
# attachment (same source used by get_sn_from_lpgbt_id).

import html
from connect import connect

db = connect(0)
cur = db.cursor(buffered=True)

# glyph, css class, and legend tooltip for each cell state
GLYPH = {
    'pass':    ('✓', 'pass',    'Passed (passed at least once)'),
    'fail':    ('✕', 'fail',    'Failed every attempt'),
    'missing': ('○', 'missing', 'Never run (but in this board type’s test set)'),
    'na':      ('·', 'na',      'Not part of this board type’s test set'),
}


def _gather():
    # test types in stand order
    cur.execute('select test_type, name, relative_order from Test_Type order by relative_order')
    test_types = [{'id': r[0], 'name': r[1], 'order': r[2]} for r in cur.fetchall()]

    # boards, joined to their board type for the subtype nickname + stitch key
    cur.execute('''select B.full_id, B.board_id, B.type_id, BT.name, BT.type_id
                   from Board B join Board_type BT on B.type_id=BT.type_sn''')
    boards = {}
    for full_id, board_id, type_sn, nickname, bt_type_id in cur.fetchall():
        boards[board_id] = {'full_id': full_id, 'board_id': board_id, 'subtype': type_sn,
                            'nickname': nickname, 'bt_type_id': bt_type_id,
                            'econ': {}, 'ldo': {}, 'lpgbt': None, 'status': {}}

    # which tests apply to which board type
    cur.execute('select type_id, test_type_id from Type_test_stitch')
    stitch = {}
    for type_id, tt in cur.fetchall():
        stitch.setdefault(type_id, set()).add(tt)

    # full test history -> ever-passed / ever-attempted per (board, test type)
    cur.execute('select board_id, test_type_id, successful from Test')
    agg = {}
    for board_id, tt, successful in cur.fetchall():
        d = agg.setdefault((board_id, tt), {'pass': False, 'any': False})
        d['any'] = True
        if successful == 1:
            d['pass'] = True

    # ECON / LDO serials scanned at the photograph station
    cur.execute('select board_id, ref_designator, kind, child_serial from Board_component')
    for board_id, ref, kind, serial in cur.fetchall():
        b = boards.get(board_id)
        if not b:
            continue
        if kind == 'IC-ECT':
            b['econ'][ref] = serial
        elif kind == 'IC-LDO':
            b['ldo'][ref] = serial

    # lpGBT id: most recent test-data attachment carrying $.test_data.DAQ.id
    cur.execute('''select T.board_id, JSON_EXTRACT(A.attach, '$.test_data.DAQ.id')
                   from Test T join Attachments A on T.test_id=A.test_id
                   where JSON_EXTRACT(A.attach, '$.test_data.DAQ.id') is not null
                   order by T.board_id, T.test_id desc''')
    for board_id, lpid in cur.fetchall():
        b = boards.get(board_id)
        if b is None or b['lpgbt'] is not None or lpid is None:
            continue
        v = lpid.decode() if isinstance(lpid, (bytes, bytearray)) else str(lpid)
        b['lpgbt'] = v.strip().strip('"')

    # resolve each cell's state
    for bid, b in boards.items():
        appl = stitch.get(b['bt_type_id'], set())
        for t in test_types:
            tt = t['id']
            d = agg.get((bid, tt))
            if d is None:
                b['status'][tt] = 'missing' if tt in appl else 'na'
            elif d['pass']:
                b['status'][tt] = 'pass'
            elif d['any']:
                b['status'][tt] = 'fail'
            else:
                b['status'][tt] = 'missing'

    board_list = sorted(boards.values(), key=lambda x: (x['subtype'], x['full_id']))
    return test_types, board_list


def _fmt_lpgbt(v):
    if not v:
        return '<span class="none">—</span>'
    try:
        hx = '0x%08X' % int(v)
        return '<span class="serial" title="decimal %s">%s</span>' % (html.escape(v), hx)
    except (ValueError, TypeError):
        return '<span class="serial">%s</span>' % html.escape(v)


def _chip_cell(dm):
    if not dm:
        return '<span class="none">—</span>'
    out = ['<div class="serials">']
    for ref in sorted(dm.keys()):
        out.append('<span class="serial" title="%s">%s</span>'
                   % (html.escape(ref), html.escape(dm[ref])))
    out.append('</div>')
    return ''.join(out)


STYLE = '''
<style>
.qcm{--pass:#1f9d57;--pass-bg:#e6f4ec;--fail:#d1435b;--fail-bg:#fbe7ec;
  --miss:#aab2c0;--miss-ring:#c2c9d6;--na:#ccd3de;--accent:#2f6db0;--accent-soft:#e7f0f9;
  --ink:#1a2230;--ink-soft:#586374;--ink-faint:#8a94a4;--border:#dde2ea;--border-strong:#c6ccd8;
  --surface:#fff;--surface-2:#f7f9fb;
  --mono:ui-monospace,"SF Mono","Cascadia Code",Menlo,Consolas,monospace;
  color:var(--ink);margin-bottom:2rem}
.qcm h2{font-size:1.6rem;margin:0 0 .35rem;letter-spacing:-.01em}
.qcm .lede{color:var(--ink-soft);max-width:80ch;margin:0 0 1rem;font-size:.95rem}
.qcm .lede strong{color:var(--ink)}
.qcm-stats{display:flex;flex-wrap:wrap;gap:.6rem;margin:1rem 0}
.qcm-stat{background:var(--surface);border:1px solid var(--border);border-radius:9px;padding:.5rem .9rem;min-width:96px}
.qcm-stat .num{font-size:1.35rem;font-weight:650;font-variant-numeric:tabular-nums;line-height:1}
.qcm-stat .lbl{font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-soft);margin-top:.28rem}
.qcm-stat.p .num{color:var(--pass)} .qcm-stat.f .num{color:var(--fail)} .qcm-stat.m .num{color:var(--ink-soft)}
.qcm-legend{display:flex;flex-wrap:wrap;gap:1.1rem;align-items:center;margin:.3rem 0 1rem;font-size:.83rem;color:var(--ink-soft)}
.qcm-legend .item{display:inline-flex;align-items:center;gap:.4rem}
.qcm .gl{width:1.35em;height:1.35em;display:inline-grid;place-items:center;border-radius:5px;font-weight:700}
.qcm .gl.pass{color:var(--pass);background:var(--pass-bg)}
.qcm .gl.fail{color:var(--fail);background:var(--fail-bg)}
.qcm .gl.missing{color:var(--miss);border:1px solid var(--miss-ring)}
.qcm .gl.na{color:var(--na)}
.qcm-wrap{overflow-x:auto;border:1px solid var(--border);border-radius:11px;background:var(--surface)}
.qcm table{border-collapse:separate;border-spacing:0;font-variant-numeric:tabular-nums;width:100%;margin:0}
.qcm thead th{position:sticky;top:0;z-index:5;background:var(--surface-2);border-bottom:2px solid var(--border-strong)}
.qcm th.corner{position:sticky;left:0;z-index:7;text-align:left;padding:.5rem .8rem;background:var(--surface-2);
  border-right:2px solid var(--border-strong);min-width:168px;font-size:.72rem;letter-spacing:.05em;
  text-transform:uppercase;color:var(--ink-soft);vertical-align:bottom}
.qcm th.chiph,.qcm th.progh{background:var(--surface-2);font-size:.66rem;letter-spacing:.05em;text-transform:uppercase;
  color:var(--ink-soft);padding:.5rem .55rem;vertical-align:bottom;border-right:1px solid var(--border);white-space:nowrap}
.qcm th.tcol{padding:.35rem .1rem .5rem;border-right:1px solid var(--border);min-width:2.15rem}
.qcm .vhead{writing-mode:vertical-rl;transform:rotate(180deg);display:inline-flex;align-items:center;gap:.4rem;
  height:8.7rem;margin:0 auto;font-size:.76rem}
.qcm .vhead .tname{font-weight:550;color:var(--ink)}
.qcm .vhead .ord{color:var(--ink-faint);font-size:.68rem}
.qcm tbody th.idcell{position:sticky;left:0;z-index:3;background:var(--surface);border-right:2px solid var(--border-strong);
  text-align:left;padding:.4rem .8rem;font-family:var(--mono);font-size:.78rem;font-weight:500;white-space:nowrap}
.qcm tbody tr:hover th.idcell{background:var(--accent-soft)}
.qcm tbody th.idcell a{color:var(--ink);text-decoration:none}
.qcm tbody th.idcell a:hover{text-decoration:underline;color:var(--accent)}
.qcm td,.qcm tbody th{border-bottom:1px solid var(--border)}
.qcm td.chip{padding:.3rem .55rem;border-right:1px solid var(--border);vertical-align:middle}
.qcm td.chip.lpgbt{border-right:2px solid var(--border-strong)}
.qcm .serials{display:flex;flex-direction:column;gap:.12rem}
.qcm .serial{font-family:var(--mono);font-size:.72rem;color:var(--ink);white-space:nowrap}
.qcm .none{color:var(--ink-faint)}
.qcm td.prog{padding:.3rem .55rem;border-right:2px solid var(--border-strong);min-width:82px;white-space:nowrap}
.qcm .bar{height:5px;border-radius:3px;background:var(--border);overflow:hidden;margin-bottom:.2rem}
.qcm .bar span{display:block;height:100%;background:var(--pass);border-radius:3px}
.qcm .pnum{font-size:.72rem;color:var(--ink-soft)}
.qcm td.cell{text-align:center;font-weight:700;font-size:.95rem;border-right:1px solid var(--border);padding:.2rem 0;cursor:default}
.qcm td.cell.pass{color:var(--pass);background:var(--pass-bg)}
.qcm td.cell.fail{color:var(--fail);background:var(--fail-bg)}
.qcm td.cell.missing{color:var(--miss)}
.qcm td.cell.na{color:var(--na)}
.qcm tbody tr:hover td{background:var(--surface-2)}
.qcm tbody tr:hover td.cell.pass{background:var(--pass-bg)}
.qcm tbody tr:hover td.cell.fail{background:var(--fail-bg)}
.qcm tr.band th{position:sticky;left:0;background:var(--accent-soft);border-top:1px solid var(--border-strong);
  border-bottom:1px solid var(--border-strong);text-align:left;padding:.45rem .8rem;z-index:4}
.qcm .bname{font-weight:650;font-size:.9rem;color:var(--ink)}
.qcm .bsub{font-family:var(--mono);font-size:.74rem;color:var(--accent);margin-left:.6rem}
.qcm .bcount{float:right;font-size:.76rem;color:var(--ink-soft)}
</style>
'''


def render_matrix():
    test_types, boards = _gather()

    tally = {'pass': 0, 'fail': 0, 'missing': 0, 'na': 0}
    for b in boards:
        for v in b['status'].values():
            tally[v] = tally.get(v, 0) + 1
    n_scanned = sum(1 for b in boards if b['econ'] or b['ldo'])
    n_lpgbt = sum(1 for b in boards if b['lpgbt'])

    # group boards by (subtype, nickname); biggest groups first
    groups = {}
    for b in boards:
        groups.setdefault((b['subtype'], b['nickname']), []).append(b)
    gkeys = sorted(groups.keys(), key=lambda k: (-len(groups[k]), k[0]))
    span = 5 + len(test_types)  # id + econ + ldo + lpgbt + prog + one per test

    print(STYLE)
    print('<div class="qcm">')
    print('<div class="row"><div class="col-md-12 pt-3 ps-5 pe-5 mx-2">')

    print('<h2>QC Status Matrix</h2>')
    print('<p class="lede">Every board and every test on the stand. A test counts as '
          '<strong>passed</strong> if the board cleared it at least once, '
          '<strong>failed</strong> only if every attempt failed, and '
          '<strong>not&nbsp;yet&nbsp;run</strong> if it was never tried. ECON, LDO and '
          'lpGBT IDs are shown where recorded.</p>')

    print('<div class="qcm-stats">')
    print('<div class="qcm-stat"><div class="num">%d</div><div class="lbl">Boards</div></div>' % len(boards))
    print('<div class="qcm-stat p"><div class="num">%d</div><div class="lbl">Passed</div></div>' % tally['pass'])
    print('<div class="qcm-stat f"><div class="num">%d</div><div class="lbl">Failed (all attempts)</div></div>' % tally['fail'])
    print('<div class="qcm-stat m"><div class="num">%d</div><div class="lbl">Not yet run</div></div>' % tally['missing'])
    print('<div class="qcm-stat"><div class="num">%d</div><div class="lbl">Chip-scanned</div></div>' % n_scanned)
    print('<div class="qcm-stat"><div class="num">%d</div><div class="lbl">lpGBT IDs</div></div>' % n_lpgbt)
    print('</div>')

    print('<div class="qcm-legend">')
    print('<span class="item"><span class="gl pass">✓</span> passed (ever)</span>')
    print('<span class="item"><span class="gl fail">✕</span> failed every attempt</span>')
    print('<span class="item"><span class="gl missing">○</span> not yet run</span>')
    print('<span class="item"><span class="gl na">·</span> not in this board type’s test set</span>')
    print('</div>')

    print('<div class="qcm-wrap"><table>')
    print('<thead><tr>')
    print('<th class="corner">Board / Full ID</th>')
    print('<th class="chiph">ECON IDs<br><span style="font-weight:400;text-transform:none">U251_T1 / _T2</span></th>')
    print('<th class="chiph">LDO IDs<br><span style="font-weight:400;text-transform:none">U661 / U681</span></th>')
    print('<th class="chiph">lpGBT ID</th>')
    print('<th class="progh">Passed</th>')
    for t in test_types:
        print('<th class="tcol" title="%s"><div class="vhead"><span class="ord">%s</span>'
              '<span class="tname">%s</span></div></th>'
              % (html.escape(t['name']), t['order'], html.escape(t['name'])))
    print('</tr></thead><tbody>')

    for (subtype, nickname) in gkeys:
        grp = groups[(subtype, nickname)]
        print('<tr class="band"><th colspan="%d"><span class="bname">%s</span>'
              '<span class="bsub">%s</span><span class="bcount">%d board%s</span></th></tr>'
              % (span, html.escape(nickname), html.escape(subtype),
                 len(grp), '' if len(grp) == 1 else 's'))
        for b in grp:
            appl = sum(1 for t in test_types if b['status'].get(t['id']) != 'na')
            passed = sum(1 for t in test_types if b['status'].get(t['id']) == 'pass')
            pct = (100 * passed // appl) if appl else 0
            print('<tr>')
            print('<th class="idcell"><a href="module.py?full_id=%s" target="_blank" title="%s">%s</a></th>'
                  % (html.escape(b['full_id']), html.escape(b['full_id']), html.escape(b['full_id'])))
            print('<td class="chip">%s</td>' % _chip_cell(b['econ']))
            print('<td class="chip">%s</td>' % _chip_cell(b['ldo']))
            print('<td class="chip lpgbt">%s</td>' % _fmt_lpgbt(b['lpgbt']))
            print('<td class="prog"><div class="bar"><span style="width:%d%%"></span></div>'
                  '<span class="pnum">%d/%d</span></td>' % (pct, passed, appl))
            for t in test_types:
                st = b['status'].get(t['id'], 'na')
                g, cls, tip = GLYPH[st]
                print('<td class="cell %s" title="%s — %s">%s</td>'
                      % (cls, html.escape(t['name']), html.escape(tip), g))
            print('</tr>')
    print('</tbody></table></div>')

    print('<p class="lede" style="margin-top:1rem;font-size:.82rem;color:var(--ink-faint)">'
          'Ordering follows each test’s relative order on the stand (number above the label). '
          '&ldquo;Not in this board type’s test set&rdquo; (from <code>Type_test_stitch</code>) '
          'is distinct from an applicable test that simply hasn’t been run yet. lpGBT IDs are '
          'read from the most recent test-data attachment; ECON / LDO serials come from the '
          'photograph station (<code>Board_component</code>). Pass/fail reflects the full test '
          'history, not only the latest attempt.</p>')

    print('</div></div></div>')
