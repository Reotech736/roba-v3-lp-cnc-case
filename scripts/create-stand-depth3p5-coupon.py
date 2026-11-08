"""Fusion MCP: local depth-3.5 test coupon in the current document, no new cloud file."""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'
NAME='stand_test_depth3p5_fingerD8_NOT_FOR_MANUFACTURE'


def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE' and not doc.isModified and doc.dataFile.versionNumber==12
    assert not any(o.component.name.startswith('STAND_COUPON_DEPTH3p5_') for o in root.occurrences)
    m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(20,0,0)
    occ=root.occurrences.addNewComponent(m);c=occ.component;c.name='STAND_COUPON_DEPTH3p5_FINGER_D8_LOCAL_TEST_ONLY'
    def p(x,y):return adsk.core.Point3D.create(x/10,y/10,0)
    def rounded(s,x,y,w,h,r):
        def q(u,v):return p(x+u,y+v)
        for a,b in [((r,0),(w-r,0)),((w,r),(w,h-r)),((w-r,h),(r,h)),((0,h-r),(0,r))]:s.sketchCurves.sketchLines.addByTwoPoints(q(*a),q(*b)).isFixed=True
        for a,b,e in [((w-r,0),(w-r+r/math.sqrt(2),r-r/math.sqrt(2)),(w,r)),((w,h-r),(w-r+r/math.sqrt(2),h-r+r/math.sqrt(2)),(w-r,h)),((r,h),(r-r/math.sqrt(2),h-r+r/math.sqrt(2)),(0,h-r)),((0,r),(r-r/math.sqrt(2),r-r/math.sqrt(2)),(r,0))]:s.sketchCurves.sketchArcs.addByThreePoints(q(*a),q(*b),q(*e)).isFixed=True
    s=c.sketches.add(c.xYConstructionPlane);rounded(s,0,0,64.8,18.8,1.5)
    c.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString('5.5 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation);s.isLightBulbOn=False
    i=c.constructionPlanes.createInput();i.setByOffset(c.xYConstructionPlane,adsk.core.ValueInput.createByString('2 mm'));plane=c.constructionPlanes.add(i);plane.isLightBulbOn=False
    def cut(s,name):
        i=c.features.extrudeFeatures.createInput(s.profiles.item(0),adsk.fusion.FeatureOperations.CutFeatureOperation)
        i.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('3.5 mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        i.participantBodies=[c.bRepBodies.item(0)];c.features.extrudeFeatures.add(i).name=name;s.isLightBulbOn=False
    s=c.sketches.add(plane);rounded(s,6,2,56.8,14.8,2.2);cut(s,'Stand_pocket_56p8x14p8_R2p2_depth3p5')
    s=c.sketches.add(plane);s.sketchCurves.sketchCircles.addByCenterRadius(p(6,9.4),.4).isFixed=True;cut(s,'Finger_access_D8_same_depth')
    assert d.computeAll();assert c.bRepBodies.count==1
    body=c.bRepBodies.item(0);inside=adsk.fusion.PointContainment.PointInsidePointContainment
    checks=[]
    for x,y,z,expect in [(3,9.4,3,False),(6,9.4,3,False),(20,9.4,3,False),(60,9.4,3,False),(1,9.4,3,True),(3,3,3,True),(3,9.4,1,True),(20,9.4,1,True),(60,9.4,1,True)]:
        actual=body.pointContainment(adsk.core.Point3D.create(x/10,y/10,z/10))==inside
        assert actual==expect;checks.append([x,y,z,actual])
    # STEP component export skips hidden occurrences. Export while visible, then hide.
    occ.isLightBulbOn=True
    ex=d.exportManager
    assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/'+NAME+'.f3d',c))
    assert ex.execute(ex.createSTEPExportOptions(BASE+'cad/design/'+NAME+'.step',c))
    stl=ex.createSTLExportOptions(c.bRepBodies.item(0),BASE+'cad/design/'+NAME+'.stl');stl.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits;stl.isBinaryFormat=True;stl.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh;stl.sendToPrintUtility=False
    assert ex.execute(stl)
    occ.isLightBulbOn=False
    assert doc.save('Add hidden local depth3.5 stand fit coupon; export standalone F3D/STEP/mm STL without creating another editable cloud file.')
    assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d'))
    r=dict(date='2026-11-08',outer_mm=[64.8,18.8,5.5],pocket_mm=[56.8,14.8,3.5],pocketR_mm=2.2,fingerDiameter_mm=8,floor_mm=2,
           pointChecks=checks,stlUnits='mm',bodyCount=1,componentDisplayTranslationX_mm=200,
           limitations=['Local fit coupon only, not a case stiffness/assembly/stand deployment certification','Actual adhesive thickness and nail access remain unmeasured','Printer process/material/tolerances are not specified; no print order placed'])
    json.dump(r,open(BASE+'cad/design/'+NAME+'.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(r,ensure_ascii=False))
