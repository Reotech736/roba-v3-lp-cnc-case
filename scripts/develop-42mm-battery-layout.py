"""Fusion MCP: new 42x20x5 cell carrier candidate with a 40 mm lead budget.

Run once on v15; validate before saving. No source/case geometry edits.
"""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'

def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE' and doc.dataFile.versionNumber==15 and not doc.dataFile.isReadOnly
    assert not any(o.component.name.startswith('BATTERY_CELL_NOMINAL_42') for o in root.occurrences)
    initial={o.component.name:o.component.bRepBodies.item(0).volume*1000 for o in root.occurrences if o.component.name.startswith(('Lower_L_','Upper_L_','MCU_RAISED_'))}
    assert abs(initial['Lower_L_FROM_PCB_OUTLINE_PROVISIONAL']-35834.86113140607)<1e-4
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/checkpoints/v05_cloud_v15_before_42mm_battery.f3d'))
    old=[o for o in root.occurrences if o.component.name.startswith(('BATTERY_REMOVABLE_CARRIER_','CARRIER_BASE_REMOVABLE_','CELL_REMOVABLE_ADHESIVE_','BATTERY_CELL_NOMINAL_','CELL_ADHESIVE_PULL_TAB_','BATTERY_WIRE_ROUTE_','BATTERY_SERVICE_SLACK_'))]
    assert len(old)==7
    def comp(name):
        o=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());o.component.name=name;return o
    def p(x,y):return adsk.core.Point3D.create(x/10,y/10,0)
    def plane(c,z):
        i=c.constructionPlanes.createInput();i.setByOffset(c.xYConstructionPlane,adsk.core.ValueInput.createByString(str(z)+' mm'))
        pl=c.constructionPlanes.add(i);pl.isLightBulbOn=False;return pl
    def rect(s,box):
        for v in s.sketchCurves.sketchLines.addTwoPointRectangle(p(*box[:2]),p(*box[2:])):v.isFixed=True
    def all_profiles(s):
        coll=adsk.core.ObjectCollection.create()
        for pr in s.profiles:coll.add(pr)
        return coll
    def extrude(c,s,h,name,profile=None):
        e=c.features.extrudeFeatures.addSimple(profile or all_profiles(s),adsk.core.ValueInput.createByString(str(h)+' mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        e.name=name;s.isLightBulbOn=False;return e
    def boxes(c,z,h,rectangles,name):
        s=c.sketches.add(plane(c,z))
        for b in rectangles:rect(s,b)
        return extrude(c,s,h,name)
    def roundrect(s,x,y,w,h,r):
        def q(u,v):return p(x+u,y+v)
        for first,last in [((r,0),(w-r,0)),((w,r),(w,h-r)),((w-r,h),(r,h)),((0,h-r),(0,r))]:
            s.sketchCurves.sketchLines.addByTwoPoints(q(*first),q(*last)).isFixed=True
        for first,mid,last in [((w-r,0),(w-r+r/math.sqrt(2),r-r/math.sqrt(2)),(w,r)),((w,h-r),(w-r+r/math.sqrt(2),h-r+r/math.sqrt(2)),(w-r,h)),((r,h),(r-r/math.sqrt(2),h-r+r/math.sqrt(2)),(0,h-r)),((0,r),(r-r/math.sqrt(2),r-r/math.sqrt(2)),(r,0))]:
            s.sketchCurves.sketchArcs.addByThreePoints(q(*first),q(*mid),q(*last)).isFixed=True
    tray=comp('BATTERY_REMOVABLE_CARRIER_44p6x22p6_CELL42_PROVISIONAL_NONMETAL')
    c=tray.component;s=c.sketches.add(plane(c,-9.3));roundrect(s,-56.3,-51.3,44.6,22.6,1.5)
    target=extrude(c,s,1,'Carrier_floor_1p0_CELL42').bodies.item(0)
    s=c.sketches.add(plane(c,-8.3));roundrect(s,-56.3,-51.3,44.6,22.6,1.5);roundrect(s,-55.5,-50.5,43,21,.7)
    ring=[p for p in s.profiles if p.profileLoops.count==2];assert len(ring)==1
    wall=extrude(c,s,2,'Low_side_guards_0p8_not_a_pouch_clamp',ring[0]).bodies.item(0)
    tools=adsk.core.ObjectCollection.create();tools.add(wall)
    ci=c.features.combineFeatures.createInput(target,tools);ci.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation;c.features.combineFeatures.add(ci)
    s=c.sketches.add(plane(c,-8.3))
    # Open corners for unknown exact lead corner, plus mid-side removal-tab access.
    for b in [(-57,-52,-52.5,-47.5),(-15.5,-52,-11,-47.5),(-57,-32.5,-52.5,-28),(-15.5,-32.5,-11,-28),(-38,-51.6,-30,-50.2),(-38,-29.8,-30,-28.4),(-56.6,-43,-55.2,-37),(-12.8,-43,-11.4,-37)]:rect(s,b)
    ci=c.features.extrudeFeatures.createInput(all_profiles(s),adsk.fusion.FeatureOperations.CutFeatureOperation)
    ci.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('2 mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
    ci.participantBodies=[target];c.features.extrudeFeatures.add(ci).name='Corner_wire_and_mid_side_tab_openings';s.isLightBulbOn=False
    assert c.bRepBodies.count==1
    base=comp('CARRIER_BASE_REMOVABLE_ADHESIVE_0p2_CELL42_ALLOWANCE')
    boxes(base.component,-9.5,.2,[(-50,-49,-44,-31),(-24,-49,-18,-31)],'Base_stack_0p2_material_pending')
    tape=comp('CELL_REMOVABLE_ADHESIVE_0p2_CELL42_ALLOWANCE')
    boxes(tape.component,-8.3,.2,[(-50,-47,-44,-33),(-24,-47,-18,-33)],'Cell_stack_0p2_material_pending')
    cell=comp('BATTERY_CELL_NOMINAL_42x20x5_USER_TARGET')
    boxes(cell.component,-8.1,5,[(-55,-50,-13,-30)],'Requested_42x20x5_not_seals_leads_or_swelling')
    install=comp('CELL42_INSTALLATION_SPACE_43x21x5p5_NOT_PART')
    boxes(install.component,-8.1,5.5,[(-55.5,-50.5,-12.5,-29.5)],'Provisional_side0p5_top0p5_clearance');install.isLightBulbOn=False
    pull=comp('CELL_ADHESIVE_PULL_TAB_ACCESS_RESERVATION_CELL42_NOT_PART')
    boxes(pull.component,-8.3,.2,[(-19,-42,-5,-38)],'Initial_tab_access_not_full_release_path');pull.isLightBulbOn=False
    route=[[-11.8,-28.8,-5.6],[-8,-24,-3.5],[-8,-8,-3.5],[-1.38934,-6,-2.75]]
    mgr=adsk.fusion.TemporaryBRepManager.get()
    def pt(x):return adsk.core.Point3D.create(*[v/10 for v in x])
    body=mgr.createSphere(pt(route[0]),.15)
    for first,last in zip(route,route[1:]):
        assert mgr.booleanOperation(body,mgr.createCylinderOrCone(pt(first),.15,pt(last),.15),adsk.fusion.BooleanTypes.UnionBooleanType)
        assert mgr.booleanOperation(body,mgr.createSphere(pt(last),.15),adsk.fusion.BooleanTypes.UnionBooleanType)
    wire=comp('BATTERY_WIRE_ROUTE_D3_CELL42_40mm_BUDGET_NOT_PART')
    bf=wire.component.features.baseFeatures.add();assert bf.startEdit();wire.component.bRepBodies.add(body,bf);assert bf.finishEdit();wire.isLightBulbOn=False
    slack=comp('BATTERY_SERVICE_SLACK_SPACE_CELL42_10x10x4_NOT_PART')
    boxes(slack.component,-7,4,[(-10,-40,0,-30)],'Unassigned_space_not_a_proven_slack_loop');slack.isLightBulbOn=False
    for o in old:o.component.name='RETIRED_V15_'+o.component.name;o.isLightBulbOn=False
    assert d.computeAll()
    for o in root.occurrences:
        if o.component.name in initial:assert abs(o.component.bRepBodies.item(0).volume*1000-initial[o.component.name])<1e-4
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    length=sum(math.dist(x,y) for x,y in zip(route,route[1:]));transition=math.dist([-13,-30,-5.6],route[0])
    assert length+transition<40
    out=dict(date='2026-11-08',baselineCloudVersion=15,requestedCell_mm=[42,20,5],leadLengthBudget_mm=40,
        nominalCellBoundsGlobal_mm=[[-55,-50,-8.1],[-13,-30,-3.1]],carrierOuter_mm=[44.6,22.6],carrierInner_mm=[43,21],
        carrierBoundsGlobal_mm=[[-56.3,-51.3,-9.3],[-11.7,-28.7,-6.3]],carrierFloor_mm=1,carrierWall_mm=.8,carrierWallHeight_mm=2,
        installationAllowanceBoundsGlobal_mm=[[-55.5,-50.5,-8.1],[-12.5,-29.5,-2.6]],adhesiveStacks_mm=[.2,.2],
        wireRouteCenters_mm=route,routeLength_mm=length,assumedCornerToRouteTransition_mm=transition,
        nominalConnectionRouteIncludingCorner_mm=length+transition,remainingWireLengthBudget_mm=40-length-transition,
        assumedCellExitCornerGlobal_mm=[-13,-30,-5.6],wireBundleEnvelope_mm=3,metalCaseVolumesUnchanged=True,metalVolumes_mm3=initial,
        carrierVolume_mm3=target.volume*1000,timelineIssues=issues,retiredComponentCount=len(old),
        limitations=['42x20x5 is the requested nominal body target, not confirmed maximum including pouch seams, terminals, protection PCB or swelling',
        'Exit corner, lead vertical position, connector termination and D3 bundle are assumed; actual 40mm measurement endpoints and bend radius need confirmation',
        'Remaining8.88mm is arithmetic budget, not a verified service loop or bend allowance; no extra15mm service requirement is retained',
        '43x21x5.5 installation space is provisional and not a certified battery expansion allowance',
        'Carrier material, adhesive removability, retention strength and electrical insulation are unqualified; no upper pouch clamp'])
    json.dump(out,open(BASE+'docs/battery42-layout-development.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False))
