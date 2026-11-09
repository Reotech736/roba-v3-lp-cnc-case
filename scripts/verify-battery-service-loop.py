"""Fusion readOnly: exact temporary wire curves vs selected static solids by pose.

No solid boolean sweeps. Each pose is separate; continuous motion is unproven.
"""
import adsk.core,adsk.fusion,json,math
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')
GAPS=[0]  # Replace with a bounded subset, e.g. [2,5,8,10], after closed-pose review.


def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct)
    assert doc.dataFile.versionNumber in [24,25,26]
    mgr=adsk.fusion.TemporaryBRepManager.get();study=json.loads((BASE/'docs/battery-service-loop-study.json').read_text(encoding='utf-8'))
    def point(p):return adsk.core.Point3D.create(*[v/10 for v in p])
    def walk(o):
        for b in o.bRepBodies:yield o.component.name,b
        for c in o.childOccurrences:yield from walk(c)
    fixed=[];moving=[]
    for o in d.rootComponent.allOccurrences:
        name=o.component.name
        if name.startswith(('Upper_L_','MCU_RAISED_','PCB_L_','PCB_SUPPORT_INSULATION_','XIAO_DETAILED_','CHOC_SOCKET_DETAILED_','CHOC_V2_RED_','WIRE_STRAIN_RELIEF_CASE_BRACKET_')):
            fixed.extend(walk(o))
        if name.startswith(('Lower_L_','BATTERY_REMOVABLE_CARRIER_','BATTERY_CELL_NOMINAL_42','CARRIER_BASE_REMOVABLE_','CELL_REMOVABLE_ADHESIVE_')):
            moving.extend(walk(o))
    rows=[]
    for pose in study['poses']:
        gap=pose['lowerDown_mm']
        if gap not in GAPS or pose['bendRadiusAssumed_mm']!=3:continue
        curves=[]
        for s in pose['bundleSegments']:
            curves.append(adsk.core.Line3D.create(point(s['start']),point(s['end'])) if s['type']=='line' else adsk.core.Arc3D.createByThreePoints(point(s['start']),point(s['mid']),point(s['end'])))
        wire,edges=mgr.createWireFromCurves(curves)
        assert wire and wire.edges.count==len(curves)
        apiLength=sum(e.length*10 for e in wire.edges)
        assert abs(apiLength-pose['bundleLength_mm'])<1e-6
        shift=adsk.core.Matrix3D.create();shift.translation=adsk.core.Vector3D.create(0,0,-gap/10)
        targets=list(fixed)
        for name,b in moving:
            c=mgr.copy(b);assert mgr.transform(c,shift);targets.append((name,c))
        minMargin=1e9;nearest=None;hits=[];measures=0
        for name,b in targets:
            # Broad-phase distance between AABBs is a conservative distance bound.
            a,c=wire.boundingBox,b.boundingBox
            separation=math.sqrt(sum(max(0,getattr(a.minPoint,v)-getattr(c.maxPoint,v),getattr(c.minPoint,v)-getattr(a.maxPoint,v))**2 for v in ['x','y','z']))*10
            if separation>study['bundleRadiusAssumed_mm']+.5:continue
            (BASE/'docs/battery-service-loop-progress.json').write_text(json.dumps({'gap':gap,'target':name,'stage':'measure'}),encoding='utf-8')
            result=app.measureManager.measureMinimumDistance(wire,b);assert result
            distance=result.value*10;measures+=1
            inside=any(b.pointContainment(point(s[k]))==adsk.fusion.PointContainment.PointInsidePointContainment for s in pose['bundleSegments'] for k in ['start','end'])
            margin=(-distance if inside else distance)-study['bundleRadiusAssumed_mm']
            if margin<minMargin:minMargin=margin;nearest=name
            if margin<-.00001:hits.append({'target':name,'centerlineDistance_mm':distance,'insideSample':inside,'radiusExcess_mm':-margin})
        rows.append({'lowerDown_mm':gap,'radiusAssumed_mm':3,'leadLength_mm':pose['eachLeadLength_mm'],'apiBundleLength_mm':apiLength,
                     'distanceQueries':measures,'nearest':nearest,'minimumCheckedRadiusMargin_mm':minMargin,'obstructions':hits})
        path=BASE/f'docs/battery-service-loop-verification-gap{gap}.json'
        path.write_text(json.dumps({'date':'2026-11-08','cloudVersion':doc.dataFile.versionNumber,'rows':[rows[-1]],'method':'Exact temporary line/arc wire-body minimum distance; D3 spherical offset, point-containment samples; lower and battery translated as one rigid set','notProven':['Continuous deformation','Actual wire bend specification','Paired-wire offsets','Pouch transition, terminal-branch bends and solder fillet','Physical opening or strain relief']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # Read-only queries also support the unsaved working revision before save.
    print(json.dumps(rows))
