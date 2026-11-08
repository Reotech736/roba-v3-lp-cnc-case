"""Fusion MCP: provisional 3.5 mm pocket depth retains 2 mm backing and 0.5 mm B1 gap."""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'


def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct)
    assert doc.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE' and not doc.isModified and doc.dataFile.versionNumber==11
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/checkpoints/v05_cloud_v11_before_stand_depth_comparison.f3d'))
    param=d.userParameters.itemByName('stand_depth');assert abs(param.value*10-3.7)<1e-6
    lower=next(o.component for o in d.rootComponent.occurrences if o.component.name.startswith('Lower_L_'))
    before=lower.bRepBodies.item(0).volume*1000
    param.expression='3.5 mm'
    feature=next(f for f in lower.features.extrudeFeatures if f.name=='Finger_access_backing_D12_residual2mm')
    distance=next(p for p in lower.modelParameters if p.createdBy==feature and p.role=='AlongDistance')
    distance.expression='stand_depth + stand_residual - floor_thickness'
    assert d.computeAll();assert lower.bRepBodies.count==1
    inside=adsk.fusion.PointContainment.PointInsidePointContainment;body=lower.bRepBodies.item(0);checks=[]
    for y in [-63.6,-17.1]:
        for x in [-52,-20,0]:
            for z,expected in [(3.49,False),(3.51,True),(5.49,True),(5.51,False)]:
                actual=body.pointContainment(adsk.core.Point3D.create(x/10,y/10,z/10))==inside
                assert actual==expected,str((x,y,z,actual,expected));checks.append([x,y,z,actual])
    assert body.pointContainment(adsk.core.Point3D.create(-.138934,-1.5,.549))==inside
    assert body.pointContainment(adsk.core.Point3D.create(-.138934,-1.5,.551))!=inside
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    p=BASE+'docs/internal-retention-development.json';r=json.load(open(p,encoding='utf-8'))
    r.update(metalCaseVolumesUnchanged=False,upperMetalCaseUnchanged=True,lowerMetalCaseChangedForConnectorClearance=True)
    r['connector']['nominalBackingGap_mm']=.5
    r['standPocketRevision']=dict(previousDepth_mm=3.7,currentDepth_mm=3.5,residual_mm=2,backingTopGlobalZ_mm=-6,
        additionalFoldedStandProtrusion_mm=.2,materialSamples=checks,nominalHeaderClearance_mm=.5,lowerVolumes_mm3=[before,body.volume*1000])
    json.dump(r,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    p=BASE+'docs/stand-folded-stack-study.json';s=json.load(open(p,encoding='utf-8'));s['previousPocketDepth_mm']=3.7;s['pocketDepth_mm']=3.5
    s['scenarios']=[dict(additionalAdhesive_mm=t,foldedProtrusionPastCase_mm=round(4+t-3.5,3),assumedRubberFootHeightFor0p2StandClearance_mm=round(4+t-3.5+.2,3)) for t in [0,.2,.5]]
    json.dump(s,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(dict(depth_mm=3.5,residual_mm=2,backingTopGlobalZ_mm=-6,nominalB1Gap_mm=.5,checkedMaterialPoints=len(checks),timelineIssues=issues)))
