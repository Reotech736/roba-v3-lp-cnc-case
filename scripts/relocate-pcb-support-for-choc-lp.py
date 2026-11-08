"""Fusion MCP: move support1, matching upper relief and insulation away from LP socket.

The 180-degree Choc placement correction must already be captured in the current design.
"""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'

def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber==19 and doc.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE'
    correction=json.load(open(BASE+'docs/choc-orientation-correction.json',encoding='utf-8'));assert correction['positionsCaptured']
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/checkpoints/v05_rotated_choc_before_support1_correction.f3d'))
    def get(prefix):return next(o.component for o in root.allOccurrences if o.component.name.startswith(prefix))
    lower=get('Lower_L_');upper=get('Upper_L_');pad=get('PCB_SUPPORT_INSULATION_')
    changes=[]
    for c,featureName in [(lower,'PCB_edge_support_1_INSULATION_PENDING'),(upper,'Support_clearance_1_0p2mm'),(pad,'Four_dielectric_support_stack_allowances')]:
        feature=next(f for f in c.features.extrudeFeatures if f.name==featureName);profile=feature.profile
        if profile.objectType==adsk.core.ObjectCollection.classType():profile=profile.item(0)
        s=profile.parentSketch;d.timeline.markerPosition=s.timelineObject.index+1;allCurves=list(s.sketchCurves)
        targets=[curve for curve in allCurves if curve.startSketchPoint.geometry.x*10 < -100 and curve.endSketchPoint.geometry.x*10 < -100 and curve.startSketchPoint.geometry.y*10 < -40 and curve.endSketchPoint.geometry.y*10 < -40]
        assert len(targets)==4,str((c.name,len(targets)))
        y0=min(min(c.startSketchPoint.geometry.y,c.endSketchPoint.geometry.y)*10 for c in targets);assert abs(y0-(-61.2 if c==upper else -61))<1e-5
        for curve in allCurves:curve.isFixed=False
        for p in list(s.sketchPoints)[1:]:p.isFixed=False
        col=adsk.core.ObjectCollection.create()
        for curve in targets:col.add(curve)
        m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,.8,0);assert s.move(col,m)
        after=min(min(curve.startSketchPoint.geometry.y,curve.endSketchPoint.geometry.y)*10 for curve in targets);assert abs(after-y0-8)<1e-5
        for curve in allCurves:curve.isFixed=True
        d.timeline.moveToEnd();assert d.computeAll();changes.append(dict(component=c.name,feature=featureName,oldMinY_mm=y0,newMinY_mm=after,dy_mm=8))
    group=next(o for o in root.occurrences if o.component.name=='CHOC_SWITCHES_AND_SOCKETS_REFERENCE_23_PAIRS')
    for kind,prefix in [('switch','CHOC_V2_RED_DETAILED_'),('socket','CHOC_SOCKET_DETAILED_')]:
        refs=[o for o in group.childOccurrences if o.component.name.startswith(prefix)]
        for o,r in zip(refs,[r for r in correction['placements'] if r['kind']==kind]):assert max(abs(x-y) for x,y in zip(o.transform2.asArray(),r['newMatrix']))<1e-8,r['key']
    assert lower.bRepBodies.count==1 and upper.bRepBodies.count==1 and pad.bRepBodies.count==4
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    out=dict(date='2026-11-08',oldSupport1XYXY_mm=[-106.12,-61,-103.82,-53],newSupport1XYXY_mm=[-106.12,-53,-103.82,-45],shiftY_mm=8,changes=changes,Choc46TransformsPreserved=True,timelineIssues=issues,
        currentCaseVolumes_mm3={c.name:c.bRepBodies.item(0).volume*1000 for c in [lower,upper]},limitations=['Public unpopulated PCB outline; actual copper/terminal revision and insulation material remain unqualified'])
    json.dump(out,open(BASE+'docs/choc-lp-support-correction.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False))
