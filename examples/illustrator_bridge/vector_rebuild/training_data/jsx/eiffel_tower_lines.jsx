// eiffel_tower_lines.jsx — parametric Eiffel Tower drawn one line at a time.
// No image trace: silhouette, iron lattice, platforms and antenna are all
// emitted as individual stroked paths from a small parametric core.
//
// Transport: inject over COM (StarBridge pattern). The runner prepends a config
// block, e.g.: var STARBRIDGE_CONFIG = { lineColor:[38,38,46], latticeColor:[95,100,112],
//                                        edgeWidth:3.0, latticeWidth:1.0 };
//
// Draws into the active document if one is open, else creates a 1000x1400 RGB
// artboard. All geometry is computed relative to the active artboardRect so it
// is robust to Illustrator version and artboard placement.

(function () {
    var cfg = (typeof STARBRIDGE_CONFIG !== "undefined") ? STARBRIDGE_CONFIG : {};
    var lineColor    = cfg.lineColor    || [38, 38, 46];
    var latticeColor = cfg.latticeColor || [95, 100, 112];
    var edgeWidth    = (cfg.edgeWidth    != null) ? cfg.edgeWidth    : 3.0;
    var latticeWidth = (cfg.latticeWidth != null) ? cfg.latticeWidth : 1.0;

    var doc = (app.documents.length > 0) ? app.activeDocument
                                         : app.documents.add(DocumentColorSpace.RGB, 1000, 1400);
    var abIndex = doc.artboards.getActiveArtboardIndex();
    var ab = doc.artboards[abIndex].artboardRect; // [left, top, right, bottom], top>bottom
    var abLeft = ab[0], abTop = ab[1], abRight = ab[2], abBottom = ab[3];
    var abW = abRight - abLeft, abH = abTop - abBottom;

    var cx    = abLeft + abW / 2.0;
    var baseY = abBottom + abH * 0.05;
    var H     = abH * 0.90;

    var layer = doc.layers.add();
    layer.name = "eiffel_tower_lines";

    function rgb(c) { var col = new RGBColor(); col.red = c[0]; col.green = c[1]; col.blue = c[2]; return col; }
    var colEdge = rgb(lineColor), colLat = rgb(latticeColor);

    var lineCount = 0;
    function addLine(pts, w, col, closed) {
        var p = layer.pathItems.add();
        p.setEntirePath(pts);
        p.filled = false; p.stroked = true;
        p.strokeWidth = w; p.strokeColor = col; p.closed = closed ? true : false;
        p.strokeCap = StrokeCap.ROUNDENDCAP; p.strokeJoin = StrokeJoin.ROUNDENDJOIN;
        lineCount++; return p;
    }

    // ---- silhouette: half-width(t) along height fraction t ------------------
    var profile = [
        [0.00, 168], [0.05, 140], [0.10, 118], [0.155, 100],
        [0.185, 95], [0.26, 78], [0.32, 66], [0.37, 56],
        [0.48, 42], [0.60, 31], [0.72, 23], [0.82, 18],
        [0.86, 16], [0.90, 13], [0.94, 10], [1.00, 7]
    ];
    function halfW(t) {
        if (t <= profile[0][0]) return profile[0][1];
        for (var i = 0; i < profile.length - 1; i++) {
            if (t >= profile[i][0] && t <= profile[i + 1][0]) {
                var f = (t - profile[i][0]) / (profile[i + 1][0] - profile[i][0]);
                return profile[i][1] + (profile[i + 1][1] - profile[i][1]) * f;
            }
        }
        return profile[profile.length - 1][1];
    }
    function yAt(t)    { return baseY + H * t; }
    function leftX(t)  { return cx - halfW(t); }
    function rightX(t) { return cx + halfW(t); }

    var P1 = 0.185, P2 = 0.37, P3 = 0.86;

    // arch opening under the first platform (half-ellipse)
    var archSpringT = 0.02, archCrownT = 0.135, archR = 118;
    function archOpenHalfW(t) {
        if (t < archSpringT) return archR;
        if (t > archCrownT)  return 0;
        var u = (t - archSpringT) / (archCrownT - archSpringT);
        var vv = 1 - u * u;
        return (vv > 0) ? archR * Math.sqrt(vv) : 0;
    }

    // 1) outer edges as two long polylines
    var Nn = 60, leftPts = [], rightPts = [];
    for (var i = 0; i <= Nn; i++) { var t = i / Nn; leftPts.push([leftX(t), yAt(t)]); rightPts.push([rightX(t), yAt(t)]); }
    addLine(leftPts, edgeWidth, colEdge, false);
    addLine(rightPts, edgeWidth, colEdge, false);

    // inner rails above platform 1
    var inset = 9, leftIn = [], rightIn = [];
    for (var i2 = 0; i2 <= Nn; i2++) {
        var tt = i2 / Nn; if (tt < P1) continue;
        leftIn.push([leftX(tt) + inset, yAt(tt)]); rightIn.push([rightX(tt) - inset, yAt(tt)]);
    }
    if (leftIn.length > 1)  addLine(leftIn,  latticeWidth + 0.4, colEdge, false);
    if (rightIn.length > 1) addLine(rightIn, latticeWidth + 0.4, colEdge, false);

    // 2) grand arch (parabola) + a concentric decorative arch
    var aSteps = 26, springY = yAt(archSpringT), crownY = yAt(archCrownT), archPts = [];
    for (var a = 0; a <= aSteps; a++) {
        var fx = a / aSteps, x = cx - archR + 2 * archR * fx;
        var hgt = 1 - Math.pow((fx - 0.5) / 0.5, 2);
        archPts.push([x, springY + (crownY - springY) * hgt]);
    }
    addLine(archPts, edgeWidth, colEdge, false);
    var archPts2 = [];
    for (var a2 = 0; a2 <= aSteps; a2++) {
        var fx2 = a2 / aSteps, x2 = cx - (archR - 16) + 2 * (archR - 16) * fx2;
        var hgt2 = 1 - Math.pow((fx2 - 0.5) / 0.5, 2);
        archPts2.push([x2, springY + (crownY - 18 - springY) * hgt2]);
    }
    addLine(archPts2, latticeWidth + 0.3, colEdge, false);

    // 3) platform decks (double line + caps + railings)
    function deck(t, overhang, thick) {
        var y = yAt(t), hw = halfW(t) + overhang;
        addLine([[cx - hw, y], [cx + hw, y]], edgeWidth, colEdge, false);
        addLine([[cx - hw, y - thick], [cx + hw, y - thick]], edgeWidth - 0.8, colEdge, false);
        addLine([[cx - hw, y], [cx - hw, y - thick]], edgeWidth - 0.8, colEdge, false);
        addLine([[cx + hw, y], [cx + hw, y - thick]], edgeWidth - 0.8, colEdge, false);
        var rN = Math.max(2, Math.round(hw / 12));
        for (var r = 0; r <= rN; r++) { var rx = cx - hw + (2 * hw) * (r / rN); addLine([[rx, y], [rx, y + 7]], latticeWidth, colLat, false); }
    }
    deck(P1, 26, 16); deck(P2, 14, 12); deck(P3, 9, 10);

    // 4) iconic iron lattice — X cross-braces per height band, columns scale with width
    var bands = 30;
    for (var b = 0; b < bands; b++) {
        var t1 = b / bands, t2 = (b + 1) / bands;
        var y1 = yAt(t1), y2 = yAt(t2);
        var lx1 = leftX(t1), rx1 = rightX(t1), lx2 = leftX(t2), rx2 = rightX(t2);
        var wMid = (rx1 - lx1 + rx2 - lx2) / 2.0;
        var nc = Math.max(1, Math.min(6, Math.round(wMid / 42)));
        for (var c = 0; c < nc; c++) {
            var f0 = c / nc, f1 = (c + 1) / nc;
            var topL = lx1 + (rx1 - lx1) * f0, topR = lx1 + (rx1 - lx1) * f1;
            var botL = lx2 + (rx2 - lx2) * f0, botR = lx2 + (rx2 - lx2) * f1;
            var skip = false;
            if (t2 <= P1) {
                var midY = (t1 + t2) / 2, open = archOpenHalfW(midY);
                var cellCx = (topL + topR + botL + botR) / 4.0;
                if (Math.abs(cellCx - cx) < open) skip = true;
            }
            if (skip) continue;
            addLine([[topL, y1], [botR, y2]], latticeWidth, colLat, false); // /
            addLine([[topR, y1], [botL, y2]], latticeWidth, colLat, false); // \
        }
    }

    // central spine above platform 1
    var spine = [];
    for (var s = 0; s <= Nn; s++) { var st = s / Nn; if (st < P1) continue; spine.push([cx, yAt(st)]); }
    if (spine.length > 1) addLine(spine, latticeWidth + 0.2, colLat, false);

    // 5) antenna / spire
    var tipTopY = yAt(1.0), boxHw = halfW(0.92);
    addLine([[cx - boxHw, yAt(0.90)], [cx - boxHw, yAt(0.965)]], edgeWidth - 1, colEdge, false);
    addLine([[cx + boxHw, yAt(0.90)], [cx + boxHw, yAt(0.965)]], edgeWidth - 1, colEdge, false);
    addLine([[cx - boxHw, yAt(0.965)], [cx + boxHw, yAt(0.965)]], edgeWidth - 1, colEdge, false);
    addLine([[cx, yAt(0.965)], [cx, tipTopY]], edgeWidth - 1, colEdge, false);
    addLine([[cx - 8, yAt(0.985)], [cx + 8, yAt(0.985)]], latticeWidth, colLat, false);
    addLine([[cx - 5, yAt(0.995)], [cx + 5, yAt(0.995)]], latticeWidth, colLat, false);

    app.redraw();
    return "" + lineCount;
})();
