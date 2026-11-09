"""One-time v28: join right M2-boss extrema with42mm straight side.

Preserves the existing unsaved document state by exporting a checkpoint first.
Re-cut right screw passages and lower bracket relief after joining new stock.
"""
import adsk.core,adsk.fusion,json
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')

def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:H9Nq8f1PSl6GXmxJMgIkbw' and doc.dataFile.versionNumber==28
    approved=json.loads((BASE/'docs/current-approved-component-state.json').read_text(encoding='utf-8'));live={o.fullPathName:o for o in root.allOccurrences}
    assert len(approved)==589
    for r in approved:
        o=live[r['path']];assert o.component.bRepBodies.count==r['bodies']
        assert max(abs(a-b) for a,b in zip(r['matrix'],o.transform2.asArray()))<1e-8
        assert all(abs(v-b.volume*1000)<1e-5 for v,b in zip(r['volumes'],o.component.bRepBodies))
    checkpoint=BASE/'cad/design/checkpoints/v05_cloud_v28_WORKING_before_positive_x_straight_wall.f3d'
    assert not checkpoint.exists()
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(checkpoint)))
    beforeModified=doc.isModified;beforeTimeline=d.timeline.count
    cases=[next(o for o in root.occurrences if o.component.name.startswith(prefix)) for prefix in ['Lower_L_','Upper_L_']]
    bounds=lambda b:[[v*10 for v in p.asArray()] for p in [b.preciseBoundingBox.minPoint,b.preciseBoundingBox.maxPoint]]
    before={o.component.name:{'boundsGlobal_mm':bounds(o.bRepBodies.item(0)),'volume_mm3':o.component.bRepBodies.item(0).volume*1000} for o in cases}
    point=lambda x,y:adsk.core.Point3D.create(x/10,y/10,0)
    def cut(c,s,height,name):
        profiles=adsk.core.ObjectCollection.create()
        for p in s.profiles:profiles.add(p)
        inp=c.features.extrudeFeatures.createInput(profiles,adsk.fusion.FeatureOperations.CutFeatureOperation)
        inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(f'{height} mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        inp.participantBodies=[c.bRepBodies.item(0)];c.features.extrudeFeatures.add(inp).name=name;s.isLightBulbOn=False
    for o,height in zip(cases,[10.5,5.5]):
        c=o.component;target=c.bRepBodies.item(0);assert c.bRepBodies.count==1
        s=c.sketches.add(c.xYConstructionPlane);s.name='Positive_X_straight_wall_between_M2_boss_extrema'
        for line in s.sketchCurves.sketchLines.addTwoPointRectangle(point(13.576167,-59),point(16.576167,-17)):line.isFixed=True
        new=c.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString(f'{height} mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        new.name='Add_right_wall_to_existing_M2_boss_outer_tangent';s.isLightBulbOn=False
        tools=adsk.core.ObjectCollection.create();tools.add(new.bodies.item(0));inp=c.features.combineFeatures.createInput(target,tools);inp.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation
        c.features.combineFeatures.add(inp).name='Explicit_join_right_wall_SINGLE_SOLID';assert c.bRepBodies.count==1
        s=c.sketches.add(c.xYConstructionPlane)
        for y in [-59,-17]:s.sketchCurves.sketchCircles.addByCenterRadius(point(13.576167,y),.11 if o==cases[0] else .08).isFixed=True
        cut(c,s,10.5 if o==cases[0] else 4.5,'Restore_right_M2_clearances_or_blind_pilots_after_straight_wall')
        if o==cases[0]:
            s=c.sketches.add(c.xYConstructionPlane)
            for y in [-59,-17]:s.sketchCurves.sketchCircles.addByCenterRadius(point(13.576167,y),.21).isFixed=True
            cut(c,s,2.2,'Restore_right_M2_head_seats_after_straight_wall')
            inp=c.constructionPlanes.createInput();inp.setByOffset(c.xYConstructionPlane,adsk.core.ValueInput.createByString('6.3 mm'));plane=c.constructionPlanes.add(inp);plane.isLightBulbOn=False
            s=c.sketches.add(plane)
            for line in s.sketchCurves.sketchLines.addTwoPointRectangle(point(10.7,-27.2),point(14.9,-18.6)):line.isFixed=True
            cut(c,s,4.2,'Restore_existing_lower_wire_bracket_relief_after_straight_wall')
        c.bRepBodies.item(0).material=c.material
    assert d.computeAll();issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues
    for r in approved:
        o=live[r['path']];assert max(abs(a-b) for a,b in zip(r['matrix'],o.transform2.asArray()))<1e-8
        if not o.component.name.startswith(('Lower_L_','Upper_L_')):
            assert r['bodies']==o.component.bRepBodies.count and all(abs(v-b.volume*1000)<1e-5 for v,b in zip(r['volumes'],o.component.bRepBodies))
    after={};edges=[]
    for o,z in zip(cases,[-11.5,4.5]):
        body=o.bRepBodies.item(0);assert o.component.bRepBodies.count==1
        after[o.component.name]={'boundsGlobal_mm':bounds(body),'volume_mm3':body.volume*1000}
        assert max(abs(a-b) for aa,bb in zip(before[o.component.name]['boundsGlobal_mm'],bounds(body)) for a,b in zip(aa,bb))<1e-5
        found=[]
        for e in body.edges:
            if e.geometry.objectType!=adsk.core.Line3D.classType():continue
            points=[[v*10 for v in p.geometry.asArray()] for p in [e.startVertex,e.endVertex]]
            if all(abs(p[0]-16.576167)<1e-5 and abs(p[2]-z)<1e-5 for p in points):found.append({'pointsGlobal_mm':points,'length_mm':e.length*10})
        assert len(found)==1 and abs(found[0]['length_mm']-42)<1e-5;edges.append({'component':o.component.name,'edge':found[0]})
    report={'date':'2026-11-10','baselineCloudVersion':28,'preexistingModifiedFlagPreserved':beforeModified,'baselineTimelineCount':beforeTimeline,'afterTimelineCount':d.timeline.count,'previousRecordsChecked':589,'onlyCaseVolumesChanged':True,'allPriorTransformsPreserved':True,'before':before,'after':after,'positiveXWall_mm':16.576167,'rightStraightEdges':edges,'caseBoundsUnchanged':True,'lowerBracketReliefPreservedByRecut':True,'rightM2HolesRestoredByRecut':True,'materialPreserved':True,'timelineIssues':issues,'saved':False}
    (BASE/'docs/positive-x-straight-wall-development.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
