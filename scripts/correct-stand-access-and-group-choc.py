"""Fusion MCP recovery one-shot: complete notch move after backing shift, then group CHOC."""
import adsk.core, adsk.fusion, json
BASE = 'C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'


def run(_context: str):
    app = adsk.core.Application.get(); doc = app.activeDocument
    d = adsk.fusion.Design.cast(app.activeProduct); root = d.rootComponent
    assert doc.name == 'left_case_two_stands_v05_NOT_FOR_MANUFACTURE'
    assert doc.dataFile.versionNumber == 14
    ex = d.exportManager
    if not doc.isModified:
        assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/checkpoints/v05_cloud_v14_before_access_and_browser_group.f3d'))
    lower = next(o for o in root.occurrences if o.component.name.startswith('Lower_L_'))
    coupon = next(o for o in root.occurrences if o.component.name.startswith('STAND_COUPON_'))
    def shift(sketch, dx):
        d.timeline.markerPosition=sketch.timelineObject.index+1
        curves = list(sketch.sketchCurves)
        col = adsk.core.ObjectCollection.create()
        for curve in curves:
            curve.isFixed = False; col.add(curve)
        for point in list(sketch.sketchPoints)[1:]: point.isFixed = False
        m = adsk.core.Matrix3D.create(); m.translation = adsk.core.Vector3D.create(dx/10,0,0)
        assert sketch.move(col,m)
        for curve in curves: curve.isFixed = True
        d.timeline.moveToEnd()
    # Recovery preflight: backing is already shifted, notch and coupon are still original.
    # Never rerun on v15; preserve checkpoints and use verification JSON for the final state.
    assert not any(o.component.name.startswith('CHOC_SWITCHES_AND_SOCKETS_REFERENCE_') for o in root.occurrences)
    circles_to_move=[s for s in lower.component.sketches if s.sketchCurves.sketchCircles.count==2 and all(abs(c.centerSketchPoint.geometry.x*10+50)<1e-5 for c in s.sketchCurves.sketchCircles)]
    assert len(circles_to_move)==1
    assert len([s for s in lower.component.sketches if s.sketchCurves.sketchCircles.count==2 and all(abs(c.centerSketchPoint.geometry.x*10-6.8)<1e-5 and abs(c.radius*10-6)<1e-5 for c in s.sketchCurves.sketchCircles)])==1
    assert abs(coupon.component.sketches.item(2).sketchCurves.sketchCircles.item(0).centerSketchPoint.geometry.x*10-6)<1e-6
    assert abs(coupon.component.sketches.item(1).sketchCurves.sketchLines.item(0).startSketchPoint.geometry.x*10-8.2)<1e-6
    assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/checkpoints/v05_verified_backing_moved_notch_original_before_completion.f3d'))
    # Shift backing and notch sketches together; leave original pocket extents untouched.
    for s in lower.component.sketches:
        circles = list(s.sketchCurves.sketchCircles)
        if len(circles)==2 and all(abs(c.centerSketchPoint.geometry.x*10+50)<1e-5 for c in circles):
            assert all(abs(c.radius*10-4)<1e-5 or abs(c.radius*10-6)<1e-5 for c in circles)
            shift(s,56.8)
    for f in lower.component.features.extrudeFeatures:
        if f.name.startswith('Stand_left_end_finger_notches_'): f.name='Stand_positive_X_end_finger_notches_D8_depth3p5'
    # Reflect the asymmetric coupon margins: pocket begins at 2, notch at 58.8.
    shift(coupon.component.sketches.item(1),-4)
    shift(coupon.component.sketches.item(2),52.8)
    assert d.computeAll()
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    def material(body,x,y,z): return body.pointContainment(adsk.core.Point3D.create(x/10,y/10,z/10))==inside
    samples=[]; body=lower.component.bRepBodies.item(0)
    for y in [-63.6,-17.1]:
        for x,z,expected in [(-53,1,True),(9.8,3,False),(9.8,3.51,True),(9.8,5.49,True),(9.8,5.51,False),(-20,3.49,False),(-20,3.51,True)]:
            actual=material(body,x,y,z); assert actual==expected,str((x,y,z,actual,expected)); samples.append([x,y,z,actual])
    for x,z,expected in [(3,3,False),(61.8,3,False),(63.8,3,True),(61.8,1,True)]:
        assert material(coupon.component.bRepBodies.item(0),x,9.4,z)==expected
    refs=[o for o in root.occurrences if o.component.name.startswith(('CHOC_V2_RED_DETAILED_','CHOC_SOCKET_DETAILED_'))]
    assert len(refs)==46
    def state(o):
        b=o.boundingBox
        return dict(matrix=o.transform2.asArray(),bounds=[[p.x,p.y,p.z] for p in [b.minPoint,b.maxPoint]],visible=o.isLightBulbOn)
    before=[state(o) for o in refs]
    group=root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    group.component.name='CHOC_SWITCHES_AND_SOCKETS_REFERENCE_23_PAIRS'
    moved=[]
    for o,expected in zip(refs,before):
        new=o.moveToComponent(group); assert new
        actual=state(new)
        assert max(abs(a-b) for a,b in zip(actual['matrix'],expected['matrix']))<1e-8
        assert max(abs(a-b) for p,q in zip(actual['bounds'],expected['bounds']) for a,b in zip(p,q))<1e-8
        assert actual['visible']==expected['visible']; moved.append(new)
    if d.snapshots.hasPendingSnapshot: d.snapshots.add()
    assert d.computeAll(); assert group.childOccurrences.count==46
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage]; assert not issues,str(issues)
    for new,expected in zip(moved,before):
        assert max(abs(a-b) for a,b in zip(state(new)['matrix'],expected['matrix']))<1e-8
    coupon.isLightBulbOn=True
    name=BASE+'cad/design/stand_test_depth3p5_fingerD8_NOT_FOR_MANUFACTURE'
    assert ex.execute(ex.createFusionArchiveExportOptions(name+'.f3d',coupon.component))
    assert ex.execute(ex.createSTEPExportOptions(name+'.step',coupon.component))
    opt=ex.createSTLExportOptions(coupon.component.bRepBodies.item(0),name+'.stl')
    opt.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits; opt.isBinaryFormat=True
    opt.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh; opt.sendToPrintUtility=False
    assert ex.execute(opt); coupon.isLightBulbOn=False
    assert ex.execute(ex.createSTEPExportOptions(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE_Lower_L_LOCAL.step',lower.component))
    result=dict(date='2026-11-08',baselineCloudVersion=14,fingerCentersXY_mm=[[6.8,-63.6],[6.8,-17.1]],depth_mm=3.5,residual_mm=2,
                lowerVolume_mm3=body.volume*1000,materialChecks=samples,chocGroupName=group.component.name,occurrencesReparented=46,
                allPosesBoundsAndVisibilityPreserved=True,timelineIssues=issues,couponPocketXY_mm=[2,2],couponFingerXY_mm=[58.8,9.4],
                userBatteryWireLengthApprox_mm=50,userStandMaximumThicknessApprox_mm=4.2,foldedProtrusionNominal_mm=.7,
                wireRouteStatus='Existing 55.08 mm route plus service allowance is too long for approx 50 mm leads; not an accepted arrangement.')
    json.dump(result,open(BASE+'docs/stand-access-and-browser-group-verification.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    assert doc.save('Reverse both stand finger accesses to positive X; group 23 CHOC switches and sockets without changing poses. Wire length needs redesign.')
    assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d'))
    print(json.dumps(result,ensure_ascii=False))
