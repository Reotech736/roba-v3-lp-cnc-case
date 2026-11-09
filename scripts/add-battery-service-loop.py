"""One-time v24: add verified nominal R3/40mm curve and bounded service poses.

Case and carrier geometry unchanged. PCB bonding footprint is a study, not a part.
"""
import adsk.core,adsk.fusion,json,math
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')


def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber==24
    # A failed wire-edge Path attempt was undone. Fusion may retain its dirty
    # flag; verify the complete approved state before allowing this retry.
    approved=json.loads((BASE/'docs/current-approved-component-state.json').read_text(encoding='utf-8'))
    live={o.fullPathName:o for o in root.allOccurrences}
    assert len(live)==len(approved)+2
    for row in approved:
        o=live[row['path']]
        assert o.component.bRepBodies.count==row['bodies']
        assert max(abs(a-b) for a,b in zip(row['matrix'],o.transform2.asArray()))<1e-8
        assert all(abs(v-b.volume*1000)<1e-5 for v,b in zip(row['volumes'],o.component.bRepBodies))
    assert (BASE/'cad/design/checkpoints/v05_cloud_v24_before_battery_service_loop.f3d').exists()
    poses=json.loads((BASE/'docs/battery-service-loop-study.json').read_text(encoding='utf-8'))['poses']
    for gap in [0,2,5,8,10]:
        r=json.loads((BASE/f'docs/battery-service-loop-verification-gap{gap}.json').read_text())
        assert len(r['rows'])==1 and not r['rows'][0]['obstructions']
    before=[(o,o.component.name,list(o.transform2.asArray()),[b.volume*1000 for b in o.component.bRepBodies]) for o in root.allOccurrences]
    studies=next(o for o in root.allOccurrences if o.component.name=='CLEARANCE_STUDIES_NOT_PARTS')
    assert max(abs(a-b) for a,b in zip(studies.transform2.asArray(),adsk.core.Matrix3D.create().asArray()))<1e-8
    mgr=adsk.fusion.TemporaryBRepManager.get()
    def point(p):return adsk.core.Point3D.create(*[v/10 for v in p])
    def wire(pose):
        curves=[]
        for s in pose['bundleSegments']:
            curves.append(adsk.core.Line3D.create(point(s['start']),point(s['end'])) if s['type']=='line' else adsk.core.Arc3D.createByThreePoints(point(s['start']),point(s['mid']),point(s['end'])))
        body,_=mgr.createWireFromCurves(curves);assert body
        return body
    def component(name):
        o=studies.component.occurrences.addNewComponent(adsk.core.Matrix3D.create());o.component.name=name;o.isLightBulbOn=False;return o.component
    def addbody(c,body,name):
        f=c.features.baseFeatures.add();f.name=name
        assert f.startEdit();new=c.bRepBodies.add(body,f);assert f.finishEdit()
        return new
    closed=next(p for p in poses if p['lowerDown_mm']==0 and p['bendRadiusAssumed_mm']==3)
    current=component('BATTERY_WIRE_ROUTE_D3_DIRECT_SOLDER_B1_40mm_R3_LOOP_NOT_PART')
    sketch=current.sketches.add(current.xYConstructionPlane);sketch.name='R3_3D_centerline_nominal40_leads'
    sketch.isComputeDeferred=True
    edges=adsk.core.ObjectCollection.create()
    for s in closed['bundleSegments']:
        curve=sketch.sketchCurves.sketchLines.addByTwoPoints(point(s['start']),point(s['end'])) if s['type']=='line' else sketch.sketchCurves.sketchArcs.addByThreePoints(point(s['start']),point(s['mid']),point(s['end']))
        curve.isFixed=True;edges.add(curve)
    sketch.isComputeDeferred=False
    assert abs(sum(c.length*10 for c in sketch.sketchCurves)-closed['bundleLength_mm'])<1e-6
    # Path resolves geometry in assembly context for this nested component.
    owner=next(o for o in root.allOccurrences if o.component==current)
    contextual=adsk.core.ObjectCollection.create()
    for c in sketch.sketchCurves:contextual.add(c.createForAssemblyContext(owner))
    path=adsk.fusion.Path.create(contextual,adsk.fusion.ChainedCurveOptions.noChainedCurves);assert path
    inp=current.features.pipeFeatures.createInput(path,adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    inp.sectionSize=adsk.core.ValueInput.createByString('3 mm')
    pipe=current.features.pipeFeatures.add(inp);pipe.name='D3_bundle_along_R3_closed_pose_NOT_ACTUAL_WIRES'
    sketch.isLightBulbOn=False
    solid=next(b for b in current.bRepBodies if b.isSolid)
    branchBodies=[]
    e=closed['bundleSegments'][-1]['end']
    for dx in [-1,1]:
        end=[e[0]+dx,e[1],-.5]
        body=mgr.createCylinderOrCone(point(e),.05,point(end),.05)
        assert mgr.booleanOperation(body,mgr.createSphere(point(end),.05),adsk.fusion.BooleanTypes.UnionBooleanType)
        addbody(current,body,'D1_terminal_branch_assumed')
    tools=adsk.core.ObjectCollection.create()
    for b in current.bRepBodies:
        if b.isSolid and b!=solid:tools.add(b)
    ci=current.features.combineFeatures.createInput(solid,tools);ci.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation
    current.features.combineFeatures.add(ci).name='Join_two_D1_branches_to_bundle_allowance'
    assert sum(b.isSolid for b in current.bRepBodies)==1
    # Keep independent open-pose centerlines hidden; no claim of continuous deformation.
    motion=component('BATTERY_SERVICE_POSES_R3_LENGTH40_CENTERLINES_NOT_PARTS')
    for gap in [2,5,8,10]:
        p=next(p for p in poses if p['lowerDown_mm']==gap and p['bendRadiusAssumed_mm']==3)
        addbody(motion,wire(p),f'LOWER_DOWN_{gap}mm_INDEPENDENT_POSE_NOT_CONTINUOUS_MOTION')
    # Mechanical allocation only: copper, solder mask and adhesive remain unqualified.
    anchor=component('PCB_WIRE_STRAIN_RELIEF_BOND_FOOTPRINT_6x2_STUDY_NOT_PART')
    footprint=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(point([-1.38934,-23,-.1]),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),.6,.2,.02))
    addbody(anchor,footprint,'PCB_BONDING_SITE_COPPER_MASK_ADHESIVE_UNVERIFIED')
    old=next(o for o in root.allOccurrences if o.component.name=='BATTERY_WIRE_ROUTE_D3_DIRECT_SOLDER_B1_40mm_BUDGET_NOT_PART')
    old.component.name='RETIRED_MINIMUM_PATH_'+old.component.name;old.isLightBulbOn=False
    assert d.computeAll()
    for o,name,matrix,volumes in before:
        assert max(abs(a-b) for a,b in zip(matrix,o.transform2.asArray()))<1e-8,name
        assert all(abs(v-b.volume*1000)<1e-5 for v,b in zip(volumes,o.component.bRepBodies)),name
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    out={'date':'2026-11-08','baselineCloudVersion':24,'caseAndCarrierGeometryChanged':False,
         'previousTransformsAndVolumesPreserved':True,'nominalEachLeadLength_mm':40,'bendRadiusAssumed_mm':3,
         'independentOpenPoses_mm':[2,5,8,10],'currentWireSolidCount':sum(b.isSolid for b in current.bRepBodies),
         'currentWireNonSolidCenterlines':sum(not b.isSolid for b in current.bRepBodies),
         'bondingFootprintXYXY_mm':[-4.38934,-24,1.61066,-22],'strainReliefStatus':'SITE_ALLOCATION_ONLY_NO_IMPLEMENTED_RESTRAINT',
         'timelineIssues':issues,'saved':False}
    (BASE/'docs/battery-service-loop-development.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out))
