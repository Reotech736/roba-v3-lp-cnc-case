"""Fusion MCP: relocate both stand pockets/backings to clear exterior and M2 seats.

One-shot on v17. Does not edit source data or any component except Lower_L.
Verify and save separately only after hole/containment/assembly checks pass.
"""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'

def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE' and doc.dataFile.versionNumber==17 and not doc.dataFile.isReadOnly
    lower=next(o.component for o in root.occurrences if o.component.name.startswith('Lower_L_'))
    assert lower.bRepBodies.count==1 and abs(lower.bRepBodies.item(0).volume*1000-35834.86113140607)<1e-4
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/checkpoints/v05_cloud_v17_before_stand_and_M2_correction.f3d'))
    def state(o):return dict(name=o.component.name,matrix=list(o.transform2.asArray()),volumes=[b.volume*1000 for b in o.component.bRepBodies],visible=o.isLightBulbOn)
    before=[state(o) for o in root.allOccurrences]
    json.dump(before,open(BASE+'docs/stand-correction-component-baseline.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    selected=[]
    for name in ['スケッチ3','スケッチ4','スケッチ5','スケッチ6','スケッチ15','スケッチ16','Original_stand_pocket_clearance_after_added_backing']:
        s=next(s for s in lower.sketches if s.name==name);selected.append(s)
    assert all(abs(c.centerSketchPoint.geometry.x*10-6.8)<1e-6 for c in selected[4].sketchCurves.sketchCircles)
    changes=[]
    for s in selected:
        d.timeline.markerPosition=s.timelineObject.index+1
        curves=list(s.sketchCurves)
        for c in curves:c.isFixed=False
        for p in list(s.sketchPoints)[1:]:p.isFixed=False
        groups={True:[],False:[]}
        def point(c):return c.centerSketchPoint.geometry if c.objectType==adsk.fusion.SketchCircle.classType() else c.startSketchPoint.geometry
        for c in curves:groups[point(c).y*10 < -40].append(c)
        checks=[]
        for row1,items in groups.items():
            if not items:continue
            dx=-2.5;dy=2.5 if row1 else 0
            prior=[[point(c).x*10,point(c).y*10] for c in items]
            col=adsk.core.ObjectCollection.create()
            for c in items:col.add(c)
            m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(dx/10,dy/10,0)
            assert s.move(col,m),s.name
            for c,p in zip(items,prior):
                actual=[point(c).x*10,point(c).y*10]
                assert max(abs(x-y) for x,y in zip(actual,[p[0]+dx,p[1]+dy]))<1e-6,str((s.name,actual,p))
            checks.append(dict(firstRow=row1,curves=len(items),dx_mm=dx,dy_mm=dy))
        for c in curves:c.isFixed=True
        d.timeline.moveToEnd();assert d.computeAll()
        changes.append(dict(sketch=s.name,groups=checks))
    assert lower.bRepBodies.count==1
    after=[state(o) for o in root.allOccurrences];assert len(before)==len(after)
    for first,last in zip(before,after):
        assert first['name']==last['name'] and first['matrix']==last['matrix'] and first['visible']==last['visible']
        if first['name']!=lower.name:
            assert len(first['volumes'])==len(last['volumes'])
            assert max([0]+[abs(x-y) for x,y in zip(first['volumes'],last['volumes'])])<1e-5,first['name']
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    out=dict(date='2026-11-08',baselineCloudVersion=17,changedComponent=lower.name,standPocketsXYWH_mm=[[-52.5,-68.5,56.8,14.8],[-52.5,-24.5,56.8,14.8]],
        standBackingXYXY_mm=[[-54.5,-70.5,6.3,-51.7],[-54.5,-26.5,6.3,-7.7]],fingerCentersXY_mm=[[4.3,-61.1],[4.3,-17.1]],
        pocketDepth_mm=3.5,nominalResidual_mm=2,fingerDiameter_mm=8,fingerBackingDiameter_mm=12,lowerVolumeBefore_mm3=before[0]['volumes'][0],lowerVolumeAfter_mm3=lower.bRepBodies.item(0).volume*1000,
        allOccurrenceTransformsPreserved=True,otherComponentVolumesPreserved=True,visibilityPreserved=True,sketchChanges=changes,timelineIssues=issues,
        limitations=['Corrected placement only; no manufacturing, hinge sweep, strength or physical assembly certification','Separate current hole, actual backing containment, residual, and assembly interference verification required before save'])
    json.dump(out,open(BASE+'docs/stand-and-M2-correction.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False))
