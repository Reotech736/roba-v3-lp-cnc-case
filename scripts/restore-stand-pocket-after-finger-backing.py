"""Fusion MCP: recut original pockets so added finger backing cannot reduce storage depth."""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'


def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct)
    lower=next(o.component for o in d.rootComponent.occurrences if o.component.name.startswith('Lower_L_'))
    assert not any(f.name=='Restore_original_stand_pockets_after_finger_backing' for f in lower.features.extrudeFeatures)
    s=lower.sketches.add(lower.xYConstructionPlane);s.name='Original_stand_pocket_clearance_after_added_backing'
    for x,y,w,h in [(-50,-71,56.8,14.8),(-50,-24.5,56.8,14.8)]:
        r=2.2
        def p(u,v):return adsk.core.Point3D.create((x+u)/10,(y+v)/10,0)
        for first,last in [((r,0),(w-r,0)),((w,r),(w,h-r)),((w-r,h),(r,h)),((0,h-r),(0,r))]:
            s.sketchCurves.sketchLines.addByTwoPoints(p(*first),p(*last)).isFixed=True
        for first,mid,last in [((w-r,0),(w-r+r/math.sqrt(2),r-r/math.sqrt(2)),(w,r)),((w,h-r),(w-r+r/math.sqrt(2),h-r+r/math.sqrt(2)),(w-r,h)),((r,h),(r-r/math.sqrt(2),h-r+r/math.sqrt(2)),(0,h-r)),((0,r),(r-r/math.sqrt(2),r-r/math.sqrt(2)),(r,0))]:
            s.sketchCurves.sketchArcs.addByThreePoints(p(*first),p(*mid),p(*last)).isFixed=True
    assert s.profiles.count==2
    pc=adsk.core.ObjectCollection.create()
    for p in s.profiles:pc.add(p)
    body=lower.bRepBodies.item(0);before=body.volume*1000
    i=lower.features.extrudeFeatures.createInput(pc,adsk.fusion.FeatureOperations.CutFeatureOperation)
    i.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('stand_depth')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
    i.participantBodies=[body];lower.features.extrudeFeatures.add(i).name='Restore_original_stand_pockets_after_finger_backing';s.isLightBulbOn=False
    assert d.computeAll();assert lower.bRepBodies.count==1
    inside=adsk.fusion.PointContainment.PointInsidePointContainment;checks=[]
    for cy in [-63.6,-17.1]:
        for x in [-49,-47,-45]:
            for y in [cy-5,cy+5]:
                for z in [1,3,3.69]:
                    assert body.pointContainment(adsk.core.Point3D.create(x/10,y/10,z/10))!=inside
                    checks.append([x,y,z])
        for x in [-53,-52,-51]:
            for z,expected in [(3,False),(3.71,True),(5.69,True),(5.71,False)]:
                assert (body.pointContainment(adsk.core.Point3D.create(x/10,cy/10,z/10))==inside)==expected
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    out=dict(date='2026-11-08',restoredPocket_mm=[56.8,14.8,3.7],pocketR_mm=2.2,pocketVoidSamples=len(checks),
             fingerResidualSamples=24,removedIntrudingBacking_mm3=before-body.volume*1000,lowerVolume_mm3=body.volume*1000,timelineIssues=issues)
    json.dump(out,open(BASE+'docs/stand-pocket-restoration-verification.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    path=BASE+'docs/stand-finger-access-verification.json';v=json.load(open(path,encoding='utf-8'));v.update(originalPocketsRecut=True,pocketVoidSamples=len(checks),finalVolume_mm3=body.volume*1000)
    json.dump(v,open(path,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(out))
