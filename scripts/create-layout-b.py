"""Fusion MCP: separate layout B, with stand-pocket voids and residual-wall studies."""
import adsk.core, adsk.fusion, json, math
BASE = 'C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'
NAME = 'internal_layout_B_stand_separated_v01_NOT_FOR_MANUFACTURE'

def run(_context: str):
    a = adsk.core.Application.get()
    project = next(p for p in a.data.dataProjects if p.name == 'roba-v3-lp-cnc-case')
    folder = next(f for f in project.rootFolder.dataFolders if f.name == '02_design')
    assert not any(f.name == NAME for f in folder.dataFiles), 'Layout B already exists'
    doc = next(x for x in a.documents if x.dataFile and x.dataFile.id == 'urn:adsk.wipprod:dm.lineage:NCa0X1qHQyWJ9c1dNVD4-A')
    assert not doc.isModified
    doc.activate()
    assert doc.saveAs(NAME,folder,'Stand-pocket locations separated from provisional battery footprints; keepout study, no manufactured case.','')
    d = adsk.fusion.Design.cast(a.activeProduct)
    root = d.rootComponent
    def box_or_pocket(name,x,y,z,w,h,depth,r=0,visible=False):
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(x/10,y/10,z/10)
        c = root.occurrences.addNewComponent(m).component
        c.name = name
        s = c.sketches.add(c.xYConstructionPlane)
        def p(x,y):return adsk.core.Point3D.create(x/10,y/10,0)
        if r:
            curves = []
            curves.append(s.sketchCurves.sketchLines.addByTwoPoints(p(r,0),p(w-r,0)))
            curves.append(s.sketchCurves.sketchArcs.addByThreePoints(p(w-r,0),p(w-r+r/math.sqrt(2),r-r/math.sqrt(2)),p(w,r)))
            curves.append(s.sketchCurves.sketchLines.addByTwoPoints(p(w,r),p(w,h-r)))
            curves.append(s.sketchCurves.sketchArcs.addByThreePoints(p(w,h-r),p(w-r+r/math.sqrt(2),h-r+r/math.sqrt(2)),p(w-r,h)))
            curves.append(s.sketchCurves.sketchLines.addByTwoPoints(p(w-r,h),p(r,h)))
            curves.append(s.sketchCurves.sketchArcs.addByThreePoints(p(r,h),p(r-r/math.sqrt(2),h-r+r/math.sqrt(2)),p(0,h-r)))
            curves.append(s.sketchCurves.sketchLines.addByTwoPoints(p(0,h-r),p(0,r)))
            curves.append(s.sketchCurves.sketchArcs.addByThreePoints(p(0,r),p(r-r/math.sqrt(2),r-r/math.sqrt(2)),p(r,0)))
        else:
            curves = s.sketchCurves.sketchLines.addTwoPointRectangle(p(0,0),p(w,h))
        for curve in curves:curve.isFixed = True
        e = c.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString(str(depth)+' mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        s.isLightBulbOn = False
        e.bodies.item(0).name = name
        e.bodies.item(0).isLightBulbOn = visible
        return c
    result = []
    for side,x,tx in [('L',-103.3,0),('R',88.5,160)]:
        board = next(c for c in d.allComponents if c.name == 'PCB_'+side+'_v2_reference_NOT_VERIFIED').bRepBodies.item(0)
        outside = 0
        for i in range(16):
            for j in range(58):
                if board.pointContainment(adsk.core.Point3D.create((x+14.8*i/15)/10,(-65+56.8*j/57)/10,.08)) == adsk.fusion.PointContainment.PointOutsidePointContainment:outside += 1
        assert outside == 0
        pocket = box_or_pocket('Stand_'+side+'_POCKET_VOID_NOT_PART_14p8x56p8_R2p2',(x+tx),-65,-11.5,14.8,56.8,3.7,2.2,True)
        expected = (14.8*56.8-(4-math.pi)*2.2**2)*3.7
        assert abs(pocket.bRepBodies.item(0).volume*1000-expected)<.001
        box_or_pocket('Stand_'+side+'_RESIDUAL_WALL_2mm_STUDY_NOT_CASE',x+tx-2,-67,-7.8,18.8,60.8,2,0,False)
        for end,y in [('A',-71),('B',-8.2)]:
            box_or_pocket('Stand_'+side+'_FINGER_ACCESS_'+end+'_6mm_ASSUMED',x+tx,y,-11.5,14.8,6,4,0,False)
        result.append(dict(side=side,displayTranslationX_mm=tx,pocketLocalBounds_mm=[[x,-65,-11.5],[x+14.8,-8.2,-7.8]],cornerRadius_mm=2.2,depth_mm=3.7,projectionSamples=928,outsidePCBMaterialSamples=outside,batteryAllowanceXYGap_mm=22.5,residualWallZ_mm=[-7.8,-5.8],residualThickness_mm=2,PCB3mmReservationToRaisedFloorGap_mm=2.8,notes='XY position and rounded-corner radius are provisional. Stand opening direction/support polygon unverified.'))
    issues = [t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage]
    assert not issues,str(issues)
    assert doc.save('Add stand pocket voids, residual-wall volumes and finger access reservations.')
    ex = d.exportManager
    assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/'+NAME+'.f3d'))
    report = dict(name=NAME,date='2026-11-07',id=doc.dataFile.id,summary=result,baseline=dict(PCBLowerFaceZ_mm=0,assumedOutsideBottomZ_mm=-11.5,batteryRegionInsideFloorZ_mm=-9.5,standRegionInsideFloorZ_mm=-5.8),timelineIssues=issues,limitations=['Void and wall study bodies are not a case assembly. No material was removed from reference cases.','Actual stand body/sweep and adhesive are not modeled. Finger access 6 mm is a placeholder at both ends.','PCB projection sampling is not an exact containment or component collision test.','M2 external screw markers retained from layout A, not optimized.','COROPIT, MCU, USB, wire routing, antenna, tipping stability and final CNC corners remain unresolved.'])
    with open(BASE+'cad/design/'+NAME+'.json','w',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    a.activeViewport.fit()
    print(json.dumps(report))
