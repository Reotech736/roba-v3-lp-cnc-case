"""Fusion MCP: provisional reset access and round/slot case locating features."""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'
NAME='left_case_two_stands_v05_NOT_FOR_MANUFACTURE'


def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.name==NAME and not doc.isModified and doc.dataFile.versionNumber==9 and not doc.dataFile.isReadOnly
    assert d.userParameters.itemByName('case_locator_height') is None
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/checkpoints/v05_cloud_v9_before_service_locators.f3d'))
    lower=next(o.component for o in root.occurrences if o.component.name.startswith('Lower_L_'))
    upper=next(o.component for o in root.occurrences if o.component.name.startswith('Upper_L_'))
    cap=next(o.component for o in root.occurrences if o.component.name.startswith('MCU_RAISED_'))
    before={c.name:c.bRepBodies.item(0).volume*1000 for c in [lower,upper,cap]}
    params=[('case_locator_height',1),('case_locator_diameter',1.6),('case_locator_socket_diameter',2),('case_locator_socket_depth',1.2),('case_locator_slot_extra',.6),('reset_access_diameter',2)]
    for name,value in params:d.userParameters.add(name,adsk.core.ValueInput.createByString(str(value)+' mm'),'mm','Provisional fit; machining and physical tolerances pending')
    def p(x,y):return adsk.core.Point3D.create(x/10,y/10,0)
    def plane(c,expression):
        i=c.constructionPlanes.createInput();i.setByOffset(c.xYConstructionPlane,adsk.core.ValueInput.createByString(expression))
        z=c.constructionPlanes.add(i);z.isLightBulbOn=False;return z
    def profiles(s):
        out=adsk.core.ObjectCollection.create()
        for v in s.profiles:out.add(v)
        return out
    def cut(c,s,distance,name):
        i=c.features.extrudeFeatures.createInput(profiles(s),adsk.fusion.FeatureOperations.CutFeatureOperation)
        i.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(distance)),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        i.participantBodies=[c.bRepBodies.item(0)];v=c.features.extrudeFeatures.add(i);v.name=name;s.isLightBulbOn=False
    axes=[(-107.12,-72),(-107.12,-8)]
    target=lower.bRepBodies.item(0);s=lower.sketches.add(plane(lower,'floor_thickness + lower_wall_height'))
    s.name='Two_case_locating_pins_independent_of_screw_axes'
    for x,y in axes:s.sketchCurves.sketchCircles.addByCenterRadius(p(x,y),.08).isFixed=True
    e=lower.features.extrudeFeatures.addSimple(profiles(s),adsk.core.ValueInput.createByString('case_locator_height'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation);e.name='Case_locating_pins_D1p6_H1_PROVISIONAL';s.isLightBulbOn=False
    tools=adsk.core.ObjectCollection.create()
    for b in e.bodies:tools.add(b)
    i=lower.features.combineFeatures.createInput(target,tools);i.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation
    lower.features.combineFeatures.add(i).name='Join_locating_pins_to_lower_only'
    # Upper local Z0 is global seam Z=-1. Slots open toward the lower part.
    s=upper.sketches.add(upper.xYConstructionPlane);s.name='Round_and_Y_relief_slot_for_case_locating'
    s.sketchCurves.sketchCircles.addByCenterRadius(p(*axes[0]),.1).isFixed=True
    x,y=axes[1];r=1;half_extra=.3
    s.sketchCurves.sketchLines.addByTwoPoints(p(x-r,y-half_extra),p(x-r,y+half_extra)).isFixed=True
    s.sketchCurves.sketchArcs.addByThreePoints(p(x-r,y+half_extra),p(x,y+half_extra+r),p(x+r,y+half_extra)).isFixed=True
    s.sketchCurves.sketchLines.addByTwoPoints(p(x+r,y+half_extra),p(x+r,y-half_extra)).isFixed=True
    s.sketchCurves.sketchArcs.addByThreePoints(p(x+r,y-half_extra),p(x,y-half_extra-r),p(x-r,y-half_extra)).isFixed=True
    assert s.profiles.count==2
    cut(upper,s,'case_locator_socket_depth','Case_locator_round_and_slot_pockets_depth1p2')
    # Datum from the imported SKTAAAE010 Body top face, not a hand-entered PCB guess.
    reset=[]
    def walk(o,flag=False):
        flag=flag or 'SKTAAAE010' in o.component.name
        if flag and o.component.name=='Body':
            for b in o.bRepBodies:
                bb=b.boundingBox;reset.append(dict(x=(bb.minPoint.x+bb.maxPoint.x)*5,y=(bb.minPoint.y+bb.maxPoint.y)*5,topZ=bb.maxPoint.z*10))
        for ch in o.childOccurrences:walk(ch,flag)
    walk(next(o for o in root.occurrences if o.component.name.startswith('XIAO_DETAILED_')));assert len(reset)==1
    button=reset[0];s=cap.sketches.add(plane(cap,'7.4 mm'))
    s.name='Reset_service_access_FROM_DETAILED_MCU'
    s.sketchCurves.sketchCircles.addByCenterRadius(p(button['x'],button['y']),.1).isFixed=True
    cut(cap,s,'2 mm','Reset_service_hole_D2_OLD_MCU_POSITION_UNVERIFIED')
    # Probe is a clearance tool; no captive plunger or enforced depression depth.
    probe=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());probe.component.name='RESET_NONCONDUCTIVE_PROBE_D0p8_ACCESS_TOOL_NOT_A_PART'
    s=probe.component.sketches.add(plane(probe.component,str(button['topZ']+.01)+' mm'))
    s.sketchCurves.sketchCircles.addByCenterRadius(p(button['x'],button['y']),.04).isFixed=True
    e=probe.component.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString(str(16-button['topZ']-.01)+' mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    e.name='Reset_probe_clear_path_to_model_button_top';s.isLightBulbOn=False;probe.isLightBulbOn=False
    assert d.computeAll()
    for c in [lower,upper,cap]:assert c.bRepBodies.count==1
    # 2D cross section sampling establishes cavity clearance and residual wall at seam.
    inside=adsk.fusion.PointContainment.PointInsidePointContainment;checks=[]
    for index,(x,y) in enumerate(axes):
        assert lower.bRepBodies.item(0).pointContainment(adsk.core.Point3D.create(x/10,y/10,1.10))==inside
        assert upper.bRepBodies.item(0).pointContainment(adsk.core.Point3D.create(x/10,y/10,.06))!=inside
        assert upper.bRepBodies.item(0).pointContainment(adsk.core.Point3D.create(x/10,y/10,.121))==inside
        for t in [j*math.pi/12 for j in range(24)]:
            xx=x+1.4*math.cos(t);yy=y+1.4*math.sin(t)
            assert upper.bRepBodies.item(0).pointContainment(adsk.core.Point3D.create(xx/10,yy/10,.06))==inside
            checks.append([index,xx,yy])
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    out=dict(date='2026-11-08',locatorsXY_mm=axes,pinDiameter_mm=1.6,pinHeight_mm=1,pinTopGlobalZ_mm=0,
             roundHoleDiameter_mm=2,slotXY_mm=[2,2.6],slotAxis='Y',socketDepth_mm=1.2,verticalClearance_mm=.2,nominalRadialClearance_mm=.2,
             locatorWallSamplePoints=len(checks),resetModelDatum_mm=button,resetAccessDiameter_mm=2,probeDiameter_mm=.8,
             beforeVolumes_mm3=before,afterVolumes_mm3={c.name:c.bRepBodies.item(0).volume*1000 for c in [lower,upper,cap]},
             timelineIssues=issues,limitations=['Locator dimensions are provisional; tolerance, lead-in chamfer and local 0.5 mm wall need DFM review',
             'Reset hole uses old model placement; actual installed revision and solder gap unverified',
             'Model button height differs from current manufacturer nominal; no captive plunger or depth stop designed',
             'Probe is a nonconductive service-tool envelope, not an included manufactured part'])
    json.dump(out,open(BASE+'docs/service-and-locating-development.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False))
