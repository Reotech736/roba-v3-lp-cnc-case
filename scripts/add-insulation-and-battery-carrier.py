"""Fusion MCP: provisional dielectric stacks, removable cell carrier and routing study.

Creates separate candidate/reference components; does not cut or edit source/case bodies.
No adhesive, dielectric or carrier material has been qualified or selected.
"""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'
NAME='left_case_two_stands_v05_NOT_FOR_MANUFACTURE'


def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.name==NAME and not doc.isModified and not doc.dataFile.isReadOnly and doc.dataFile.versionNumber==10
    assert not any(o.component.name.startswith('BATTERY_REMOVABLE_CARRIER_') for o in root.occurrences)
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/checkpoints/v05_cloud_v10_before_internal_retention.f3d'))
    initial={o.component.name:o.component.bRepBodies.item(0).volume*1000 for o in root.occurrences if o.component.name.startswith(('Lower_L_','Upper_L_','MCU_RAISED_'))}
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
    # 0.2 mm is a total stack allowance, not a selected film/adhesive specification.
    supports=json.load(open(BASE+'cad/design/'+NAME+'.json',encoding='utf-8'))['edgeSupportsXY_mm']
    pad=comp('PCB_SUPPORT_INSULATION_STACK_0p2_MATERIAL_PENDING')
    boxes(pad.component,-.2,.2,supports,'Four_dielectric_support_stack_allowances')
    assert pad.component.bRepBodies.count==4
    tray=comp('BATTERY_REMOVABLE_CARRIER_32p6x22p6_PROVISIONAL_NONMETAL')
    c=tray.component;s=c.sketches.add(plane(c,-9.3));roundrect(s,-66.3,-51.3,32.6,22.6,1.5)
    target=extrude(c,s,.5,'Carrier_floor_0p5').bodies.item(0)
    s=c.sketches.add(plane(c,-8.8));roundrect(s,-66.3,-51.3,32.6,22.6,1.5);roundrect(s,-65.5,-50.5,31,21,.7)
    rings=[p for p in s.profiles if p.profileLoops.count==2];assert len(rings)==1
    walls=extrude(c,s,2,'Low_side_guards_0p8_not_a_clamp',rings[0]).bodies.item(0)
    tools=adsk.core.ObjectCollection.create();tools.add(walls)
    i=c.features.combineFeatures.createInput(target,tools);i.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation
    c.features.combineFeatures.add(i).name='Join_carrier_floor_and_guards'
    # Open all four sides provisionally until the actual cell lead exit is known.
    s=c.sketches.add(plane(c,-8.8))
    for b in [(-54,-51.5,-46,-50.3),(-54,-29.7,-46,-28.5),(-66.5,-43,-65.3,-37),(-34.7,-43,-33.5,-37)]:rect(s,b)
    i=c.features.extrudeFeatures.createInput(all_profiles(s),adsk.fusion.FeatureOperations.CutFeatureOperation)
    i.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('2 mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
    i.participantBodies=[c.bRepBodies.item(0)];c.features.extrudeFeatures.add(i).name='Four_open_wire_and_pull_tab_exits';s.isLightBulbOn=False
    assert c.bRepBodies.count==1
    base_tape=comp('CARRIER_BASE_REMOVABLE_ADHESIVE_0p2_ALLOWANCE')
    boxes(base_tape.component,-9.5,.2,[(-61,-49,-55,-31),(-45,-49,-39,-31)],'Two_carrier_fixing_stack_allowances')
    cell_tape=comp('CELL_REMOVABLE_ADHESIVE_0p2_ALLOWANCE')
    boxes(cell_tape.component,-8.8,.2,[(-61,-47,-55,-33),(-45,-47,-39,-33)],'Two_cell_fixing_stack_allowances')
    cell=comp('BATTERY_CELL_NOMINAL_30x20x4_USER_APPROX')
    boxes(cell.component,-8.6,4,[(-65,-50,-35,-30)],'Nominal_cell_not_terminals_or_swelling')
    pull=comp('CELL_ADHESIVE_PULL_TAB_ACCESS_RESERVATION_NOT_PART')
    boxes(pull.component,-8.8,.2,[(-39,-42,-27,-38)],'Assumed_pull_tab_access_from_positive_X');pull.isLightBulbOn=False
    # B1 from public-v2 B.Cu footprint; exact matching STEP was not obtained.
    board=json.load(open(BASE+'cad/design/pcb_v2_layout_input.json',encoding='utf-8'))['boards'][0]
    u=next(f for f in board['footprints'] if f['reference']=='U1');b=next(f for f in board['footprints'] if f['reference']=='B1')
    bx=float(b['at'][0])-float(u['at'][0]);by=float(u['at'][1])-float(b['at'][1])
    header=comp('B1_JST_PH_SMD_DATASHEET_RESERVATION_NOT_DETAILED_CAD')
    boxes(header.component,-5.5,5.5,[(bx-4.1,by-1.75,bx+4.1,by+7.45)],'Backside_header_height5p5_and_footprint_extent');header.isLightBulbOn=False
    plug=comp('B1_MATING_PLUG_ACCESS_ASSUMED_8x6x4_NOT_PART')
    boxes(plug.component,-4.75,4,[(bx-4,by+7.45,bx+4,by+13.45)],'Assumed_mating_plug_and_grip_space');plug.isLightBulbOn=False
    # Route around the connector from its positive-Y mating side; endpoints are not terminals.
    route=[[-33.8,-40,-6.6],[-12,-32,-4.6],[-8,-26,-3.5],[-8,-8,-3.5],[bx,-6,-2.75]]
    mgr=adsk.fusion.TemporaryBRepManager.get()
    def pt(x):return adsk.core.Point3D.create(*[v/10 for v in x])
    body=mgr.createSphere(pt(route[0]),.1)
    for first,last in zip(route,route[1:]):
        cylinder=mgr.createCylinderOrCone(pt(first),.1,pt(last),.1)
        assert mgr.booleanOperation(body,cylinder,adsk.fusion.BooleanTypes.UnionBooleanType)
        sphere=mgr.createSphere(pt(last),.1)
        assert mgr.booleanOperation(body,sphere,adsk.fusion.BooleanTypes.UnionBooleanType)
    wire=comp('BATTERY_WIRE_ROUTE_D2_ASSUMED_CLEARANCE_NOT_PART')
    feature=wire.component.features.baseFeatures.add();feature.name='Reproducible_polyline_capsule_route_reservation'
    assert feature.startEdit();wire.component.bRepBodies.add(body,feature);assert feature.finishEdit();wire.isLightBulbOn=False
    assert wire.component.bRepBodies.count==1
    # Retain old installation allowance hidden; it intentionally contains new parts.
    next(o for o in root.occurrences if o.component.name.startswith('Battery_L_ALLOWANCE_')).isLightBulbOn=False
    assert d.computeAll()
    for o in root.occurrences:
        if o.component.name in initial:assert abs(o.component.bRepBodies.item(0).volume*1000-initial[o.component.name])<.0001
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    length=sum(math.dist(a,b) for a,b in zip(route,route[1:]))
    out=dict(date='2026-11-08',caseVolumesUnchanged=True,pcbInsulationStack_mm=.2,pcbSupportRectsXY_mm=supports,
             carrier=dict(outerXY_mm=[32.6,22.6],innerXY_mm=[31,21],floor_mm=.5,wall_mm=.8,wallHeight_mm=2,boundsGlobal_mm=[[-66.3,-51.3,-9.3],[-33.7,-28.7,-6.8]]),
             nominalCellBoundsGlobal_mm=[[-65,-50,-8.6],[-35,-30,-4.6]],adhesiveLayers_mm=[.2,.2],
             connector=dict(reference='B1',part='JST S2B-PH-SM4-TB',layer='B.Cu',originXY_mm=[bx,by],reservedHeight_mm=5.5,nominalBackingGap_mm=.3,source='https://www.jst-mfg.com/product/pdf/eng/ePH.pdf'),
             wireRouteCenters_mm=route,wireBundleEnvelopeDiameter_mm=2,wireRouteLength_mm=length,assumedAdditionalServiceSlack_mm=15,
             wireLengthComparison_mm=length+15,timelineIssues=issues,
             limitations=['All dielectric/adhesive/carrier materials and retention strength are unselected and untested',
             'Cell dimensions are approximate; terminals, leads and swelling are not represented by its nominal box',
             'Carrier guards are low and do not clamp the pouch; adhesive removal procedure needs a real product choice',
             'Public v2 B1 footprint is provisional for actual PCB; exact matching connector STEP was not obtained',
             'Wire route and plug access are design reservations, not actual wire/connector geometry or a bend-radius specification',
             'Stand hinge/adhesive thickness and actual battery lead direction/length await user confirmation'])
    json.dump(out,open(BASE+'docs/internal-retention-development.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False))
