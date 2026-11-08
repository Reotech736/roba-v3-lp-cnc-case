"""Fusion MCP: align the selected side with M2 boss extrema to form a contact line.

One-shot v18; no screw relocation, PCB edits or source changes. Save after verification.
"""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'

def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE' and doc.dataFile.versionNumber==18 and not doc.isModified
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/checkpoints/v05_cloud_v18_before_continuous_contact_edge.f3d'))
    lower=next(o for o in root.occurrences if o.component.name.startswith('Lower_L_'));upper=next(o for o in root.occurrences if o.component.name.startswith('Upper_L_'))
    before={o.component.name:o.component.bRepBodies.item(0).volume*1000 for o in [lower,upper]}
    extentsBefore={o.component.name:dict(min=o.bRepBodies.item(0).preciseBoundingBox.minPoint.asArray(),max=o.bRepBodies.item(0).preciseBoundingBox.maxPoint.asArray()) for o in [lower,upper]}
    xAxis=-108.119997;xContact=xAxis-3
    def pt(x,y):return adsk.core.Point3D.create(x/10,y/10,0)
    def profiles(s):
        out=adsk.core.ObjectCollection.create()
        for p in s.profiles:out.add(p)
        return out
    def cut(c,diameter,height,name):
        s=c.sketches.add(c.xYConstructionPlane)
        for y in [-59,-17]:s.sketchCurves.sketchCircles.addByCenterRadius(pt(xAxis,y),diameter/20).isFixed=True
        i=c.features.extrudeFeatures.createInput(profiles(s),adsk.fusion.FeatureOperations.CutFeatureOperation)
        i.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(str(height)+' mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        i.participantBodies=[c.bRepBodies.item(0)];c.features.extrudeFeatures.add(i).name=name;s.isLightBulbOn=False
    for o,height in [(lower,10.5),(upper,5.5)]:
        c=o.component;s=c.sketches.add(c.xYConstructionPlane)
        for line in s.sketchCurves.sketchLines.addTwoPointRectangle(pt(xContact,-59),pt(xAxis,-17)):line.isFixed=True
        i=c.features.extrudeFeatures.createInput(s.profiles.item(0),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        i.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(str(height)+' mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        added=c.features.extrudeFeatures.add(i);added.name='Continuous_front_contact_wall_to_M2_boss_extent';s.isLightBulbOn=False
        existing=next(b for b in c.bRepBodies if b not in list(added.bodies))
        tools=adsk.core.ObjectCollection.create();tools.add(added.bodies.item(0));ci=c.features.combineFeatures.createInput(existing,tools);ci.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation
        c.features.combineFeatures.add(ci).name='Join_contact_wall_only_to_same_case_component'
        assert c.bRepBodies.count==1
        if o==lower:
            cut(c,2.2,10.5,'Restore_two_M2_passages_after_contact_wall')
            cut(c,4.2,2.2,'Restore_two_M2_head_seats_after_contact_wall')
        else:cut(c,1.6,4.5,'Restore_two_M2_blind_pilots_after_contact_wall')
    assert d.computeAll()
    boundsAfter={o.component.name:dict(min=o.bRepBodies.item(0).preciseBoundingBox.minPoint.asArray(),max=o.bRepBodies.item(0).preciseBoundingBox.maxPoint.asArray()) for o in [lower,upper]}
    for name in extentsBefore:
        for key in ['min','max']:assert max(abs(x-y) for x,y in zip(extentsBefore[name][key],boundsAfter[name][key]))<1e-6,str((name,key))
    edges=[]
    for e in lower.bRepBodies.item(0).edges:
        line=adsk.core.Line3D.cast(e.geometry)
        if not line:continue
        ends=[[v.geometry.x*10,v.geometry.y*10,v.geometry.z*10] for v in [e.startVertex,e.endVertex]]
        if all(abs(p[0]-xContact)<1e-5 and abs(p[2]+11.5)<1e-5 for p in ends):edges.append(dict(endsGlobal_mm=ends,length_mm=e.length*10))
    assert abs(sum(v['length_mm'] for v in edges)-42)<1e-4,str(edges)
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    out=dict(date='2026-11-08',baselineCloudVersion=18,oldSelectedEdgeX_mm=-108.619997,contactEdgeX_mm=xContact,contactEdgeGlobalZ_mm=-11.5,
        contactEdgeYRange_mm=[-59,-17],contactEdgeLength_mm=42,edgeMovedOutward_mm=2.5,overallCaseBoundsUnchanged=True,boundsBefore_cm=extentsBefore,boundsAfter_cm=boundsAfter,
        affectedComponents=[lower.component.name,upper.component.name],volumesBefore_mm3=before,volumesAfter_mm3={o.component.name:o.component.bRepBodies.item(0).volume*1000 for o in [lower,upper]},
        contactEdges=edges,M2AxesPreserved=True,clearanceDiameter_mm=2.2,headSeatDiameter_mm=4.2,headSeatDepth_mm=2.2,pilotDiameter_mm=1.6,pilotDepth_mm=4.5,timelineIssues=issues,
        limitations=['Contact line is shifted2.5mm outward relative to selected v18 edge, while the former screw-boss envelope remains the outer bound',
        'Ideal rigid planar-table support only; actual stand angles, feet, rubber and stability are not certified','No edge chamfer/fillet or protective strip applied to the contact line'])
    json.dump(out,open(BASE+'docs/continuous-contact-edge-development.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False))
