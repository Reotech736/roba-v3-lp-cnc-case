"""One-time v26 audit correction: strengthen outside stock of new M1.6 pilots."""
import adsk.core,adsk.fusion,json
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')


def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber==26
    assert (BASE/'cad/design/checkpoints/v05_cloud_v26_before_consistency_audit_correction.f3d').exists()
    upper=next(o for o in root.occurrences if o.component.name.startswith('Upper_L_'));c=upper.component
    assert c.bRepBodies.count==1 and abs(c.bRepBodies.item(0).volume*1000-13564.68913438139)<1e-5
    def bounds(body):return [[v*10 for v in p.asArray()] for p in [body.preciseBoundingBox.minPoint,body.preciseBoundingBox.maxPoint]]
    before={'upperVolume_mm3':c.bRepBodies.item(0).volume*1000,'bodyGlobalBounds_mm':bounds(upper.bRepBodies.item(0))}
    target=c.bRepBodies.item(0)
    s=c.sketches.add(c.xYConstructionPlane);s.name='Audit_fix_upper_M1p6_outer_backing_profile'
    for line in s.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(1.38,-2.76,0),adsk.core.Point3D.create(1.6,-1.82,0)):line.isFixed=True
    f=c.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString('5.5 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation);f.name='Audit_fix_upper_M1p6_outer_backing'
    tools=adsk.core.ObjectCollection.create();tools.add(f.bodies.item(0));i=c.features.combineFeatures.createInput(target,tools);i.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation
    c.features.combineFeatures.add(i).name='Explicit_join_upper_M1p6_backing_SINGLE_SOLID';s.isLightBulbOn=False
    assert d.computeAll() and c.bRepBodies.count==1
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues
    after={'upperVolume_mm3':c.bRepBodies.item(0).volume*1000,'bodyGlobalBounds_mm':bounds(upper.bRepBodies.item(0))}
    unchanged=max(abs(a-b) for aa,bb in zip(before['bodyGlobalBounds_mm'],after['bodyGlobalBounds_mm']) for a,b in zip(aa,bb))<1e-5
    out={'date':'2026-11-09','baselineCloudVersion':26,'fix':'Add local upper outside backing for the two M1.6 pilots; old outer-side thread-major stock approx0.476mm.',
         'addedBackingGlobal_mm':[13.8,-27.6,-1,16,-18.2,4.5],'comparisonSleeveRadialWall_mm':.9,
         'before':before,'after':after,'upperSingleSolid':True,'upperMaximumBodyBoundsUnchanged':unchanged,'timelineIssues':issues,'saved':False}
    (BASE/'docs/design-consistency-correction.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
