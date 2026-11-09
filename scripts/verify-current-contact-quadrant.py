"""Fusion readOnly: exact42mm edge and conservative rigid-body contact-plane bound.

If every solid has X>=contactX and Z>=contactZ, then sin(t)*dx+cos(t)*dz
is nonnegative for 0<=t<=90 degrees. This is not stand stability or compliance.
"""
import adsk.core,adsk.fusion,json
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')


def run(_context: str):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    x0=-111.119997;z0=-11.5
    prefixes=('Lower_L_','Upper_L_','PCB_L_','MCU_RAISED_','XIAO_DETAILED_','CHOC_SWITCHES_AND_SOCKETS_','PCB_SUPPORT_INSULATION_','BATTERY_ASSEMBLY_','COVER_M1p6x6_')
    bodies=[]
    def walk(o):
        if o.component.name=='CLEARANCE_STUDIES_NOT_PARTS':return
        for b in o.bRepBodies:
            if b.isSolid:bodies.append((o.fullPathName,b))
        for ch in o.childOccurrences:walk(ch)
    for o in root.occurrences:
        if o.component.name.startswith(prefixes):walk(o)
    for o in root.allOccurrences:
        if o.component.name.startswith(('WIRE_BRACKET_M1p6x4_','WIRE_BRACKET_TIE_HEAD_')):
            for b in o.bRepBodies:bodies.append((o.fullPathName,b))
    violations=[]
    for name,b in bodies:
        p=b.preciseBoundingBox.minPoint
        if p.x*10<x0-1e-5 or p.z*10<z0-1e-5:violations.append({'name':name,'minimum_mm':[v*10 for v in p.asArray()]})
    lower=next(o for o in root.occurrences if o.component.name.startswith('Lower_L_'));edges=[]
    for edge in lower.bRepBodies.item(0).edges:
        if not adsk.core.Line3D.cast(edge.geometry):continue
        ps=[[v*10 for v in q.geometry.asArray()] for q in [edge.startVertex,edge.endVertex]]
        if all(abs(p[0]-x0)<1e-5 and abs(p[2]-z0)<1e-5 for p in ps):edges.append({'length_mm':edge.length*10,'yInterval_mm':sorted(p[1] for p in ps)})
    assert len(edges)==1 and abs(edges[0]['length_mm']-42)<1e-5 and not violations
    out={'date':'2026-11-09','baselineCloudVersion':25,'contactEdgeX_mm':x0,'contactEdgeZ_mm':z0,'continuousEdge':edges[0],
         'solidBoundsChecked':len(bodies),'positiveQuadrantViolations':violations,'nominalM2Screws':'D3.8xH2 heads at Z-11.3..-9.3; D2 shanks at Z-9.3..2.7 remain above Z-11.5 and right of X-111.119997',
         'idealPlaneProof':'All checked solid points satisfy dx>=0 and dz>=0, so sin(theta)*dx+cos(theta)*dz>=0 for0..90deg positive-X lift.',
         'limitations':['Rigid selected solids only; real stand geometry, feet, compliance, friction and tip-over stability unverified.',
                        'No contact-edge chamfer or protective layer qualified.']}
    (BASE/'docs/case-wire-bracket-contact-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
