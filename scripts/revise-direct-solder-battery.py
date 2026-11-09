"""One-time v22 -> v23 direct-solder study. Run only after read-only checks complete.

Does not change case, switch, PCB, battery carrier, source data or their placement.
Retires obsolete connector reservations and adds a hidden direct-wire study.
"""
import adsk.core,adsk.fusion,json,math
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')
PHASE='check'  # check is readOnly; replace with apply only after reviewing its JSON.


def run(_context: str):
    app=adsk.core.Application.get()
    doc=next(x for x in app.documents if x.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE')
    assert doc.dataFile.versionNumber==22 and not doc.isModified
    assert app.activeDocument==doc,'Activate the current design before running'
    d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    assert not d.snapshots.hasPendingSnapshot
    study=json.loads((BASE/'docs/direct-solder-battery-study.json').read_text(encoding='utf-8'))
    assert study['userConfirmed']['connection'].startswith('Direct solder')
    before=[{'path':o.fullPathName,'name':o.component.name,'matrix':list(o.transform2.asArray()),
             'volumes':[b.volume*1000 for b in o.component.bRepBodies],'visible':o.isLightBulbOn} for o in root.allOccurrences]
    assert not any(o.component.name.startswith('BATTERY_WIRE_ROUTE_D3_DIRECT_SOLDER_') for o in root.allOccurrences)
    mgr=adsk.fusion.TemporaryBRepManager.get()
    def point(p):return adsk.core.Point3D.create(*[v/10 for v in p])
    route=study['bundleRoute_mm'][1:];r=study['bundleRadius_mm']/10
    wire=mgr.createSphere(point(route[0]),r)
    for a,b in zip(route,route[1:]):
        assert mgr.booleanOperation(wire,mgr.createCylinderOrCone(point(a),r,point(b),r),adsk.fusion.BooleanTypes.UnionBooleanType)
        assert mgr.booleanOperation(wire,mgr.createSphere(point(b),r),adsk.fusion.BooleanTypes.UnionBooleanType)
    for branch in study['branches']:
        a,b=branch['wireCenterRoute_mm'][-2:];r=.05
        assert mgr.booleanOperation(wire,mgr.createCylinderOrCone(point(a),r,point(b),r),adsk.fusion.BooleanTypes.UnionBooleanType)
        assert mgr.booleanOperation(wire,mgr.createSphere(point(b),r),adsk.fusion.BooleanTypes.UnionBooleanType)
    # Check physical targets before any document change. Exclude obsolete connector studies.
    targets=[]
    prefixes=('Lower_L_','Upper_L_','MCU_RAISED_','PCB_L_','PCB_SUPPORT_INSULATION_','BATTERY_REMOVABLE_CARRIER_',
              'BATTERY_CELL_NOMINAL_42','CARRIER_BASE_REMOVABLE_','CELL_REMOVABLE_ADHESIVE_')
    for o in root.allOccurrences:
        if o.component.name.startswith(prefixes):targets.extend((o.component.name,b) for b in o.bRepBodies)
    def walk(o):
        for b in o.bRepBodies:yield o.component.name,b
        for ch in o.childOccurrences:yield from walk(ch)
    for o in root.allOccurrences:
        if o.component.name.startswith(('CHOC_SOCKET_DETAILED_','CHOC_V2_RED_')):targets.extend(walk(o))
    collisions=[]
    candidates=0
    journal=BASE/'docs/direct-solder-battery-check-progress.json'
    for index,(name,b) in enumerate(targets):
        bb,other=wire.boundingBox,b.boundingBox
        # Coincident boundary contact has no positive volume. Avoid feeding
        # tangent-only, complex proxy geometry to the boolean kernel.
        if any(min(getattr(bb.maxPoint,axis),getattr(other.maxPoint,axis))-max(getattr(bb.minPoint,axis),getattr(other.minPoint,axis))<=1e-7 for axis in ['x','y','z']):continue
        candidates+=1
        journal.write_text(json.dumps({'stage':'before_boolean','index':index,'target':name,'phase':PHASE}),encoding='utf-8')
        copy=mgr.copy(wire);assert mgr.booleanOperation(copy,b,adsk.fusion.BooleanTypes.IntersectionBooleanType)
        if copy.volume*1000>1e-5:collisions.append({'target':name,'volume_mm3':copy.volume*1000})
        journal.write_text(json.dumps({'stage':'after_boolean','index':index,'target':name,'phase':PHASE}),encoding='utf-8')
    report={'date':'2026-11-08','baselineCloudVersion':22,'temporaryWireCollisions':collisions,
            'physicalTargetsChecked':len(targets),'positiveBBoxCandidates':candidates,'wireReservationVolume_mm3':wire.volume*1000}
    (BASE/'docs/direct-solder-battery-geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert not collisions,str(collisions)
    if PHASE=='check':
        print(json.dumps(report));return
    assert PHASE=='apply'
    checkpoint=BASE/'cad/design/checkpoints/v05_cloud_v22_before_direct_solder_battery.f3d'
    assert not checkpoint.exists(),'Do not overwrite a checkpoint'
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(checkpoint)))
    retired=[]
    for prefix in ['B1_JST_PH_SMD_','B1_MATING_PLUG_ACCESS_','BATTERY_WIRE_ROUTE_D3_CELL42_']:
        found=[o for o in root.allOccurrences if o.component.name.startswith(prefix)]
        assert len(found)==1,str((prefix,len(found)))
        o=found[0];old=o.component.name
        o.component.name='RETIRED_CONNECTOR_VARIANT_'+old;o.isLightBulbOn=False
        retired.append({'oldName':old,'newName':o.component.name})
    studies=next(o for o in root.allOccurrences if o.component.name=='CLEARANCE_STUDIES_NOT_PARTS')
    assert max(abs(a-b) for a,b in zip(studies.transform2.asArray(),adsk.core.Matrix3D.create().asArray()))<1e-8
    occ=studies.component.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name='BATTERY_WIRE_ROUTE_D3_DIRECT_SOLDER_B1_40mm_BUDGET_NOT_PART'
    feature=occ.component.features.baseFeatures.add();feature.name='Direct_solder_B1_bundle_D3_branches_D1_ASSUMED'
    assert feature.startEdit();occ.component.bRepBodies.add(wire,feature);assert feature.finishEdit();occ.isLightBulbOn=False
    assert d.computeAll()
    after={o.fullPathName:o for o in root.allOccurrences}
    # Paths of renamed instances change: resolve by preserved component identity through order.
    remaining=[o for o in root.allOccurrences if not o.component.name.startswith('BATTERY_WIRE_ROUTE_D3_DIRECT_SOLDER_')]
    assert len(remaining)==len(before)
    for old,new in zip(before,remaining):
        assert max(abs(a-b) for a,b in zip(old['matrix'],new.transform2.asArray()))<1e-8,old['name']
        assert len(old['volumes'])==new.component.bRepBodies.count
        assert all(abs(v-b.volume*1000)<1e-5 for v,b in zip(old['volumes'],new.component.bRepBodies)),old['name']
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    report.update(retiredStudies=retired,allPreviousTransformsAndVolumesPreserved=True,
                  caseGeometryChanged=False,timelineIssues=issues,checkpoint=str(checkpoint),
                  limitations=study['limitations'],status='DIRECT_SOLDER_PROVISIONAL_GEOMETRY_CHECKED_NOT_MANUFACTURING_APPROVAL')
    (BASE/'docs/direct-solder-battery-geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert doc.save('Direct solder battery: 40 mm from pouch exit to PCB B1 solder pads. Retire connector and plug studies; add hidden D3 bundle/D1 branches. Preserve all cases, references, placements and group hierarchy.')
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(BASE/'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d')))
    approved=[]
    for o in root.allOccurrences:
        if o.component.name in ['BATTERY_ASSEMBLY_CELL42_WIRE40_PROVISIONAL','CLEARANCE_STUDIES_NOT_PARTS']:continue
        approved.append({'name':o.component.name,'path':o.fullPathName,'matrix':list(o.transform2.asArray()),
                         'bodies':o.component.bRepBodies.count,'volumes':[b.volume*1000 for b in o.component.bRepBodies]})
    (BASE/'docs/current-approved-component-state.json').write_text(json.dumps(approved,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ['limitations','checkpoint']},ensure_ascii=False))
