"""Fusion MCP: relocate support #4 after detailed socket interference was detected."""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'


def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE'
    lower=next(o.component for o in root.occurrences if o.component.name.startswith('Lower_L_'))
    upper=next(o.component for o in root.occurrences if o.component.name.startswith('Upper_L_'))
    old=next(f for f in lower.features.extrudeFeatures if f.name=='PCB_edge_support_4_INSULATION_PENDING')
    assert not old.isSuppressed
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/checkpoints/v05_before_socket_support_relocation.f3d'))
    old.isSuppressed=True;d.computeAll()
    def p(x,y):return adsk.core.Point3D.create(x/10,y/10,0)
    def rect(c,z,b):
        i=c.constructionPlanes.createInput();i.setByOffset(c.xYConstructionPlane,adsk.core.ValueInput.createByString(str(z)+' mm'))
        plane=c.constructionPlanes.add(i);plane.isLightBulbOn=False;s=c.sketches.add(plane)
        for line in s.sketchCurves.sketchLines.addTwoPointRectangle(p(*b[:2]),p(*b[2:])):line.isFixed=True
        return s
    target=lower.bRepBodies.item(0)
    s=rect(lower,8,[-66.3,6.254,-60.3,8.554])
    e=lower.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString('support_height'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    e.name='Relocated_PCB_support_4_SOCKET_CLEARANCE_INSULATION_PENDING';s.isLightBulbOn=False
    coll=adsk.core.ObjectCollection.create();coll.add(e.bodies.item(0))
    i=lower.features.combineFeatures.createInput(target,coll);i.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation
    lower.features.combineFeatures.add(i).name='Join_relocated_support_4_to_lower_only'
    s=rect(upper,0,[-66.5,6.054,-60.1,8.754])
    i=upper.features.extrudeFeatures.createInput(s.profiles.item(0),adsk.fusion.FeatureOperations.CutFeatureOperation)
    i.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('1 mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
    i.participantBodies=[upper.bRepBodies.item(0)]
    upper.features.extrudeFeatures.add(i).name='Relocated_support_4_upper_relief_0p2mm';s.isLightBulbOn=False
    assert d.computeAll()
    assert lower.bRepBodies.count==1 and upper.bRepBodies.count==1
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    # All samples within the intended bearing strip remain under actual PCB material.
    pcb=next(o for o in root.occurrences if o.component.name.startswith('PCB_L_')).bRepBodies.item(0)
    INSIDE=adsk.fusion.PointContainment.PointInsidePointContainment
    points=[]
    # Exclude the rounded PCB corner from the intended central bearing strip.
    for x in [-65,-64,-63,-62,-61]:
        for y in [6.3,6.5,6.8,7]:
            assert pcb.pointContainment(adsk.core.Point3D.create(x/10,y/10,.08))==INSIDE
            assert lower.bRepBodies.item(0).pointContainment(adsk.core.Point3D.create(x/10,y/10,1.129))==INSIDE
            points.append([x,y])
    out=dict(date='2026-11-08',oldSupportXY_mm=[-60,6.254,-54,8.554],newSupportXY_mm=[-66.3,6.254,-60.3,8.554],
             upperReliefXY_mm=[-66.5,6.054,-60.1,8.754],supportTopGlobalZ_mm=-.2,
             bearingSamples=len(points),nominalSocketPlasticBoundingGapX_mm=.50566,
             lowerVolume_mm3=lower.bRepBodies.item(0).volume*1000,upperVolume_mm3=upper.bRepBodies.item(0).volume*1000,
             timelineIssues=issues,limitations=['PCB trace clearance and insulation not established','Socket orientation remains provisional'])
    json.dump(out,open(BASE+'docs/socket-support-relocation-verification.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False))
