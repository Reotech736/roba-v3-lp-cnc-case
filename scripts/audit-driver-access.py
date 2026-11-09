"""Fusion readOnly: bounded axial driver checks, no detailed assembly motion.

D3 and D1.8 are assumed straight tool envelopes, not selected driver products.
"""
import adsk.core,adsk.fusion,json,math
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')


def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct)
    assert doc.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE' and doc.dataFile.versionNumber in [23,24,25] and not doc.isModified
    root=d.rootComponent;mgr=adsk.fusion.TemporaryBRepManager.get()
    axes=json.loads((BASE/'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.json').read_text())['screwAxesXY_mm']
    def walk(o):
        for b in o.bRepBodies:yield o.component.name,b
        for ch in o.childOccurrences:yield from walk(ch)
    targets=[]
    for o in root.allOccurrences:
        if o.component.name.startswith(('Lower_L_','Upper_L_','MCU_RAISED_','KEYCAP_SWEEP_','CHOC_V2_RED_','XIAO_DETAILED_')):
            targets.extend(walk(o))
    rows=[]
    for kind,positions,z0,z1 in [('M2',axes,-40,-10.3),('M1.6',[[-8,3.8],[8,3.8]],8.9,40)]:
        for x,y in positions:
            for diameter in [3,1.8]:
                tool=mgr.createCylinderOrCone(adsk.core.Point3D.create(x/10,y/10,z0/10),diameter/20,adsk.core.Point3D.create(x/10,y/10,z1/10),diameter/20)
                collisions=[];candidateCount=0
                for name,b in targets:
                    a,c=tool.boundingBox,b.boundingBox
                    if any(min(getattr(a.maxPoint,v),getattr(c.maxPoint,v))-max(getattr(a.minPoint,v),getattr(c.minPoint,v))<=1e-7 for v in ['x','y','z']):continue
                    candidateCount+=1
                    (BASE/'docs/driver-access-progress.json').write_text(json.dumps({'kind':kind,'axis':[x,y],'diameter':diameter,'target':name}),encoding='utf-8')
                    copy=mgr.copy(tool);assert mgr.booleanOperation(copy,b,adsk.fusion.BooleanTypes.IntersectionBooleanType)
                    if copy.volume*1000>1e-5:collisions.append({'target':name,'volume_mm3':copy.volume*1000})
                rows.append({'kind':kind,'axisXY_mm':[x,y],'toolDiameter_mm':diameter,'toolZInterval_mm':[z0,z1],
                             'positiveBBoxCandidates':candidateCount,'collisions':collisions})
                (BASE/'docs/driver-access-verification.json').write_text(json.dumps({'status':'PARTIAL','checks':rows},indent=2)+'\n',encoding='utf-8')
    fasteners=[]
    for kind,pitch,length,grip,pilot,depth,cap in [('M2',.4,12,8.3,1.6,4.5,1),('M1.6',.35,6,3.5,1.25,3.2,1.3)]:
        projection=length-grip;point=(pilot/2)/math.tan(math.radians(59))
        fasteners.append({'kind':kind,'pitch_mm':pitch,'length_mm':length,'nominalGrip_mm':grip,'geometricProjection_mm':projection,
                         'cylindricalPilotDiameter_mm':pilot,'cylindricalDepth_mm':depth,'bottomGap_mm':depth-projection,
                         'marginOverHalfPilotDiameter_mm':depth-projection-pilot/2,'assumedDrillPoint118degDepth_mm':point,
                         'axialCapAfterAssumedDrillPoint_mm':cap-point,
                         'engagementSensitivity_mm':[{'assumedLostThreadTurns':turns,'remainingOverlap_mm':max(0,projection-turns*pitch)} for turns in [1,2,3]]})
    out={'date':'2026-11-08','cloudVersion':doc.dataFile.versionNumber,'status':'SPECIFIED_AXIAL_ENVELOPES_CHECKED',
         'checks':rows,'fastenerDepthStudy':fasteners,'geometryModified':False,
         'sources':['https://us.misumi-ec.com/blog/metric-socket-head-cap-screws-dimensions/','https://jlccnc.com/help/article/threaded-hole-guideline'],
         'limitations':['D3 and D1.8 straight cylinders are study assumptions. 1.5 AF hex has circumscribed diameter 1.732 mm; actual shaft, holder and hand need separate access.',
                        'Screw heads and recess shape are excluded from tool collision targets; socket engagement is assumed, not modeled.',
                        'Cap sweep is the existing D3.0 drop, 18.8 mm square assumption; exact cap geometry is unconfirmed.',
                        'Thread projection is not effective engagement. Tap lead, chamfer, drill point, tolerances, strength and torque remain unqualified.',
                        'No continuous PCB, cover, battery or stand motion has been certified.']}
    (BASE/'docs/driver-access-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert not doc.isModified
    print(json.dumps({'checks':len(rows),'collisionCounts':[len(r['collisions']) for r in rows]}))
