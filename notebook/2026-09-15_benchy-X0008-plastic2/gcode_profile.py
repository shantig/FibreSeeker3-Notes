#!/usr/bin/env python3
"""Measure the settings a G-code file actually prints with, per ;TYPE: feature.

Reports tools, temperatures, bed, pressure advance, square-corner velocity,
layer heights, retract/deretract (E-only moves), lift after retract, fan
commands, travel speed, first-layer speeds, and per feature: the most common
speed, line width, layer height, extruded mm^3 per mm and flow relative to
Orca's nominal cross-section ((w - h(1 - pi/4)) * h). Handles G2/G3 arcs.
Works on OrcaSlicer and Rocket plastic-only files (both use ;TYPE:/;WIDTH:/;HEIGHT:).

Usage: gcode_profile.py FILE.gcode   (prints JSON)
"""
import re, sys, math, collections, statistics, json
AREA=math.pi*(1.75/2)**2
def profile(path):
    feat=None; width=None; height=None; layer=0; z=0.0
    x=y=None; F=None
    by=collections.defaultdict(lambda: {"len":0.0,"e":0.0,"t":0.0,"fw":collections.Counter(),"w":collections.Counter(),"h":collections.Counter()})
    retr=collections.Counter(); deretr=collections.Counter(); zhop=collections.Counter()
    temps=collections.Counter(); bed=collections.Counter(); fans=collections.Counter(); pa=[]; scv=[]; accel=collections.Counter()
    lh=collections.Counter(); travel_f=collections.Counter(); travel_len=0.0
    last_retract=False; lastz=None; first_layer_feats=collections.defaultdict(lambda: collections.Counter())
    tool=[]
    for ln in open(path, errors='replace'):
        s=ln.split(';',1)[0].strip() if not ln.startswith(';') else ''
        c=ln.strip()
        if c.startswith(';TYPE:'): feat=c[6:]; continue
        if c.startswith(';WIDTH:'): width=float(c[7:]); continue
        if c.startswith(';HEIGHT:'): height=float(c[8:]); lh[round(height,3)]+=1; continue
        m=re.match(r'^SET_PRINT_STATS_INFO CURRENT_LAYER=(\d+)',c)
        if m: layer=int(m.group(1)); continue
        if not s: continue
        if re.match(r'^T\d',s): tool.append(s.split()[0])
        m=re.match(r'^M10[49] S(\d+)',s)
        if m: temps[(layer<=1, int(m.group(1)))]+=1
        m=re.match(r'^M1[49]0 S(\d+)',s)
        if m: bed[int(m.group(1))]+=1
        m=re.match(r'^M106 (P\d+ )?S(\d+)',s)
        if m: fans[(m.group(1) or 'P0 ').strip()+f"={int(m.group(2))}"]+=1
        m=re.search(r'SET_PRESSURE_ADVANCE.*ADVANCE=([\d.]+)',s)
        if m: pa.append(float(m.group(1)))
        m=re.search(r'SQUARE_CORNER_VELOCITY=([\d.]+)',s)
        if m: scv.append(float(m.group(1)))
        m=re.search(r'SET_VELOCITY_LIMIT ACCEL=(\d+)',s)
        if m: accel[(feat,int(m.group(1)))]+=1
        if s.startswith(('G2 ','G3 ')) and x is not None:
            w=dict(re.findall(r'([XYIJEF])(-?[\d.]+)',s))
            if 'F' in w: F=float(w['F'])
            nx=float(w.get('X',x)); ny=float(w.get('Y',y)); cx=x+float(w.get('I',0)); cy=y+float(w.get('J',0))
            r=math.hypot(x-cx,y-cy); a0=math.atan2(y-cy,x-cx); a1=math.atan2(ny-cy,nx-cx)
            da=a1-a0
            if s.startswith('G2 '):
                da = da if da<0 else da-2*math.pi
            else:
                da = da if da>0 else da+2*math.pi
            if abs(nx-x)<1e-9 and abs(ny-y)<1e-9: da=2*math.pi
            d=abs(da)*r; e=float(w.get('E',0))
            if e>0 and d>0:
                bb=by[feat]; bb["len"]+=d; bb["e"]+=e; bb["fw"][int(round((F or 0)/60))]+=d
                if width: bb["w"][width]+=d
                if height: bb["h"][height]+=d
            x,y=nx,ny
            continue
        if s.startswith(('G1','G0')):
            w=dict(re.findall(r'([XYZEF])(-?[\d.]+)',s))
            if 'F' in w: F=float(w['F'])
            nx=float(w['X']) if 'X' in w else x; ny=float(w['Y']) if 'Y' in w else y
            if 'Z' in w:
                nz=float(w['Z'])
                if last_retract and lastz is not None and nz>lastz+0.01: zhop[round(nz-lastz,2)]+=1
                lastz=nz
            e=float(w['E']) if 'E' in w else 0.0
            moved = x is not None and ('X' in w or 'Y' in w)
            if not moved and 'E' in w:
                if e<0: retr[(round(-e,3), int(F or 0))]+=1; last_retract=True
                elif e>0: deretr[(round(e,3), int(F or 0))]+=1; last_retract=False
            elif moved:
                d=math.hypot(nx-x, ny-y)
                if e>0 and d>0:
                    b=by[feat]; b["len"]+=d; b["e"]+=e; b["fw"][int(round((F or 0)/60))]+=d
                    if width: b["w"][width]+=d
                    if height: b["h"][height]+=d
                    if layer<=1: first_layer_feats[feat][int(round((F or 0)/60))]+=d
                elif e<=0 and d>0:
                    travel_f[int(round((F or 0)/60))]+=d; travel_len+=d
            x,y=nx,ny
    out={"tools":sorted(set(tool)),"temps":{f"{'L1' if k[0] else 'later'} {k[1]}":v for k,v in temps.items()},"bed":dict(bed),"pa":pa,"scv":scv,
         "layer_heights":dict(lh.most_common(4)),"retract":[f"{k[0]}mm@{round(k[1]/60)}mm/s x{v}" for k,v in retr.most_common(3)],"deretract":[f"{k[0]}mm@{round(k[1]/60)}mm/s x{v}" for k,v in deretr.most_common(3)],"zhop_after_retract":dict(zhop.most_common(3)),
         "fans":dict(fans.most_common(6)),"travel_speed_mm_s":travel_f.most_common(3)}
    feats={}
    for k,b in by.items():
        if b["len"]<5: continue
        w=b["w"].most_common(1)[0][0] if b["w"] else None; h=b["h"].most_common(1)[0][0] if b["h"] else None
        mm3=b["e"]*AREA/b["len"]
        nominal=(w-h*(1-math.pi/4))*h if w and h else None
        feats[k]={"extruded_mm":round(b["len"]),"speed_mm_s":b["fw"].most_common(1)[0][0],"width":w,"height":h,"mm3_per_mm":round(mm3,4),"flow_vs_nominal":round(mm3/nominal,3) if nominal else None}
    out["features"]=feats
    out["first_layer_speeds"]={k:v.most_common(1)[0][0] for k,v in first_layer_feats.items()}
    out["accel_by_feature"]=sorted({(k[0],k[1]) for k in accel})[:30]
    return out
print(json.dumps(profile(sys.argv[1]),indent=1,default=str))
