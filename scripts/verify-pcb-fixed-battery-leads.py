"""Fusion readOnly: closed D1 curves fixed to PCB; only lower moves.

This does not sweep solids or move the live design. Restrict gaps for first run.
"""
import adsk.core,adsk.fusion,json,math
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')
GAPS=[0,2,5,8,10]

def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct)
    assert doc.dataFile.versionNumber in [28,29]
    mgr=adsk.fusion.TemporaryBRepManager.get();study=json.loads((BASE/'docs/individual-battery-lead-study.json').read_text(encoding='utf-8'))
    def point(p):return adsk.core.Point3D.create(*[v/10 for v in p])
    def walk(o):
        for b in o.bRepBodies:
            if b.isSolid:yield o.component.name,b
        for c in o.childOccurrences:yield from walk(c)
    fixed=[];moving=[]
    for o in d.rootComponent.allOccurrences:
        name=o.component.name
        if name.startswith(('Upper_L_','MCU_RAISED_','PCB_L_','PCB_SUPPORT_INSULATION_','XIAO_DETAILED_','CHOC_SOCKET_DETAILED_','CHOC_V2_RED_','BATTERY_CELL_NOMINAL_42')):fixed.extend(walk(o))
        if name.startswith(('Lower_L_',)):moving.extend(walk(o))
    results=[]
    pose=next(p for p in study['poses'] if p['lowerDown_mm']==0)
    for gap in GAPS:
        shift=adsk.core.Matrix3D.create();shift.translation=adsk.core.Vector3D.create(0,0,-gap/10)
        targets=list(fixed)
        for name,b in moving:
            c=mgr.copy(b);assert mgr.transform(c,shift);targets.append((name,c))
        wires=[];rows=[]
        for lead in pose['leads']:
            curves=[adsk.core.Line3D.create(point(s['start']),point(s['end'])) if s['type']=='line' else adsk.core.Arc3D.createByThreePoints(point(s['start']),point(s['mid']),point(s['end'])) for s in lead['segments']]
            wire,_=mgr.createWireFromCurves(curves);assert wire;wires.append(wire)
            # Only nominal emergence/solder interfaces are allowed to touch their
            # respective host. Re-check every remaining section against that host.
            first=lead['segments'][0];last=lead['segments'][-1]
            assert first['type']==last['type']=='line' and first['length_mm']>.8 and last['length_mm']>.5
            start=[a+(b-a)*.8/first['length_mm'] for a,b in zip(first['start'],first['end'])]
            end=[b+(a-b)*.5/last['length_mm'] for a,b in zip(last['start'],last['end'])]
            pouchCurves=[adsk.core.Line3D.create(point(start),point(first['end']))]+curves[1:]
            pcbCurves=curves[:-1]+[adsk.core.Line3D.create(point(last['start']),point(end))]
            pouchWire,_=mgr.createWireFromCurves(pouchCurves);pcbWire,_=mgr.createWireFromCurves(pcbCurves)
            apiLength=sum(e.length*10 for e in wire.edges);assert abs(apiLength-40)<1e-6
            hits=[];near=[];queries=0
            for name,b in targets:
                tested=pouchWire if name.startswith('BATTERY_CELL_NOMINAL_42') else pcbWire if name.startswith('PCB_L_') else wire
                a,c=tested.boundingBox,b.boundingBox
                bound=math.sqrt(sum(max(0,getattr(a.minPoint,v)-getattr(c.maxPoint,v),getattr(c.minPoint,v)-getattr(a.maxPoint,v))**2 for v in ['x','y','z']))*10
                if bound>1.:continue
                distance=app.measureManager.measureMinimumDistance(tested,b).value*10;queries+=1
                inside=any(b.pointContainment(point(s[k]))==adsk.fusion.PointContainment.PointInsidePointContainment for s in lead['segments'] for k in ['start','end','mid'] if k in s)
                margin=(-distance if inside else distance)-.5
                near.append({'target':name,'margin_mm':margin})
                if margin<-.00001:hits.append({'target':name,'distance_mm':distance,'insideSample':inside,'radialOverlap_mm':-margin})
            rows.append({'side':lead['side'],'APIlength_mm':apiLength,'distanceQueries':queries,'obstructions':hits,'nearestChecked':sorted(near,key=lambda x:x['margin_mm'])[:4]})
        pairDistance=app.measureManager.measureMinimumDistance(wires[0],wires[1]).value*10
        result={'date':'2026-11-10','cloudVersion':doc.dataFile.versionNumber,'lowerDown_mm':gap,'mountingConcept':'PCB_FIXED_BATTERY_AND_WIRES_LOWER_ONLY_MOVES','wireCurvePoseUsed_mm':0,'selectedTargetSolids':len(targets),'leads':rows,'pairCenterlineDistance_mm':pairDistance,'pairD1SurfaceMargin_mm':pairDistance-1.,'intentionalInterfaceExclusions':{'pouchFirstCenterline_mm':.8,'solderFinalCenterline_mm':.5,'scope':'Exclusions apply only to respective host; other solids and pair tests retain full curve. No real pouch outlet or solder fillet modeled.'},'actualMinimumBendSpecificationVerified':False,'continuousOpeningVerified':False}
        results.append(result);(BASE/f'docs/pcb-fixed-lead-verification-gap{gap}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(results))
