"""Fusion MCP. Separate fastening candidate with recessed M2 socket-cap heads."""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'
NAME='left_case_fastening_v03_NOT_FOR_MANUFACTURE'

def run(_context: str):
    a=adsk.core.Application.get();project=next(p for p in a.data.dataProjects if p.name=='roba-v3-lp-cnc-case');folder=next(f for f in project.rootFolder.dataFolders if f.name=='02_design')
    assert not any(f.name==NAME for f in folder.dataFiles),'Fastening candidate already exists'
    doc=next(x for x in a.documents if x.dataFile and x.dataFile.name=='left_case_structure_cnc_v02_NOT_FOR_MANUFACTURE');assert not doc.isModified
    doc.activate();assert doc.saveAs(NAME,folder,'Provisional M2x12 socket-cap screw seats and blind-hole depth; not a released fastener specification.','')
    d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    lower=next(c for c in d.allComponents if c.name=='Lower_L_FROM_PCB_OUTLINE_PROVISIONAL')
    upper=next(c for c in d.allComponents if c.name=='Upper_L_PERIMETER_ONLY_NO_SWITCH_PLATE')
    axes=json.load(open(BASE+'cad/design/left_case_structure_v01_NOT_FOR_MANUFACTURE.json',encoding='utf-8'))['screwAxesXY_mm']
    d.userParameters.add('head_seat_depth',adsk.core.ValueInput.createByString('2.2 mm'),'mm','Provisional 2 mm high socket cap + 0.2 mm recess')
    s=lower.sketches.add(lower.xYConstructionPlane)
    for x,y in axes:
        circle=s.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(x/10,y/10,0),.21);circle.isFixed=True
    profiles=adsk.core.ObjectCollection.create()
    for p in s.profiles:profiles.add(p)
    before=lower.bRepBodies.item(0).volume*1000
    e=lower.features.extrudeFeatures.addSimple(profiles,adsk.core.ValueInput.createByString('head_seat_depth'),adsk.fusion.FeatureOperations.CutFeatureOperation);e.name='Four_D4p2_head_seats_depth_2p2';s.isLightBulbOn=False
    expected_removed=4*math.pi*((4.2/2)**2-(2.2/2)**2)*2.2
    assert abs(before-lower.bRepBodies.item(0).volume*1000-expected_removed)<.001
    # Extend cylindrical pilot reservation; explicit thread depth and drill-tip
    # geometry must still be specified in the final drawing.
    d.userParameters.itemByName('M2_pilot_depth').expression='4.5 mm'
    assert d.computeAll()
    entities=adsk.core.ObjectCollection.create()
    for o in root.occurrences:entities.add(o)
    ii=d.createInterferenceInput(entities);ii.areCoincidentFacesIncluded=False;rr=d.analyzeInterference(ii);assert rr.count==0
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    assert doc.save('M2x12 candidate: heads recessed 0.2 mm nominal, 3.7 mm projection into upper, 0.8 mm pilot-end clearance.')
    ex=d.exportManager;assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/'+NAME+'.f3d'))
    for c,label in [(lower,'Lower_L'),(upper,'Upper_L_perimeter_only')]:assert ex.execute(ex.createSTEPExportOptions(BASE+'cad/design/'+NAME+'_'+label+'_LOCAL.step',c))
    report=dict(name=NAME,id=doc.dataFile.id,date='2026-11-07',candidate=dict(screw='M2 x 12 socket cap, pitch 0.4 mm, dimensional comparison only',nominalHeadDiameter_mm=3.8,nominalHeadHeight_mm=2,headSeatDiameter_mm=4.2,headSeatDepth_mm=2.2,headRecess_mm=.2,nominalProjectionPastSeam_mm=3.7,pilotCylindricalDepth_mm=4.5,nominalPilotEndClearance_mm=.8,pilotEndCap_mm=1,nominalBossRadialWallAtSeat_mm=.9),solidInterferences=rr.count,collisionSet='lower/upper/unpopulated public PCB/battery allowance; screw threads not modeled',analyticalSeatRemoval_mm3=expected_removed,timelineIssues=issues,limitations=['Screw is a dimensional candidate; no purchase or grade/coating/threadlocker specification.','3.7 mm is geometric projection, not verified full thread engagement; thread lead/chamfer/drill tip/tolerances remain.','Blind-hole end cap 1 mm and counterbore sidewall 0.9 mm require DFM and strength review.','No locating feature, final preload/torque, switch plate, ports or RF window.','No populated-board or physical assembly validation.'])
    with open(BASE+'cad/design/'+NAME+'.json','w',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    a.activeViewport.fit();print(json.dumps(report))
