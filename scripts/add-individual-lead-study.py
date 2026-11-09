"""One-time v27: add hidden individual-wire feasibility studies only.

No physical case, bracket or prior study is changed. All wires are nominal
geometric trials; endpoints do not model a pouch outlet or stripped conductors.
"""
import adsk.core,adsk.fusion,json,math
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')

def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber==27 and not doc.isModified
    assert (BASE/'cad/design/checkpoints/v05_cloud_v27_before_individual_lead_study.f3d').exists()
    approved=json.loads((BASE/'docs/current-approved-component-state.json').read_text(encoding='utf-8'));live={o.fullPathName:o for o in root.allOccurrences}
    assert len(approved)==587
    for r in approved:
        o=live[r['path']];assert r['bodies']==o.component.bRepBodies.count
        assert max(abs(a-b) for a,b in zip(r['matrix'],o.transform2.asArray()))<1e-8
        assert all(abs(v-b.volume*1000)<1e-5 for v,b in zip(r['volumes'],o.component.bRepBodies))
    for gap in [0,2,5,8,10]:
        verification=json.loads((BASE/f'docs/individual-lead-verification-gap{gap}.json').read_text(encoding='utf-8'))
        assert all(not r['obstructions'] for r in verification['leads']) and verification['pairD1SurfaceMargin_mm']>.1
    studies=next(o for o in root.allOccurrences if o.component.name=='CLEARANCE_STUDIES_NOT_PARTS')
    assert studies.childOccurrences.count==12
    assert not any(o.component.name.startswith('BATTERY_TWO_D1_LEADS40_') for o in root.allOccurrences)
    def component(name):
        o=studies.component.occurrences.addNewComponent(adsk.core.Matrix3D.create());o.component.name=name;o.isLightBulbOn=False;return o.component
    closed=component('BATTERY_TWO_D1_LEADS40_CLOSED_GEOMETRY_TRIAL_NOT_PARTS')
    openPoses=component('BATTERY_TWO_D1_LEADS40_OPEN_POSES_NOT_CONTINUOUS_MOTION')
    point=lambda p:adsk.core.Point3D.create(*[v/10 for v in p])
    data=json.loads((BASE/'docs/individual-battery-lead-study.json').read_text(encoding='utf-8'))
    for lead in data['poses'][0]['leads']:
        sketch=closed.sketches.add(closed.xYConstructionPlane);sketch.name=f'Lead_to_X{lead["padXY_mm"][0]}_40mm_R1_R3_R1p5_ASSUMED'
        sketch.isComputeDeferred=True
        for s in lead['segments']:
            curve=sketch.sketchCurves.sketchLines.addByTwoPoints(point(s['start']),point(s['end'])) if s['type']=='line' else sketch.sketchCurves.sketchArcs.addByThreePoints(point(s['start']),point(s['mid']),point(s['end']))
            curve.isFixed=True
        sketch.isComputeDeferred=False
        assert abs(sum(c.length*10 for c in sketch.sketchCurves)-40)<1e-6
        owner=next(o for o in root.allOccurrences if o.component==closed);collection=adsk.core.ObjectCollection.create()
        for c in sketch.sketchCurves:collection.add(c.createForAssemblyContext(owner))
        path=adsk.fusion.Path.create(collection,adsk.fusion.ChainedCurveOptions.noChainedCurves);assert path
        inp=closed.features.pipeFeatures.createInput(path,adsk.fusion.FeatureOperations.NewBodyFeatureOperation);inp.sectionSize=adsk.core.ValueInput.createByString('1 mm')
        feature=closed.features.pipeFeatures.add(inp);feature.name=f'D1_40mm_GEOMETRIC_LEAD_SIDE{lead["side"]}_NOT_ELECTRICAL_POLARITY'
        sketch.isLightBulbOn=False
    assert closed.bRepBodies.count==2 and all(b.isSolid and abs(b.volume*1000-10*math.pi)<.01 for b in closed.bRepBodies)
    manager=adsk.fusion.TemporaryBRepManager.get();base=openPoses.features.baseFeatures.add();base.name='Independent_40mm_poses_not_flexible_motion';assert base.startEdit()
    for pose in data['poses'][1:]:
        for lead in pose['leads']:
            curves=[adsk.core.Line3D.create(point(s['start']),point(s['end'])) if s['type']=='line' else adsk.core.Arc3D.createByThreePoints(point(s['start']),point(s['mid']),point(s['end'])) for s in lead['segments']]
            body,_=manager.createWireFromCurves(curves);new=openPoses.bRepBodies.add(body,base);new.name=f'DOWN_{pose["lowerDown_mm"]}mm_SIDE_{lead["side"]}_LENGTH40'
    assert base.finishEdit();assert openPoses.bRepBodies.count==8
    assert d.computeAll();issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues
    for r in approved:
        o=live[r['path']];assert r['bodies']==o.component.bRepBodies.count
        assert max(abs(a-b) for a,b in zip(r['matrix'],o.transform2.asArray()))<1e-8
        assert all(abs(v-b.volume*1000)<1e-5 for v,b in zip(r['volumes'],o.component.bRepBodies))
    result={'date':'2026-11-09','baselineCloudVersion':27,'saved':False,'previous587RecordsPreserved':True,'physicalGeometryChanged':False,'addedClosedD1StudySolids':2,'addedIndependentOpenWireBodies':8,'batteryPhysicalCandidates':5,'clearanceStudyChildren':studies.childOccurrences.count,'timelineIssues':issues,'actualWireBendSpecificationVerified':False,'installedTieRoutingVerified':False}
    (BASE/'docs/individual-lead-development.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
