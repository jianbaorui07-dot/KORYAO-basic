// staircase_oblique.jsx — faithful OBLIQUE rebuild of a perspective staircase
// line drawing. No image trace: every tread/riser corner is computed by
// projection and drawn as an individual stroked path.
//
// Transport: inject over COM with the StarBridge pattern. The runner prepends a
// config block, e.g.:  var STARBRIDGE_CONFIG = { strokeWidth:2.0, lineColor:[15,15,18] };
//
// Key lesson encoded here (see training_data/forward_line_reconstruction.jsonl):
//   * Keep the TRUE side profile undistorted — tread strictly horizontal (Ry=0),
//     riser strictly vertical (Hx=0); skew only the receding WIDTH axis W.
//   * Construction lines are anchored to real corners. The near-wall TOP edge
//     runs parallel to the far-wall top and connects the landing front corner to
//     the bottom-left floor corner — so the two long diagonals form one band.

(function () {
    var cfg = (typeof STARBRIDGE_CONFIG !== "undefined") ? STARBRIDGE_CONFIG : {};
    var stroke = (cfg.strokeWidth != null) ? cfg.strokeWidth : 2.0;
    var inkC   = cfg.lineColor || [15, 15, 18];

    var IW = 1264, IH = 1232;
    var doc = app.documents.add(DocumentColorSpace.RGB, IW, IH);
    var ab = doc.artboards[doc.artboards.getActiveArtboardIndex()].artboardRect;
    var abLeft = ab[0], abTop = ab[1];

    var layer = doc.layers.add();
    layer.name = "staircase_vector";

    var ink = new RGBColor();
    ink.red = inkC[0]; ink.green = inkC[1]; ink.blue = inkC[2];

    var count = 0;
    function L(pts, w, closed) {              // pts in image space (y DOWN)
        var conv = [];
        for (var i = 0; i < pts.length; i++) conv.push([abLeft + pts[i][0], abTop - pts[i][1]]);
        var p = layer.pathItems.add();
        p.setEntirePath(conv);
        p.filled = false; p.stroked = true;
        p.strokeWidth = (w != null) ? w : stroke;
        p.strokeColor = ink; p.closed = closed ? true : false;
        p.strokeCap = StrokeCap.ROUNDENDCAP; p.strokeJoin = StrokeJoin.ROUNDENDJOIN;
        count++; return p;
    }

    // ---- oblique projection -------------------------------------------------
    var N = 15;
    var Ox = 215, Oy = 1012;       // P(0,0,0): near, bottom of first riser
    var Rx = 42.3, Ry = 0.0;       // run  per step: TREAD stays HORIZONTAL
    var Hx = 0.0,  Hy = -47.3;     // rise per step: RISER stays VERTICAL
    var Wx = 265,  Wy = -120;      // oblique depth: stair WIDTH recedes up-right
    function P(i, j, k) { return [Ox + i*Rx + j*Wx + k*Hx, Oy + i*Ry + j*Wy + k*Hy]; }

    // near & far step profiles (riser, then tread, repeated)
    function profile(j) {
        var v = [];
        for (var m = 0; m < N; m++) { v.push(P(m, j, m)); v.push(P(m, j, m + 1)); }
        v.push(P(N, j, N));
        return v;
    }
    var nearV = profile(0), farV = profile(1);
    L(nearV, stroke);                                  // near zigzag (front edge)
    L(farV, stroke);                                   // far  zigzag (back edge)
    for (var v = 0; v < nearV.length; v++) L([nearV[v], farV[v]], stroke);  // W-rungs

    // ---- top landing + two vertical wall panels -----------------------------
    var nearTop = P(N, 0, N);      // top of last step, near
    var farTop  = P(N, 1, N);      // far top corner, where panels stand
    L([farTop, [farTop[0] + 60, 300]], stroke);                 // right edge down to floor
    L([[farTop[0] + 60, 300], [nearTop[0] + 55, 300]], stroke); // front floor edge
    L([nearTop, [nearTop[0] + 55, 300]], stroke);               // close to last step
    function panel(b0, b1, vh) {
        var t0 = [b0[0], b0[1] - vh], t1 = [b1[0], b1[1] - vh];
        L([b0, t0], stroke); L([b1, t1], stroke); L([t0, t1], stroke); L([b0, b1], stroke);
    }
    panel([905, 288], [992, 261], 198);                // left panel
    panel([1050, 245], [1137, 218], 198);              // right panel

    // ---- enclosing far wall + floor (long framing strokes) ------------------
    L([[905, 90], [175, 840]], stroke);                // far wall top (outer diagonal)
    L([[175, 840], [178, 1075]], stroke);              // far wall left vertical
    L([[178, 1075], [Ox, Oy + 78]], stroke);           // bottom floor edge
    L([[Ox, Oy + 78], [Ox, Oy]], stroke);              // near wall front (up to base)
    L([[Ox, Oy + 78], [nearTop[0], nearTop[1]]], stroke); // near floor line under flight
    // near wall TOP edge: landing front corner -> bottom-left floor corner
    // (parallel to the far-wall top, so the two long diagonals line up as a band)
    L([[905, 288], [178, 1075]], stroke);

    try { app.executeMenuCommand("fitall"); } catch (e) {}
    app.redraw();
    return "" + count;
})();
