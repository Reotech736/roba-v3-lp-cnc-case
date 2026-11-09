"""One-time v25: prototype case-mounted nonmetal cable restraint bracket.

Separate verification/save required. Does not modify PCB or source references.
"""
import adsk.core,adsk.fusion,json,math
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')


def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber==25 and not doc.isModified
    assert (BASE/'cad/design/checkpoints/v05_cloud_v25_before_case_wire_bracket.f3d').exists()
    report=json.loads((BASE/'docs/case-wire-bracket-preflight.json').read_text(encoding='utf-8'))
    assert not report['bracketCollisions'] and all(abs(p['majorCylinderStockFraction']-1)<1e-6 for p in report['pilotStock'])
    before=[{'name':o.component.name,'path':o.fullPathName,'matrix':list(o.transform2.asArray()),'volumes':[b.volume*1000 for b in o.component.bRepBodies],'visible':o.isLightBulbOn} for o in root.allOccurrences]
    (BASE/'docs/case-wire-bracket-baseline.json').write_text(json.dumps(before,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lower=next(o for o in root.occurrences if o.component.name.startswith('Lower_L_'))
    upper=next(o for o in root.occurrences if o.component.name.startswith('Upper_L_'))
    assert abs(lower.transform2.translation.z*10+11.5)<1e-7 and abs(upper.transform2.translation.z*10+1)<1e-7
    oldVolumes={o.component.name:o.component.bRepBodies.item(0).volume*1000 for o in [lower,upper]}
    mgr=adsk.fusion.TemporaryBRepManager.get();union=adsk.fusion.BooleanTypes.UnionBooleanType;difference=adsk.fusion.BooleanTypes.DifferenceBooleanType
    def point(p):return adsk.core.Point3D.create(*[v/10 for v in p])
    def box(b):
        x0,y0,z0,x1,y1,z1=b
        return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(point([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2]),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
    def cyl(x,y,z0,z1,r):return mgr.createCylinderOrCone(point([x,y,z0]),r/10,point([x,y,z1]),r/10)
    def plane(c,z):
        i=c.constructionPlanes.createInput();i.setByOffset(c.xYConstructionPlane,adsk.core.ValueInput.createByString(f'{z} mm'));p=c.constructionPlanes.add(i);p.isLightBulbOn=False;return p
    def cutProfile(c,s,h,name):
        profiles=adsk.core.ObjectCollection.create()
        for p in s.profiles:profiles.add(p)
        i=c.features.extrudeFeatures.createInput(profiles,adsk.fusion.FeatureOperations.CutFeatureOperation)
        i.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(f'{h} mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection);i.participantBodies=[c.bRepBodies.item(0)]
        f=c.features.extrudeFeatures.add(i);f.name=name;s.isLightBulbOn=False
    def rectFeature(c,b,zOffset,operation,name):
        x0,y0,z0,x1,y1,z1=b;s=c.sketches.add(plane(c,z0+zOffset));s.name=name+'_profile'
        for line in s.sketchCurves.sketchLines.addTwoPointRectangle(point([x0,y0,0]),point([x1,y1,0])):line.isFixed=True
        if operation==adsk.fusion.FeatureOperations.CutFeatureOperation:cutProfile(c,s,z1-z0,name)
        else:
            f=c.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString(f'{z1-z0} mm'),operation);f.name=name;s.isLightBulbOn=False
    rectFeature(lower.component,report['lowerBackingGlobal_mm'],11.5,adsk.fusion.FeatureOperations.JoinFeatureOperation,'Case_wire_bracket_external_backing_WITHIN_EXISTING_MAX_BOUNDS')
    rectFeature(lower.component,report['lowerReliefGlobal_mm'],11.5,adsk.fusion.FeatureOperations.CutFeatureOperation,'Case_wire_bracket_removable_lower_clearance_0p3')
    s=upper.component.sketches.add(upper.component.xYConstructionPlane);s.name='Case_wire_bracket_two_M1p6_axes'
    for x,y in report['axesXY_mm']:s.sketchCurves.sketchCircles.addByCenterRadius(point([x,y,0]),.0625).isFixed=True
    cutProfile(upper.component,s,3.6,'Case_wire_bracket_M1p6_pilots_D1p25_depth3p6_THREAD_NOT_MODELED')
    battery=next(o for o in root.occurrences if o.component.name=='BATTERY_ASSEMBLY_CELL42_WIRE40_PROVISIONAL')
    studies=next(o for o in root.allOccurrences if o.component.name=='CLEARANCE_STUDIES_NOT_PARTS')
    occ=battery.component.occurrences.addNewComponent(adsk.core.Matrix3D.create());c=occ.component;c.name='WIRE_STRAIN_RELIEF_CASE_BRACKET_NONMETAL_PROVISIONAL'
    stock=box(report['bracketStockBoxesGlobal_mm'][0])
    for b in report['bracketStockBoxesGlobal_mm'][1:]:assert mgr.booleanOperation(stock,box(b),union)
    for x,y in report['axesXY_mm']:assert mgr.booleanOperation(stock,cyl(x,y,-3,-.9,.9),difference)
    for slot in report['tieSlots']:
        vx,vy=slot['longAxisXY'];cx,cy=slot['centerXY_mm']
        tool=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(point([cx,cy,-4.5]),adsk.core.Vector3D.create(vx,vy,0),adsk.core.Vector3D.create(-vy,vx,0),.22,.11,.2))
        assert mgr.booleanOperation(stock,tool,difference)
    def addBody(comp,b,name):
        f=comp.features.baseFeatures.add();f.name=name;assert f.startEdit();comp.bRepBodies.add(b,f);assert f.finishEdit()
    addBody(c,stock,'Nonmetal_cradle_beam_two_tie_slots_and_upper_mount_stock')
    target=c.bRepBodies.item(0)
    wire=next(o for o in root.allOccurrences if o.component.name=='BATTERY_WIRE_ROUTE_D3_DIRECT_SOLDER_B1_40mm_R3_LOOP_NOT_PART')
    sketch=wire.component.sketches.item(0);curves=adsk.core.ObjectCollection.create()
    for curve in sketch.sketchCurves:curves.add(curve.createForAssemblyContext(wire))
    path=adsk.fusion.Path.create(curves,adsk.fusion.ChainedCurveOptions.noChainedCurves);assert path
    inp=c.features.pipeFeatures.createInput(path,adsk.fusion.FeatureOperations.NewBodyFeatureOperation);inp.sectionSize=adsk.core.ValueInput.createByString('3.4 mm')
    toolFeature=c.features.pipeFeatures.add(inp);toolFeature.name='D3p4_R3_groove_tool_for_D3_bundle'
    tools=adsk.core.ObjectCollection.create()
    for b in toolFeature.bodies:tools.add(b)
    ci=c.features.combineFeatures.createInput(target,tools);ci.operation=adsk.fusion.FeatureOperations.CutFeatureOperation
    c.features.combineFeatures.add(ci).name='Open_cradle_groove_0p2_radial_allowance_NOT_A_COMPRESSION_SPEC'
    assert c.bRepBodies.count==1 and c.bRepBodies.item(0).isSolid
    occ.isLightBulbOn=True
    # Study envelope for the two independent M1.6 x4 fasteners. Thread is not modeled.
    screwOcc=studies.component.occurrences.addNewComponent(adsk.core.Matrix3D.create());sc=screwOcc.component;sc.name='WIRE_BRACKET_M1p6x4_TWO_SCREW_ENVELOPES_NOT_PARTS'
    for x,y in report['axesXY_mm']:
        body=cyl(x,y,-2.2,1.8,.8);assert mgr.booleanOperation(body,cyl(x,y,-3.8,-2.2,1.5),union);addBody(sc,body,'M1p6x4_shank_and_D3x1p6_head')
    screwOcc.isLightBulbOn=False
    tieOcc=studies.component.occurrences.addNewComponent(adsk.core.Matrix3D.create());tc=tieOcc.component;tc.name='WIRE_BRACKET_TIE_HEAD_AND_UNDERSIDE_BAND_ASSUMED_NOT_PARTS'
    addBody(tc,box([3.2,-19.6,-4,6.8,-16.3,-1.2]),'Assumed_head_3p6x3p3x2p8_NOT_COMPLETE_TIE_PATH')
    slots=report['tieSlots'];cx=sum(s['centerXY_mm'][0] for s in slots)/2;cy=sum(s['centerXY_mm'][1] for s in slots)/2;vx,vy=slots[0]['longAxisXY']
    band=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(point([cx,cy,-5.3]),adsk.core.Vector3D.create(vx,vy,0),adsk.core.Vector3D.create(-vy,vx,0),.18,.52,.08));addBody(tc,band,'Assumed_tie_band_0p8_below_cradle')
    tieOcc.isLightBulbOn=False
    old=next(o for o in root.allOccurrences if o.component.name.startswith('PCB_WIRE_STRAIN_RELIEF_BOND_FOOTPRINT_'))
    old.component.name='RETIRED_PCB_BONDING_ALTERNATIVE_'+old.component.name;old.isLightBulbOn=False
    assert d.computeAll()
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    # Preserve every previous transform and every non-case component volume.
    after={o.fullPathName:o for o in root.allOccurrences}
    for row in before:
        o=after.get(row['path'])
        if o is None:
            assert row['name'].startswith('PCB_WIRE_STRAIN_RELIEF_BOND_FOOTPRINT_')
            o=next(o for o in root.allOccurrences if o.component.name=='RETIRED_PCB_BONDING_ALTERNATIVE_'+row['name'])
        assert max(abs(a-b) for a,b in zip(row['matrix'],o.transform2.asArray()))<1e-8
        if o.component not in [upper.component,lower.component]:assert all(abs(v-b.volume*1000)<1e-5 for v,b in zip(row['volumes'],o.component.bRepBodies)),row['name']
    out={'date':'2026-11-09','baselineCloudVersion':25,'saved':False,'changedCases':[upper.component.name,lower.component.name],
         'caseVolumesBefore_mm3':oldVolumes,'caseVolumesAfter_mm3':{o.component.name:o.component.bRepBodies.item(0).volume*1000 for o in [lower,upper]},
         'bracketVolume_mm3':c.bRepBodies.item(0).volume*1000,'bracketSolidCount':c.bRepBodies.count,'axesXY_mm':report['axesXY_mm'],
         'caseMount':'Two independent M1.6x4 candidate screws from below; upper D1.25x3.6 pilots',
         'wireContact':'D3.4 open saddle for D3 comparison bundle; adjustable tie required, not modeled as a qualified preload',
         'tieInterface_mm':[2.2,1.1],'tieHeadEnvelopeAssumed_mm':[3.6,3.3,2.8],'allPreviousTransformsPreserved':True,
         'nonCaseOriginalVolumesPreserved':True,'timelineIssues':issues,'PCBAdhesiveRequired':False,
         'limitations':['Nonmetal material, printed/machined tolerances, rib stiffness, friction and tie force unqualified.',
             'Tie-head box and underside band are clearance studies, not a complete installed cable tie.',
             'Local lower outer wall is nominal1.1mm and needs structural/DFM review.',
             'Actual wire diameters and insulation remain unconfirmed.']}
    (BASE/'docs/case-wire-bracket-development.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out))
