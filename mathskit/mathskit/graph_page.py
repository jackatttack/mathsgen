"""How a graph looks and behaves on a page: HTML, CSS and the page script.

html(graph) is what blocks.graph() returns. The page script finds each
.mk-graph as it appears, compiles its curves (JavaScript from graph.py)
and draws them on a canvas in the theme's colours: grid at nice steps,
axes, tick labels, then curves, broken where they jump (1/x).

Touch, all in the page:
    slider          redraws as it moves
    tap             traces the first full curve: a dot and (x, y)
    one finger      drags the graph around inside its box (past TAP_SLOP;
                    less is a tap)
    two fingers     zoom and pan the graph only: the page's own pinch is
                    stopped before it sees the gesture (window, capture
                    phase; editorkit's Cards pinch listens later, on
                    document). The point under the fingers stays put.
    Reset view      shows once the view has moved; puts it back
A finger that starts on a graph moves the graph, so scroll the page from
outside one. Redraws wait for the next frame.

typeset.page_extras() carries CSS and SCRIPT. Pure Python.
"""
import json

from .blocks import escape

TRACE_HINT = 'Drag to move \u00b7 pinch to zoom \u00b7 tap to trace'
RESET_LABEL = 'Reset view'


def html(figure):
    spec = json.dumps(figure.spec())
    title = '<div class="mk-gtitle">%s</div>' % escape(figure.title) if figure.title else ''
    keys = ''.join('<span class="mk-key%s"><i></i><span class="mk-inline" data-tex="%s">%s</span>'
                   '</span>' % (' mk-faint' if curve.faint else '', escape('y = ' + curve.tex),
                                escape('y = ' + curve.text))
                   for curve in figure.curves)
    sliders = ''.join(slider_html(slider) for slider in figure.sliders)
    return ('<div class="mk-graph" data-graph="%s">%s<canvas class="mk-canvas"></canvas>'
            '<div class="mk-gbar"><div class="mk-readout">%s</div>'
            '<span class="mk-reset" data-graph-reset="1">%s</span></div>'
            '<div class="mk-legend">%s</div><div class="mk-sliders">%s</div></div>'
            % (escape(spec), title, escape(TRACE_HINT), escape(RESET_LABEL), keys, sliders))


def slider_html(slider):
    return ('<label class="mk-slider"><span class="mk-sname">%s</span>'
            '<input type="range" min="%g" max="%g" step="%g" value="%g" data-name="%s">'
            '<span class="mk-svalue">%g</span></label>'
            % (escape(slider.name), slider.low, slider.high, slider.step, slider.value,
               escape(slider.name), slider.value))


CSS = """
.mk-graph { margin: 0.6em 0 1.4em; }
.mk-gtitle { font: 600 14px -apple-system, sans-serif; margin-bottom: 6px; }
.mk-canvas { display: block; width: 100%; border-radius: 12px; background: var(--wash);
    touch-action: none; }
.mk-gbar { display: flex; align-items: center; gap: 10px; margin-top: 5px; min-height: 26px; }
.mk-readout { flex: 1; min-width: 0; font: 12px/1.4 Menlo, monospace; color: var(--muted); }
.mk-reset { display: none; padding: 3px 10px; border-radius: 8px; background: var(--wash-strong);
    font: 12px -apple-system, sans-serif; cursor: pointer; -webkit-user-select: none;
    user-select: none; }
.mk-graph.mk-zoomed .mk-reset { display: inline-block; }
.mk-legend { display: flex; flex-wrap: wrap; gap: 4px 16px; margin-top: 2px; }
.mk-key { display: inline-flex; align-items: center; gap: 7px; font-size: 15px; }
.mk-key i { display: inline-block; width: 16px; height: 3px; border-radius: 2px;
    background: var(--accent); }
.mk-key.mk-faint { opacity: 0.6; }
.mk-sliders { display: grid; gap: 4px; margin-top: 8px; }
.mk-slider { display: flex; align-items: center; gap: 10px; }
.mk-sname { font: italic 18px KaTeX_Math, serif; width: 1.2em; text-align: center; }
.mk-slider input { flex: 1; min-width: 0; height: 30px; accent-color: var(--accent); }
.mk-svalue { font: 13px Menlo, monospace; min-width: 3.5em; text-align: right; }
"""

