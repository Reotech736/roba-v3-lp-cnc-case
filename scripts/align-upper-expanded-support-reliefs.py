"""Fusion MCP: align small/expanded upper support reliefs with current pads1 and4.

Remove obsolete late duplicate relief4 by suppression; preserve all other components.
"""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'

def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE' and doc.dataFile.versionNumber==21 and not doc.dataFile.isReadOnly
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/checkpoints/v05_cloud_v21_before_upper_support_relief_alignment.f3d'))
    upper=next(o.component for o in root.occurrences if o.component.name.startswith('Upper_L_'))
    def records():return [dict(name=o.component.name,path=o.fullPathName,matrix=list(o.transform2.asArray()),bodies=o.component.bRepBodies.count,volumes=[b.volume*1000 for b in o.component.bRepBodies],visible=o.isLightBulbOn) for o in root.allOccurrences]
    before=records();beforeVolume=upper.bRepBodies.item(0).volume*1000
    late=next(f for f in upper.features.extrudeFeatures if f.name=='Relocated_support_4_upper_relief_0p2mm');assert not late.isSuppressed
    late.isSuppressed=True
    changes=[]
    for name,dx,dy,expected in [('Expanded_support_clearance_1',0,8,[-107.32,-62.2,-102.62,-51.8]),('Support_clearance_4_0p2mm',-6.3,0,[-60.2,6.054,-53.8,8.754]),('Expanded_support_clearance_4',-6.3,0,[-61.2,5.054,-52.8,9.754])]:
        f=next(f for f in upper.features.extrudeFeatures if f.name==name);s=f.profile.parentSketch
        d.timeline.markerPosition=s.timelineObject.index+1;curves=list(s.sketchCurves.sketchLines)
        def bounds():
            points=[p.geometry for c in curves for p in [c.startSketchPoint,c.endSketchPoint]]
            return [min(p.x*10 for p in points),min(p.y*10 for p in points),max(p.x*10 for p in points),max(p.y*10 for p in points)]
        old=bounds();assert max(abs(x-y) for x,y in zip(old,expected))<1e-5,str((name,old))
        for c in curves:c.isFixed=False
        for p in list(s.sketchPoints)[1:]:p.isFixed=False
        col=adsk.core.ObjectCollection.create()
        for c in curves:col.add(c)
        m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(dx/10,dy/10,0);assert s.move(col,m)
        new=bounds();assert max(abs(x-y) for x,y in zip(new,[old[0]+dx,old[1]+dy,old[2]+dx,old[3]+dy]))<1e-5
        for c in curves:c.isFixed=True
        d.timeline.moveToEnd();assert d.computeAll();changes.append(dict(feature=name,beforeXYXY_mm=old,afterXYXY_mm=new))
    assert upper.bRepBodies.count==1
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    after=records();assert len(before)==len(after)
    for x,y in zip(before,after):
        assert x['name']==y['name'] and x['path']==y['path'] and x['matrix']==y['matrix'] and x['visible']==y['visible'] and x['bodies']==y['bodies']
        if x['name']!=upper.name:assert max([0]+[abs(a-b) for a,b in zip(x['volumes'],y['volumes'])])<1e-5,x['name']
    out=dict(date='2026-11-08',baselineCloudVersion=21,changedComponent=upper.name,reason='Expanded relief1 and both old relief4 cuts were not aligned when PCB supports moved',changes=changes,suppressedObsoleteFeature=late.name,
        upperVolumeBefore_mm3=beforeVolume,upperVolumeAfter_mm3=upper.bRepBodies.item(0).volume*1000,otherGeometryTransformsAndVisibilityPreserved=True,timelineIssues=issues,
        limitations=['Four reliefs still need current-pad cavity, detail socket and locator/fastener checks; no manufacturing certification'])
    json.dump(out,open(BASE+'docs/upper-support-relief-alignment.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False))
