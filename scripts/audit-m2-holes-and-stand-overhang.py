"""Fusion MCP read-only audit. Positive-solid clearance does not certify holes or DFM.

Write the current audit separately; preserve v17-fastening-and-overhang-audit.json as baseline.
"""
import adsk.core,adsk.fusion,json
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')

def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent;mgr=adsk.fusion.TemporaryBRepManager.get()
    lower=next(o for o in root.occurrences if o.component.name.startswith('Lower_L_'))
    upper=next(o for o in root.occurrences if o.component.name.startswith('Upper_L_'))
    native=lower.component.bRepBodies.item(0);world=mgr.copy(native);assert mgr.transform(world,lower.transform2)
    top=mgr.copy(upper.component.bRepBodies.item(0));assert mgr.transform(top,upper.transform2)
    axes=json.loads((BASE/'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.json').read_text())['screwAxesXY_mm']
    def cylinder(x,y,z0,z1,r):return mgr.createCylinderOrCone(adsk.core.Point3D.create(x/10,y/10,z0/10),r/10,adsk.core.Point3D.create(x/10,y/10,z1/10),r/10)
    def overlap(tool,target):
        b=mgr.copy(tool);assert mgr.booleanOperation(b,target,adsk.fusion.BooleanTypes.IntersectionBooleanType);return b.volume*1000
    checks=[]
    for x,y in axes:
        checks.append(dict(axisXY_mm=[x,y],lowerD2p2PassageObstruction_mm3=overlap(cylinder(x,y,-9.3,-1,1.1),world),
            lowerD4p2SeatObstruction_mm3=overlap(cylinder(x,y,-11.5,-9.3,2.1),world),
            M2NominalShankVsLower_mm3=overlap(cylinder(x,y,-9.3,2.7,1),world),
            M2AssumedHeadVsLower_mm3=overlap(cylinder(x,y,-11.3,-9.3,1.9),world),
            upperD1p6PilotObstruction_mm3=overlap(cylinder(x,y,-1,3.5,.8),top)))
    inside=adsk.fusion.PointContainment.PointInsidePointContainment
    def material(x,y,z):return native.pointContainment(adsk.core.Point3D.create(x/10,y/10,(z+11.5)/10))==inside
    samples=[]
    # Baseline selected rectangle had y=-73; sample outside the base and inside added backing.
    for x in [-51.9,-51,-50,-49,-48,-47.5]:
        samples.append(dict(pointXY_mm=[x,-72.9],baseAtGlobalZminus10p5=material(x,-72.9,-10.5),backingAtGlobalZminus8=material(x,-72.9,-8)))
    blocked=[v for v in checks if any(value>1e-5 for key,value in v.items() if key.endswith('_mm3'))]
    overhang=[v for v in samples if v['backingAtGlobalZminus8'] and not v['baseAtGlobalZminus10p5']]
    out=dict(cloudVersion=a.activeDocument.dataFile.versionNumber,M2Checks=checks,backingSamples=samples,
        obstructedM2Axes=len(blocked),sampledOverhangPoints=len(overhang),status='FAIL' if blocked or overhang else 'CHECKED_SUBSET_CLEAR',
        limitations=['Only specified axes, nominal screw dimensions and selected backing samples; not full exterior containment or manufacturing certification',
        'Full thread engagement, radial wall distribution, drill tip, driver access, fastener tolerances, preload and strength are not certified'])
    (BASE/'docs/fastening-and-overhang-current-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False))
