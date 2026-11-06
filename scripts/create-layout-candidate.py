"""Run via Fusion MCP. Creates a separate study; never edits source/reference files."""
import adsk.core, adsk.fusion, json
BASE = 'C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'
NAME = 'internal_layout_candidate_v01_NOT_FOR_MANUFACTURE'

def run(_context: str):
    a = adsk.core.Application.get()
    project = next(p for p in a.data.dataProjects if p.name == 'roba-v3-lp-cnc-case')
    folder = next(f for f in project.rootFolder.dataFolders if f.name == '02_design')
    existing = next((f for f in folder.dataFiles if f.name == NAME), None)
    if existing:
        # Recover only an unchanged initial copy after a failed API run.
        opened = next((x for x in a.documents if x.dataFile and x.dataFile.id == existing.id), None)
        if opened:
            assert not opened.isModified, 'Close the failed study without saving before retrying'
        doc = opened or a.documents.open(existing)
        doc.activate()
        check = adsk.fusion.Design.cast(a.activeProduct)
        assert check.allComponents.count == 5 and all('PARKED' in c.name for c in check.allComponents if c.name.startswith('Battery_')), 'Completed or altered study already exists'
    else:
        doc = next(x for x in a.documents if x.dataFile and x.dataFile.id == 'urn:adsk.wipprod:dm.lineage:TDPgr-O0Ro-8BhpLoqM8uA')
        assert not doc.isModified
        source_id = doc.dataFile.id
        doc.activate()
        assert doc.saveAs(NAME, folder, 'Provisional battery and external screw study; no case geometry or verified assembled parts.', '')
        assert doc.dataFile.id != source_id
    d = adsk.fusion.Design.cast(a.activeProduct)
    root = d.rootComponent
    def component(name, x, y, z):
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(x/10, y/10, z/10)
        o = root.occurrences.addNewComponent(m)
        o.component.name = name
        return o.component
    def box(name, xyz, size, visible):
        c = component(name, *xyz)
        s = c.sketches.add(c.xYConstructionPlane)
        s.name = 'Assumed_envelope_NOT_component_CAD'
        for line in s.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(0,0,0), adsk.core.Point3D.create(size[0]/10,size[1]/10,0)):
            line.isFixed = True
        e = c.features.extrudeFeatures.addSimple(s.profiles.item(0), adsk.core.ValueInput.createByString(str(size[2])+' mm'), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        e.bodies.item(0).name = name
        s.isLightBulbOn = False
        e.bodies.item(0).isLightBulbOn = visible
        return c
    summary = []
    for side, bx in [('L',-65),('R',35)]:
        tx = 0 if side == 'L' else 160
        pcb_occ = next(o for o in root.occurrences if o.component.name.startswith('PCB_'+side))
        pcb = pcb_occ.component.bRepBodies.item(0)
        battery = next(o for o in root.occurrences if o.component.name.startswith('Battery_'+side))
        m = adsk.core.Matrix3D.create()
        # Original battery's local sketch starts at y=30 mm.
        m.translation = adsk.core.Vector3D.create((tx+bx)/10, -80/10, -8/10)
        battery.transform2 = m
        # Capture before adding features: timeline recompute otherwise restores
        # the parked occurrence position from the copied design.
        if d.snapshots.hasPendingSnapshot:
            d.snapshots.add()
        battery.component.name = 'Battery_'+side+'_30x20x4_CANDIDATE_UNVERIFIED'
        box('Battery_'+side+'_32x22x5p5_INSTALLATION_ALLOWANCE_ASSUMED', (tx+bx-1,-51,-9), (32,22,5.5), False)
        bounds = pcb.boundingBox
        x0,y0 = bounds.minPoint.x*10,bounds.minPoint.y*10
        x1,y1 = bounds.maxPoint.x*10,bounds.maxPoint.y*10
        box('PCB_'+side+'_UNDERSIDE_3mm_RESERVATION_NOT_COMPLETE_PARTS', (tx+x0,y0,-3), (x1-x0,y1-y0,3), False)
        c = component('Screw_'+side+'_M2_EXTERNAL_AXES_ONLY_NOT_FINAL',tx,0,0)
        s = c.sketches.add(c.xYConstructionPlane)
        s.name = 'Four_external_candidates_d6_boss_and_d2_axis_NO_HOLES'
        axes = [(x0-5,y1-15),(x1+5,y1-15),(x0-5,y0+15),(x1+5,y0+15)]
        for x,y in axes:
            for radius in (1,3):
                circle = s.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(x/10,y/10,0),radius/10)
                circle.isConstruction = True
                circle.isFixed = True
        # Check the projected allowance perimeter against PCB material at 0.8 mm.
        pts = []
        for i in range(65):
            x = bx-1+32*i/64
            pts.extend([(x,-51),(x,-29)])
        for i in range(45):
            y = -51+22*i/44
            pts.extend([(bx-1,y),(bx+31,y)])
        outside = [(x,y) for x,y in pts if pcb.pointContainment(adsk.core.Point3D.create(x/10,y/10,.08)) == adsk.fusion.PointContainment.PointOutsidePointContainment]
        summary.append(dict(side=side,displayTranslateX_mm=tx,batteryLocalBounds_mm=[[bx,-50,-8],[bx+30,-30,-4]],allowanceLocalBounds_mm=[[bx-1,-51,-9],[bx+31,-29,-3.5]],screwAxesLocalXY_mm=axes,perimeterSampleCount=len(pts),outsidePCBMaterialSamples=len(outside),outsideSamplePoints_mm=outside))
    if d.snapshots.hasPendingSnapshot:
        d.snapshots.add()
    for side, bx, tx in [('L',-65,0),('R',35,160)]:
        o = next(o for o in root.occurrences if o.component.name.startswith('Battery_'+side+'_30x20'))
        b = o.bRepBodies.item(0).boundingBox
        assert abs(b.minPoint.x*10-(tx+bx)) < 1e-6 and abs(b.minPoint.y*10+50) < 1e-6 and abs(b.minPoint.z*10+8) < 1e-6, 'Battery position lost during timeline recompute'
    issues = [t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage]
    assert not issues, str(issues)
    assert doc.save('Placed provisional battery envelopes and external screw axes. No actual part interference certification.')
    ex = d.exportManager
    assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/'+NAME+'.f3d'))
    for side in ('L','R'):
        c = next(c for c in d.allComponents if c.name.startswith('Battery_'+side+'_30x20'))
        assert ex.execute(ex.createSTEPExportOptions(BASE+'cad/design/'+NAME+'_Battery_'+side+'_LOCAL.step',c))
    report = dict(name=NAME,id=doc.dataFile.id,date='2026-11-07',status='PROVISIONAL_NOT_FOR_MANUFACTURE',coordinateSystem='PCB underside z=0, each U1 XY origin; right display only +160 mm X',summary=summary,timelineIssues=issues,limitations=['Perimeter sampling is not exact containment or populated-board collision detection.','Battery allowance is a design assumption, not a battery swelling specification. Connector and wire routing are unresolved.','External screw axes imply expanded case planform. No case walls or screw solids exist.','COROPIT absolute placement, resin shell, antenna and MCU clearances remain unresolved.','STEP exports are component-local body geometry; use JSON/F3D for assembly placement.'])
    with open(BASE+'cad/design/'+NAME+'.json','w',encoding='utf-8') as f:
        json.dump(report,f,ensure_ascii=False,indent=2)
    a.activeViewport.fit()
    print(json.dumps(report))
