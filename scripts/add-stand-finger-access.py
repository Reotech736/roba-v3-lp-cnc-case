"""Fusion MCP: provisional left-end access. MUST recut the original pockets next.

Run restore-stand-pocket-after-finger-backing.py before saving/exporting this study;
the backing added here temporarily enters the original pocket volume.
"""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'


def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE'
    lower=next(o.component for o in root.occurrences if o.component.name.startswith('Lower_L_'))
    assert not any(f.name=='Stand_left_end_finger_notches_D8_depth3p7' for f in lower.features.extrudeFeatures)
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/checkpoints/v05_before_stand_finger_access.f3d'))
    centers=[(-50,-63.6),(-50,-17.1)];before=lower.bRepBodies.item(0).volume*1000
    def circles(z,diameter):
        i=lower.constructionPlanes.createInput();i.setByOffset(lower.xYConstructionPlane,adsk.core.ValueInput.createByString(str(z)+' mm'))
        plane=lower.constructionPlanes.add(i);plane.isLightBulbOn=False;s=lower.sketches.add(plane)
        for x,y in centers:s.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(x/10,y/10,0),diameter/20).isFixed=True
        coll=adsk.core.ObjectCollection.create()
        for p in s.profiles:coll.add(p)
        return s,coll
    target=lower.bRepBodies.item(0);s,pr=circles(2,12)
    e=lower.features.extrudeFeatures.addSimple(pr,adsk.core.ValueInput.createByString('3.7 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation);s.isLightBulbOn=False;e.name='Finger_access_backing_D12_residual2mm'
    tools=adsk.core.ObjectCollection.create()
    for b in e.bodies:tools.add(b)
    i=lower.features.combineFeatures.createInput(target,tools);i.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation
    lower.features.combineFeatures.add(i).name='Join_finger_backing_to_lower_only'
    s,pr=circles(0,8)
    i=lower.features.extrudeFeatures.createInput(pr,adsk.fusion.FeatureOperations.CutFeatureOperation)
    i.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('stand_depth')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
    i.participantBodies=[lower.bRepBodies.item(0)]
    lower.features.extrudeFeatures.add(i).name='Stand_left_end_finger_notches_D8_depth3p7';s.isLightBulbOn=False
    assert d.computeAll();assert lower.bRepBodies.count==1
    body=lower.bRepBodies.item(0);inside=adsk.fusion.PointContainment.PointInsidePointContainment;checks=[]
    for x,y in centers:
        # x=-52 is outside the old stand pocket; verify actual new access and backing.
        for xx in [x-3,x-2,x-1]:
            for local_z,expect in [(3,False),(3.71,True),(5.69,True),(5.71,False)]:
                actual=body.pointContainment(adsk.core.Point3D.create(xx/10,y/10,local_z/10))==inside
                assert actual==expect,str((xx,y,local_z,actual,expect));checks.append([xx,y,local_z,actual])
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    out=dict(date='2026-11-08',centersXY_mm=centers,notchDiameter_mm=8,notchDepth_mm=3.7,
             backingDiameter_mm=12,nominalResidual_mm=2,addedLeftAccessBeyondPocket_mm=4,
             originalPocket_mm=[56.8,14.8,3.7],pointChecks=checks,volumeBefore_mm3=before,volumeAfter_mm3=body.volume*1000,
             timelineIssues=issues,limitations=['Left-end access is provisional; actual hinge/nail deployment direction unconfirmed',
             'Finger size, tape thickness, hinge sweep and physical use not validated','Not a promise of stand deployment clearance'])
    json.dump(out,open(BASE+'docs/stand-finger-access-verification.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False))