SCRIPT = r"""
(function () {
  var CURVE_COLOURS = ['#5AC8FA', '#62D26F', '#FF9F43', '#BF5AF2'];   // after the accent
  var SMALLEST_SPAN = 1e-3, LARGEST_SPAN = 1e6;                       // how far a pinch goes
  var TAP_SLOP = 10;                                                  // px a tap may drift

  function cssVar(element, name, fallback) {
    var value = getComputedStyle(element).getPropertyValue(name);
    return value && value.trim() ? value.trim() : fallback;
  }

  function curveColour(box, index) {
    var curve = box.mkSpec.curves[index];
    if (curve.faint) { return cssVar(box, '--muted', '#888888'); }
    var full = 0;
    for (var i = 0; i < index; i++) { if (!box.mkSpec.curves[i].faint) { full += 1; } }
    return full === 0 ? cssVar(box, '--accent', '#FF2D55')
                      : CURVE_COLOURS[(full - 1) % CURVE_COLOURS.length];
  }

  function niceStep(span, lines) {
    var raw = span / Math.max(1, lines);
    var power = Math.pow(10, Math.floor(Math.log(raw) / Math.LN10));
    var unit = raw / power;
    return (unit < 1.5 ? 1 : unit < 3.5 ? 2 : unit < 7.5 ? 5 : 10) * power;
  }

  function tickText(value, step) {
    var digits = Math.max(0, -Math.floor(Math.log(step) / Math.LN10));
    return String(Number(value.toFixed(digits)));
  }

  function shortNumber(value) {
    return Math.abs(value) >= 1000 ? value.toFixed(0) : String(Number(value.toFixed(2)));
  }

  function evaluate(box, curve, x) {
    if (!curve.fn) { return null; }
    var values = [x];
    var sliders = box.mkSpec.sliders;
    for (var i = 0; i < sliders.length; i++) { values.push(box.mkValues[sliders[i].name]); }
    try {
      var y = curve.fn.apply(null, values);
      return (typeof y === 'number' && isFinite(y)) ? y : null;
    } catch (error) { return null; }
  }

  function autoY(box) {
    var spec = box.mkSpec;
    var found = [];
    for (var c = 0; c < spec.curves.length; c++) {
      for (var i = 0; i <= 240; i++) {
        var y = evaluate(box, spec.curves[c], spec.x[0] + (spec.x[1] - spec.x[0]) * i / 240);
        if (y !== null) { found.push(y); }
      }
    }
    if (!found.length) { return [-5, 5]; }
    found.sort(function (a, b) { return a - b; });
    var low = found[Math.floor(found.length * 0.02)];
    var high = found[Math.max(0, Math.ceil(found.length * 0.98) - 1)];
    if (high - low < 1e-9) { low -= 1; high += 1; }
    var pad = (high - low) * 0.12;
    low -= pad; high += pad;
    if (low > 0 && low < (high - low) * 0.4) { low = -pad; }    // keep the x axis in view
    if (high < 0 && -high < (high - low) * 0.4) { high = pad; }
    return [low, high];
  }

  function startingY(box, width, height) {
    var spec = box.mkSpec;
    if (spec.square) {
      var span = (spec.x[1] - spec.x[0]) * height / width;
      var middle = spec.y ? (spec.y[0] + spec.y[1]) / 2 : 0;
      return [middle - span / 2, middle + span / 2];
    }
    return box.mkY;
  }

  function draw(box) {
    var spec = box.mkSpec;
    if (!spec) { return; }
    var canvas = box.querySelector('canvas');
    var width = box.clientWidth;
    if (width < 40) { return; }                     // hidden: the ResizeObserver redraws
    var height = spec.height || Math.round(Math.min(380, Math.max(180, width * 0.7)));
    var ratio = window.devicePixelRatio || 1;
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';
    var g = canvas.getContext('2d');
    g.setTransform(ratio, 0, 0, ratio, 0, 0);
    g.clearRect(0, 0, width, height);

    var view = box.mkView;                          // set by a pinch; null is the start view
    var x0 = view ? view.x[0] : spec.x[0], x1 = view ? view.x[1] : spec.x[1];
    var range = view ? view.y : startingY(box, width, height);
    var y0 = range[0], y1 = range[1];
    box.mkShown = {x: [x0, x1], y: [y0, y1]};
    function px(x) { return (x - x0) / (x1 - x0) * width; }
    function py(y) { return height - (y - y0) / (y1 - y0) * height; }
    var text = cssVar(box, '--text', '#DDDDDD');
    var xStep = niceStep(x1 - x0, width / 64);
    var yStep = niceStep(y1 - y0, height / 48);
    var v;

    g.lineWidth = 1;
    g.strokeStyle = cssVar(box, '--rule', 'rgba(128,128,128,0.2)');
    g.beginPath();
    for (v = Math.ceil(x0 / xStep) * xStep; v <= x1; v += xStep) {
      g.moveTo(Math.round(px(v)) + 0.5, 0); g.lineTo(Math.round(px(v)) + 0.5, height);
    }
    for (v = Math.ceil(y0 / yStep) * yStep; v <= y1; v += yStep) {
      g.moveTo(0, Math.round(py(v)) + 0.5); g.lineTo(width, Math.round(py(v)) + 0.5);
    }
    g.stroke();

    g.lineWidth = 1.5;
    g.strokeStyle = cssVar(box, '--line', 'rgba(128,128,128,0.5)');
    g.beginPath();
    if (x0 <= 0 && 0 <= x1) { g.moveTo(px(0), 0); g.lineTo(px(0), height); }
    if (y0 <= 0 && 0 <= y1) { g.moveTo(0, py(0)); g.lineTo(width, py(0)); }
    g.stroke();

    g.fillStyle = text;
    g.globalAlpha = 0.6;
    g.font = '11px -apple-system, sans-serif';
    var axisRow = Math.min(height - 4, Math.max(13, py(0) + 13));
    var axisColumn = Math.min(width - 30, Math.max(3, px(0) + 4));
    g.textAlign = 'center';
    for (v = Math.ceil(x0 / xStep) * xStep; v <= x1; v += xStep) {
      if (Math.abs(v) > xStep / 100) { g.fillText(tickText(v, xStep), px(v), axisRow); }
    }
    g.textAlign = 'left';
    for (v = Math.ceil(y0 / yStep) * yStep; v <= y1; v += yStep) {
      if (Math.abs(v) > yStep / 100) { g.fillText(tickText(v, yStep), axisColumn, py(v) + 4); }
    }
    g.globalAlpha = 1;

    var samples = Math.max(240, Math.round(width * 2));
    var span = y1 - y0;
    for (var c = 0; c < spec.curves.length; c++) {
      var curve = spec.curves[c];
      g.strokeStyle = curveColour(box, c);
      g.lineWidth = curve.faint ? 1.5 : 2.5;
      g.globalAlpha = curve.faint ? 0.55 : 1;
      if (g.setLineDash) { g.setLineDash(curve.faint ? [5, 4] : []); }
      g.beginPath();
      var drawing = false, previous = null;
      for (var i = 0; i <= samples; i++) {
        var x = x0 + (x1 - x0) * i / samples;
        var y = evaluate(box, curve, x);
        if (y === null || (previous !== null && Math.abs(y - previous) > span * 4)) {
          drawing = false; previous = y; continue;
        }
        var screenY = Math.max(-height, Math.min(height * 2, py(y)));
        if (drawing) { g.lineTo(px(x), screenY); } else { g.moveTo(px(x), screenY); drawing = true; }
        previous = y;
      }
      g.stroke();
      if (g.setLineDash) { g.setLineDash([]); }
      g.globalAlpha = 1;
    }

    var readout = box.querySelector('.mk-readout');
    if (box.mkTrace === null) { return; }
    for (var t = 0; t < spec.curves.length; t++) {
      if (spec.curves[t].faint) { continue; }
      var traced = evaluate(box, spec.curves[t], box.mkTrace);
      readout.textContent = 'x = ' + shortNumber(box.mkTrace) +
        (traced === null ? ', y undefined' : ', y = ' + shortNumber(traced));
      if (traced !== null) {
        g.fillStyle = curveColour(box, t);
        g.beginPath(); g.arc(px(box.mkTrace), py(traced), 5, 0, Math.PI * 2); g.fill();
      }
      return;
    }
  }

  function redraw(box) {
    if (box.mkPending) { return; }
    box.mkPending = true;
    window.requestAnimationFrame(function () { box.mkPending = false; draw(box); });
  }

  function setUp(box) {
    box.setAttribute('data-mk-drawn', '1');
    var spec;
    try { spec = JSON.parse(box.getAttribute('data-graph')); } catch (error) { return; }
    box.mkSpec = spec;
    box.mkValues = {};
    box.mkTrace = null;
    box.mkView = null;
    var names = ['x'];
    for (var s = 0; s < spec.sliders.length; s++) {
      box.mkValues[spec.sliders[s].name] = spec.sliders[s].value;
      names.push(spec.sliders[s].name);
    }
    for (var c = 0; c < spec.curves.length; c++) {
      try { spec.curves[c].fn = new Function(names.join(','), 'return (' + spec.curves[c].js + ');'); }
      catch (error) { spec.curves[c].fn = null; }
    }
    var keys = box.querySelectorAll('.mk-key i');
    for (var k = 0; k < keys.length; k++) { keys[k].style.background = curveColour(box, k); }
    var inputs = box.querySelectorAll('input[data-name]');
    for (var i = 0; i < inputs.length; i++) {
      inputs[i].addEventListener('input', function () {
        box.mkValues[this.getAttribute('data-name')] = parseFloat(this.value);
        var label = this.parentNode.querySelector('.mk-svalue');
        if (label) { label.textContent = String(Number(parseFloat(this.value).toFixed(3))); }
        redraw(box);
      });
    }
    box.mkY = spec.y || autoY(box);
    if (window.ResizeObserver) { new ResizeObserver(function () { redraw(box); }).observe(box); }
    draw(box);
  }

  function setUpAll() {
    var boxes = document.querySelectorAll('.mk-graph:not([data-mk-drawn])');
    for (var i = 0; i < boxes.length; i++) { setUp(boxes[i]); }
  }

  // --- Tap: trace, and Reset view ---
  function traceAt(canvas, clientX) {
    var box = canvas.closest('.mk-graph');
    if (!box || !box.mkShown) { return; }
    var rect = canvas.getBoundingClientRect();
    var shown = box.mkShown.x;
    box.mkTrace = shown[0] + (clientX - rect.left) / rect.width * (shown[1] - shown[0]);
    redraw(box);
  }

  function resetView(button) {
    var box = button.closest('.mk-graph');
    if (!box) { return; }
    box.mkView = null;
    box.classList.remove('mk-zoomed');
    redraw(box);
  }

  function isCanvas(target) {
    return target && target.classList && target.classList.contains('mk-canvas');
  }

  function resetFor(target) {
    if (target && target.nodeType !== 1) { target = target.parentNode; }
    return target && target.closest ? target.closest('[data-graph-reset]') : null;
  }

  // --- Two fingers on a graph: zoom and pan it, not the page ---
  var pinch = null;          // {box, rect, start fingers, x, y} while a graph is pinched
  var graphGesture = false;  // the current WebKit gesture began on a graph
  var lastPinch = 0;

  function fingers(event) {
    var a = event.touches[0], b = event.touches[1];
    var dx = a.clientX - b.clientX, dy = a.clientY - b.clientY;
    return {x: (a.clientX + b.clientX) / 2, y: (a.clientY + b.clientY) / 2,
            d: Math.max(10, Math.sqrt(dx * dx + dy * dy))};
  }

  function clampSpan(span) { return Math.min(LARGEST_SPAN, Math.max(SMALLEST_SPAN, span)); }

  function pinchMoved(event) {
    var now = fingers(event);
    var scale = now.d / pinch.start.d;
    var r = pinch.rect;
    var spanX = clampSpan((pinch.x[1] - pinch.x[0]) / scale);
    var spanY = clampSpan((pinch.y[1] - pinch.y[0]) / scale);
    // The graph point that was under the fingers' centre stays under it.
    var gx = pinch.x[0] + (pinch.start.x - r.left) / r.width * (pinch.x[1] - pinch.x[0]);
    var gy = pinch.y[1] - (pinch.start.y - r.top) / r.height * (pinch.y[1] - pinch.y[0]);
    var left = gx - (now.x - r.left) / r.width * spanX;
    var top = gy + (now.y - r.top) / r.height * spanY;
    pinch.box.mkView = {x: [left, left + spanX], y: [top - spanY, top]};
    pinch.box.classList.add('mk-zoomed');
    redraw(pinch.box);
  }

  ['gesturestart', 'gesturechange', 'gestureend'].forEach(function (name) {
    window.addEventListener(name, function (event) {
      if (name === 'gesturestart') {
        var target = event.target;
        graphGesture = !!(target && target.closest && target.closest('.mk-canvas'));
      }
      if (graphGesture) { event.preventDefault(); event.stopPropagation(); }
      if (name === 'gestureend') { graphGesture = false; }
    }, true);
  });

  // --- One finger on a graph: drag it around inside its box ---
  var start = null;
  var drag = null;           // {box, rect, x, y, moved} while one finger is on a graph

  function dragMoved(dx, dy) {
    var spanX = drag.x[1] - drag.x[0], spanY = drag.y[1] - drag.y[0];
    var shiftX = dx / drag.rect.width * spanX, shiftY = dy / drag.rect.height * spanY;
    drag.box.mkView = {x: [drag.x[0] - shiftX, drag.x[1] - shiftX],
                       y: [drag.y[0] + shiftY, drag.y[1] + shiftY]};
    drag.box.classList.add('mk-zoomed');
    redraw(drag.box);
  }

  window.addEventListener('touchstart', function (event) {
    var touch = event.touches[0];
    if (event.touches.length === 1) {
      start = touch ? {x: touch.clientX, y: touch.clientY, many: false} : null;
      var held = isCanvas(event.target) ? event.target.closest('.mk-graph') : null;
      drag = (held && held.mkShown && touch) ?
        {box: held, rect: event.target.getBoundingClientRect(),
         x: held.mkShown.x.slice(), y: held.mkShown.y.slice(), moved: false} : null;
    } else {
      if (start) { start.many = true; }
      drag = null;                                  // two fingers: the pinch takes over
    }
    if (event.touches.length === 2 && isCanvas(event.touches[0].target) &&
        event.touches[0].target === event.touches[1].target) {
      var box = event.touches[0].target.closest('.mk-graph');
      if (box && box.mkShown) {
        event.preventDefault();
        pinch = {box: box, rect: event.touches[0].target.getBoundingClientRect(),
                 start: fingers(event), x: box.mkShown.x.slice(), y: box.mkShown.y.slice()};
      }
    }
  }, {capture: true, passive: false});

  window.addEventListener('touchmove', function (event) {
    if (pinch && event.touches.length >= 2) {
      event.preventDefault();
      pinchMoved(event);
      return;
    }
    if (drag && start && event.touches.length === 1) {
      event.preventDefault();
      var touch = event.touches[0];
      var dx = touch.clientX - start.x, dy = touch.clientY - start.y;
      if (!drag.moved && Math.abs(dx) <= TAP_SLOP && Math.abs(dy) <= TAP_SLOP) { return; }
      drag.moved = true;
      dragMoved(dx, dy);
    }
  }, {capture: true, passive: false});

  window.addEventListener('touchend', function (event) {
    if (pinch && event.touches.length < 2) { pinch = null; lastPinch = Date.now(); return; }
    if (drag && drag.moved) { drag = null; event.preventDefault(); return; }   // not a tap
    drag = null;
    var touch = event.changedTouches[0];
    if (!start || !touch || start.many || event.touches.length) { return; }
    if (Math.abs(touch.clientX - start.x) > TAP_SLOP ||
        Math.abs(touch.clientY - start.y) > TAP_SLOP) { return; }
    if (Date.now() - lastPinch < 400) { return; }
    var reset = resetFor(event.target);
    if (reset) { event.preventDefault(); resetView(reset); return; }
    if (isCanvas(event.target)) { event.preventDefault(); traceAt(event.target, touch.clientX); }
  }, {capture: true, passive: false});

  window.addEventListener('touchcancel', function () { pinch = null; drag = null; }, true);

  new MutationObserver(setUpAll).observe(document.documentElement, {childList: true, subtree: true});
  document.addEventListener('DOMContentLoaded', setUpAll);
})();
"""
