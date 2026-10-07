"""Original cut-paper character drawings, sampled back into the ASCII grid."""
import math
import numpy as np
from PIL import Image, ImageDraw
from . import shapes as S


def portrait(cv, cx, cy, scale, m, t=0, mirror=False, closed=False, covered=False):
    # Hand-drawn layers in a 100 x 100 local square; no external artwork.
    def layer(points, color, stroke=False, width=1):
        im = Image.new("L", (cv.W * 3, cv.H * 3))
        d = ImageDraw.Draw(im)
        pts = [((cx + (50-x if mirror else x-50)*scale)*3,
                (cy + (y-50)*scale/cv.aspect)*3) for x,y in points]
        if stroke:
            d.line(pts, fill=255, width=max(2, int(width*scale*3)), joint="curve")
        else:
            d.polygon(pts, fill=255)
        a = np.asarray(im.resize((cv.W, cv.H), Image.Resampling.BOX), dtype=np.float32)/255
        mask = a > .2
        cv.ch[mask] = 0
        cv.bg[mask] = m.bg
        cv.shape_field(a, 0, 0, color, fill="#" if not stroke else "=", tin=.62, tedge=.18)
    sway=math.sin(t*1.7)*1.4
    # Hair silhouette, neck, blouse, sailor collar, shoulder, long loose strands.
    layer([(23,57),(19,34),(22,18),(31,7),(49,3),(64,9),(72,23),(73,42),
           (80+sway,65),(65,61),(60,49),(30,53)],m.fg)
    layer([(39,44),(56,43),(57,61),(72,67),(82,93),(13,93),(20,70),(39,60)],m.mid)
    layer([(33,23),(56,17),(64,27),(64,37),(69,43),(63,46),(59,55),(49,59),
           (38,52),(31,41)],m.bg)
    layer([(29,20),(37,13),(58,14),(64,24),(53,20),(48,33),(42,23),(36,37),(30,44)],m.fg)
    layer([(36,60),(47,69),(59,60),(66,67),(48,80),(29,67)],m.fg)
    layer([(35,65),(48,75),(61,65)],m.bg,True,1.2)
    layer([(48,76),(43,83),(47,91),(53,83)],m.accent)
    layer([(25,73),(30,84),(27,92)],m.fg,True)
    layer([(68,73),(63,83),(66,92)],m.fg,True)
    layer([(52,35),(60,34),(62,36)],m.fg,True)
    if not closed and int(t*2)%13 != 0:
        layer([(57,35),(57,39)],m.fg,True,1.3)
    layer([(59,48),(63,48)],m.fg,True,.7)
    layer([(29,19),(25,33),(27,48),(24,57)],m.mid,True,.6)
    layer([(66,19),(68,40),(72,58)],m.mid,True,.6)
    layer([(26,24),(33,23)],m.accent,True,1.3)

    if covered:
        # Forearms and separated fingers obscure the eyes, without changing identity.
        for off in (0, 22):
            layer([(29+off,89),(26+off,54),(29+off,34),(32+off,31),
                   (34+off,45),(37+off,34),(39+off,35),(39+off,53),(36+off,89)],m.mid)
            layer([(30+off,40),(30+off,56),(33+off,77)],m.fg,True,.6)


def furnishings(cv, vp, fg, dim, faint, t):
    x0,y0,x1,y1=vp
    w,h=x1-x0,y1-y0
    if w < 75 or w > 250: return
    def pt(x,y): return x0+w*x, y0+h*y
    def line(a,b,col=dim,ch=None): cv.line(*pt(*a),*pt(*b),col,ch)
    # Bookcase, uneven books, sliding door, skirting boards.
    for y in (.40,.49,.58,.68): line((.68,y),(.82,y))
    for x in (.68,.82): line((x,.40),(x,.68))
    for i in range(9):
        x=.691+i*.013
        line((x,.42+(i%3)*.016),(x,.485),fg, "|")
        line((x,.52+(i%2)*.02),(x,.575),dim, "|")
    for x in (.89,.97): line((x,.20),(x,.79))
    line((.89,.20),(.97,.20)); line((.89,.79),(.97,.79))
    line((.90,.47),(.90,.52),fg)
    # Low writing desk, legs, notebook and mug.
    corners=[(.12,.73),(.37,.73),(.43,.82),(.09,.82),(.12,.73)]
    cv.polyline([pt(*v) for v in corners],fg)
    for x in (.11,.40): line((x,.82),(x,.94),fg)
    line((.13,.84),(.39,.84))
    cv.polyline([pt(*v) for v in [(.22,.75),(.31,.75),(.33,.79),(.23,.79),(.22,.75)]],dim)
    x,y=pt(.15,.76); cv.put(int(x),int(y),"(__)o",fg)
    # Oblique window light and irregular plaster cracks.
    for k in range(4): line((.04+k*.045,.60),(.31+k*.07,.98),faint, ".")
    cv.polyline([pt(*v) for v in [(.57,.12),(.56,.18),(.58,.21),(.575,.25)]],faint)
    x,y=pt(.61,.41); cv.put(int(x),int(y),"[07]",dim)
    # Hanging shade, cable and swaying curtains.
    cv.polyline([pt(*v) for v in [(.46,.10),(.54,.10),(.57,.15),(.43,.15),(.46,.10)]],fg)
    for k in range(3):
        x=.065+k*.018+math.sin(t+k)*.006
        line((x,.18),(x+.018,.52),dim,":")
