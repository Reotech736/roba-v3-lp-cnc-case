"""Fusion readOnly: evaluate a case-mounted nonmetal strain-relief bracket.

Uses temporary world-space stock/case candidates. Case editing is a separate step.
"""
import adsk.core,adsk.fusion,json,math
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')


def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber==25 and not doc.isModified
    mgr=adsk.fusion.TemporaryBRepManager.get();union=adsk.fusion.BooleanTypes.UnionBooleanType;cut=adsk.fusion.BooleanTypes.DifferenceBooleanType;intersection=adsk.fusion.BooleanTypes.IntersectionBooleanType
    def point(p):return adsk.core.Point3D.create(*[v/10 for v in p])
    def box(b):
        x0,y0,z0,x1,y1,z1=b
        return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(point([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2]),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
    def cyl(x,y,z0,z1,r):return mgr.createCylinderOrCone(point([x,y,z0]),r/10,point([x,y,z1]),r/10)
    bracketBoxes=[[-4,-24,-4.9,4,-16.5,-4],[3,-22,-4.9,11.7,-19.5,-4],
                  [10.9,-24,-4.9,11.7,-20,-1],[10.9,-26.8,-2.2,14.6,-19.7,-1]]
    stock=box(bracketBoxes[0])
    for b in bracketBoxes[1:]:assert mgr.booleanOperation(stock,box(b),union)
    # A conservative tangent cylinder along the fixed terminal straight can
    # preflight the cradle. Exact full-path groove is produced in CAD later.
    pose=json.loads((BASE/'docs/battery-service-loop-study.json').read_text())['poses'][0]
    last=pose['bundleSegments'][-1];a=last['start'];b=last['end'];length=math.dist(a,b);u=[(q-p)/length for p,q in zip(a,b)]
    first=[p-v for p,v in zip(a,u)];lastPoint=[p+v for p,v in zip(b,u)]
    groove=mgr.createCylinderOrCone(point(first),.17,point(lastPoint),.17)
    assert mgr.booleanOperation(stock,groove,cut)
    axes=[[12.8,-25],[12.8,-21.5]]
    for x,y in axes:assert mgr.booleanOperation(stock,cyl(x,y,-3,-.9,.9),cut)
    # Slot axes follow the wire projection; two slots straddle its terminal span.
    vx,vy=u[:2];n=math.hypot(vx,vy);vx/=n;vy/=n;px,py=-vy,vx
    q=[b[i]-u[i]*1.6 for i in range(3)]
    slots=[]
    for sign in [-1,1]:
        cx=q[0]+sign*2.6*px;cy=q[1]+sign*2.6*py
        slot=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(point([cx,cy,-4.5]),adsk.core.Vector3D.create(vx,vy,0),adsk.core.Vector3D.create(px,py,0),.22,.11,.2))
        assert mgr.booleanOperation(stock,slot,cut)
        slots.append({'centerXY_mm':[cx,cy],'longAxisXY':[vx,vy],'width_mm':2.2,'thickness_mm':1.1})
    lower=next(o for o in root.occurrences if o.component.name.startswith('Lower_L_')).bRepBodies.item(0)
    upper=next(o for o in root.occurrences if o.component.name.startswith('Upper_L_')).bRepBodies.item(0)
    originalLower=mgr.copy(lower);newLower=mgr.copy(lower)
    backing=[13.8,-27.6,-5.4,16,-18.2,-1];relief=[10.7,-27.2,-5.2,14.9,-18.6,-1]
    assert mgr.booleanOperation(newLower,box(backing),union)
    assert mgr.booleanOperation(newLower,box(relief),cut)
    newUpper=mgr.copy(upper)
    for x,y in axes:assert mgr.booleanOperation(newUpper,cyl(x,y,-1,2.6,.625),cut)
    def overlap(a,b):
        aa,bb=a.boundingBox,b.boundingBox
        if any(min(getattr(aa.maxPoint,v),getattr(bb.maxPoint,v))-max(getattr(aa.minPoint,v),getattr(bb.minPoint,v))<=1e-7 for v in ['x','y','z']):return 0
        c=mgr.copy(a);assert mgr.booleanOperation(c,b,intersection);return c.volume*1000
    targets=[('lower_candidate',newLower),('upper_candidate',newUpper)]
    def walk(o):
        for body in o.bRepBodies:
            if body.isSolid:yield o.component.name,body
        for child in o.childOccurrences:yield from walk(child)
    for o in root.allOccurrences:
        if o.component.name.startswith(('PCB_L_','MCU_RAISED_','XIAO_DETAILED_','CHOC_V2_RED_','CHOC_SOCKET_DETAILED_','BATTERY_CELL_NOMINAL_42','BATTERY_REMOVABLE_CARRIER_','PCB_SUPPORT_INSULATION_')):targets.extend(walk(o))
    collisions=[]
    for name,target in targets:
        v=overlap(stock,target)
        if v>1e-5:collisions.append({'target':name,'volume_mm3':v})
    # Upper pilots must be completely surrounded by stock at their major diameter.
    pilotSupport=[]
    for x,y in axes:
        c=cyl(x,y,-1,2.6,.8)
        pilotSupport.append({'axisXY_mm':[x,y],'majorCylinderStockFraction':overlap(c,upper)/(c.volume*1000)})
    oldBounds=originalLower.boundingBox;newBounds=newLower.boundingBox
    out={'date':'2026-11-09','baselineCloudVersion':25,'bracketStockBoxesGlobal_mm':bracketBoxes,'axesXY_mm':axes,
         'lowerBackingGlobal_mm':backing,'lowerReliefGlobal_mm':relief,'tieSlots':slots,
         'bracketPreflightVolume_mm3':stock.volume*1000,'bracketCollisions':collisions,'pilotStock':pilotSupport,
         'lowerBoundsBefore_mm':[[v*10 for v in p.asArray()] for p in [oldBounds.minPoint,oldBounds.maxPoint]],
         'lowerBoundsAfter_mm':[[v*10 for v in p.asArray()] for p in [newBounds.minPoint,newBounds.maxPoint]],
         'localOuterWallNominal_mm':1.1,'reliefToBracketZNominal_mm':.3,
         'limitations':['Preflight uses only terminal tangent groove; final uses the exact curved D3.4 path.',
             'Nonmetal material and tie/insulation contact force unqualified. Tie selected only by size class.',
             'Case wall/neck and cantilever strength, corner finish and manufacturing tool access require review.',
             'No PCB copper contact required for this mounting concept.']}
    (BASE/'docs/case-wire-bracket-preflight.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k not in ['limitations','tieSlots','bracketStockBoxesGlobal_mm']}))
