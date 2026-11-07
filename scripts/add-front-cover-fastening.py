"""Fusion MCP: provisional two-screw front attachment for the nonmetal MCU cover."""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'


def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE' and not doc.dataFile.isReadOnly
    upper=next(o.component for o in root.occurrences if o.component.name.startswith('Upper_L_'))
    cap=next(o.component for o in root.occurrences if o.component.name.startswith('MCU_RAISED_'))
    assert not any(f.name=='Cover_front_M1p6_pilots_D1p25_depth3p2' for f in upper.features.extrudeFeatures)
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/checkpoints/v05_choc_references_before_cover_mount.f3d'))
    before=dict(upper=upper.bRepBodies.item(0).volume*1000,cover=cap.bRepBodies.item(0).volume*1000)
    axes=[(-8,3.8),(8,3.8)]
    def p(x,y):return adsk.core.Point3D.create(x/10,y/10,0)
    def plane(c,z):
        i=c.constructionPlanes.createInput();i.setByOffset(c.xYConstructionPlane,adsk.core.ValueInput.createByString(str(z)+' mm'))
        v=c.constructionPlanes.add(i);v.isLightBulbOn=False;return v
    def circles(c,z,diam):
        s=c.sketches.add(plane(c,z))
        for x,y in axes:s.sketchCurves.sketchCircles.addByCenterRadius(p(x,y),diam/20).isFixed=True
        return s
    def rects(c,z):
        s=c.sketches.add(plane(c,z))
        for b in [(-9.3,1.6,-6.2,3.8),(6.2,1.6,9.3,3.8)]:
            for v in s.sketchCurves.sketchLines.addTwoPointRectangle(p(*b[:2]),p(*b[2:])):v.isFixed=True
        return s
    def profiles(s):
        coll=adsk.core.ObjectCollection.create()
        for pr in s.profiles:coll.add(pr)
        return coll
    def make(c,s,h,name):
        e=c.features.extrudeFeatures.addSimple(profiles(s),adsk.core.ValueInput.createByString(str(h)+' mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        e.name=name;s.isLightBulbOn=False;return e
    def join(c,target,name):
        coll=adsk.core.ObjectCollection.create()
        for b in c.bRepBodies:
            if b!=target:coll.add(b)
        i=c.features.combineFeatures.createInput(target,coll);i.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation
        e=c.features.combineFeatures.add(i);e.name=name
    def cut(c,s,h,name):
        i=c.features.extrudeFeatures.createInput(profiles(s),adsk.fusion.FeatureOperations.CutFeatureOperation)
        i.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(str(h)+' mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        i.participantBodies=[c.bRepBodies.item(0)]
        e=c.features.extrudeFeatures.add(i);e.name=name;s.isLightBulbOn=False
    # Upper is translated -1 mm in the assembly; its local Z is global Z +1.
    original=upper.bRepBodies.item(0)
    make(upper,circles(upper,1,3.6),4.5,'Cover_front_bosses_D3p6_GLOBAL_Z0_to4p5')
    join(upper,original,'Join_cover_mount_bosses_to_upper_only')
    cut(upper,circles(upper,2.3,1.25),3.2,'Cover_front_M1p6_pilots_D1p25_depth3p2')
    original=cap.bRepBodies.item(0)
    make(cap,circles(cap,4.5,3.6),3.5,'Cover_front_feet_D3p6_seatZ8p0')
    make(cap,rects(cap,6.8),1.2,'Bridges_outside_USB_12mm_access')
    join(cap,original,'Join_cover_front_feet_and_bridges')
    cut(cap,circles(cap,4.5,1.8),6,'Cover_M1p6_clearance_D1p8')
    cut(cap,circles(cap,8,3.8),3,'Open_head_clearance_at_front_lid_edge_D3p8')
    cap.name='MCU_RAISED_SKIRT_COVER_FRONT_M1p6_PROVISIONAL'
    assert upper.bRepBodies.count==1 and cap.bRepBodies.count==1
    d.computeAll();issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    entities=adsk.core.ObjectCollection.create()
    for o in root.occurrences:
        if o.component.name.startswith(('Upper_L_','Lower_L_','MCU_RAISED_','Battery_L_','PCB_L_','XIAO_KEY_SIDE_ENVELOPE_','USB_CABLE_')):entities.add(o)
    # Cable overlaps the MCU connector intentionally. Exclude only that pair after inspection.
    ii=d.createInterferenceInput(entities);ii.areCoincidentFacesIncluded=False;rr=d.analyzeInterference(ii)
    hits=[dict(first=r.entityOne.parentComponent.name,second=r.entityTwo.parentComponent.name,volume_mm3=r.interferenceBody.volume*1000) for r in rr]
    out=dict(date='2026-11-08',axesXY_mm=axes,bossDiameter_mm=3.6,coverSeatZ_mm=4.5,headSeatZ_mm=8,
             capClearanceHole_mm=1.8,tapCandidate='M1.6 x 0.35',pilot_mm=1.25,pilotDepth_mm=3.2,
             screwCandidate='M1.6 x 6; head D3.2 x H1.6 assumed, procurement pending',
             nominalProjectionIntoUpper_mm=2.5,nominalPilotBottomGap_mm=.7,capGrip_mm=3.5,
             headReliefDiameter_mm=3.8,headReliefOpenToOuterEdge=True,
             volumesBefore_mm3=before,volumesAfter_mm3=dict(upper=upper.bRepBodies.item(0).volume*1000,cover=cap.bRepBodies.item(0).volume*1000),
             initialInterferences=hits,timelineIssues=issues,
             limitations=['Provisional front fastening; rear cantilever stiffness and material/process unverified',
                          'Geometric projection is not guaranteed full thread engagement; lead, drill point and chamfers remain',
                          'Screw head dimensions, grade, torque, fit and thread serviceability not finalized'])
    json.dump(out,open(BASE+'docs/cover-front-fastening-verification.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False))
