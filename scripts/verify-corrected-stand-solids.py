"""Fusion MCP read-only: exact nominal void and residual solids, hole/seat continuity."""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'

def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent;mgr=adsk.fusion.TemporaryBRepManager.get()
    lower=next(o.component for o in root.occurrences if o.component.name.startswith('Lower_L_'));body=lower.bRepBodies.item(0)
    report=json.load(open(BASE+'docs/stand-and-M2-correction.json',encoding='utf-8'))
    def box(x0,y0,z0,x1,y1,z1):
        return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create((x0+x1)/20,(y0+y1)/20,(z0+z1)/20),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
    def cylinder(x,y,z0,z1,r):return mgr.createCylinderOrCone(adsk.core.Point3D.create(x/10,y/10,z0/10),r/10,adsk.core.Point3D.create(x/10,y/10,z1/10),r/10)
    def union(a,b):assert mgr.booleanOperation(a,b,adsk.fusion.BooleanTypes.UnionBooleanType)
    def roundrect(x,y,w,h,r,z0,z1):
        result=box(x+r,y,z0,x+w-r,y+h,z1);union(result,box(x,y+r,z0,x+w,y+h-r,z1))
        for cx,cy in [(x+r,y+r),(x+w-r,y+r),(x+w-r,y+h-r),(x+r,y+h-r)]:union(result,cylinder(cx,cy,z0,z1,r))
        return result
    checks=[]
    for pocket,center in zip(report['standPocketsXYWH_mm'],report['fingerCentersXY_mm']):
        void=roundrect(*pocket,2.2,0,3.5);union(void,cylinder(*center,0,3.5,4))
        nominalArea=void.volume*1000/3.5
        assert mgr.booleanOperation(void,body,adsk.fusion.BooleanTypes.IntersectionBooleanType)
        blocked=void.volume*1000;assert blocked<1e-5,str(blocked)
        residual=roundrect(*pocket,2.2,3.5,5.5);union(residual,cylinder(*center,3.5,5.5,4))
        assert mgr.booleanOperation(residual,body,adsk.fusion.BooleanTypes.DifferenceBooleanType)
        missing=residual.volume*1000;assert missing<1e-5,str(missing)
        checks.append(dict(pocketXYWH_mm=pocket,fingerXY_mm=center,nominalPocketAndFingerArea_mm2=nominalArea,nominalDepth_mm=3.5,nominalResidual_mm=2,obstructingPocketMaterial_mm3=blocked,missingResidualMaterial_mm3=missing))
    axes=json.load(open(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.json',encoding='utf-8'))['screwAxesXY_mm'];walls=[]
    for x,y in axes:
        ring=cylinder(x,y,0,2.2,3);assert mgr.booleanOperation(ring,cylinder(x,y,0,2.2,2.1),adsk.fusion.BooleanTypes.DifferenceBooleanType)
        assert mgr.booleanOperation(ring,body,adsk.fusion.BooleanTypes.DifferenceBooleanType)
        missing=ring.volume*1000;assert missing<1e-5,str((x,y,missing))
        walls.append(dict(axisXY_mm=[x,y],seatRadialAnnulus_mm=.9,missingAnnulusMaterial_mm3=missing))
    # Export actual moved backing sketch geometry for whole-footprint containment calculation.
    footprints=[]
    for name in ['スケッチ3','スケッチ4']:
        s=next(s for s in lower.sketches if s.name==name);points=[p.geometry for p in list(s.sketchPoints)[1:]]
        footprints.append(dict(rectXYXY_mm=[min(p.x*10 for p in points),min(p.y*10 for p in points),max(p.x*10 for p in points),max(p.y*10 for p in points)]))
    s=next(s for s in lower.sketches if s.name=='スケッチ15');circles=[dict(centerXY_mm=[c.centerSketchPoint.geometry.x*10,c.centerSketchPoint.geometry.y*10],radius_mm=c.radius*10) for c in s.sketchCurves.sketchCircles]
    for f,c in zip(footprints,sorted(circles,key=lambda v:v['centerXY_mm'][1])):f['circle']=c
    out=dict(pocketAndResidualVolumeChecks=checks,M2SeatWallChecks=walls,actualBackingFootprints=footprints,
        limitations=['Exact nominal model volumes; tolerances, physical stand motion and strength not certified','0.9mm radial seat wall is verified geometrically, not accepted as a manufacturing/strength requirement'])
    json.dump(out,open(BASE+'docs/corrected-stand-solid-verification.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False))
