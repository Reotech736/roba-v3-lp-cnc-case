"""Save one-time v24 working revision after loop/site/subset verification."""
import adsk.core,adsk.fusion,json
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')


def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber==24
    proof=json.loads((BASE/'docs/battery-service-loop-development.json').read_text())
    assert proof['previousTransformsAndVolumesPreserved'] and not proof['caseAndCarrierGeometryChanged']
    fit=json.loads((BASE/'docs/internal-retention-fit-verification.json').read_text())
    for name in ['coreInterferences','wireVsAssemblyInterferences','slackSpaceVsAssemblyInterferences','pullTabAccessVsAssemblyInterferences','detailedSocketsVsNewPartsInterferences']:assert not fit[name],name
    approved=json.loads((BASE/'docs/current-approved-component-state.json').read_text(encoding='utf-8'))
    live={o.fullPathName:o for o in root.allOccurrences}
    for row in approved:
        o=live.get(row['path'])
        if o is None:
            assert row['name']=='BATTERY_WIRE_ROUTE_D3_DIRECT_SOLDER_B1_40mm_BUDGET_NOT_PART'
            o=next(o for o in root.allOccurrences if o.component.name=='RETIRED_MINIMUM_PATH_'+row['name'])
        assert o.component.bRepBodies.count==row['bodies']
        assert max(abs(a-b) for a,b in zip(row['matrix'],o.transform2.asArray()))<1e-8
        assert all(abs(v-b.volume*1000)<1e-5 for v,b in zip(row['volumes'],o.component.bRepBodies))
    assert not any(o.component.name=='pin3' for o in root.allOccurrences)
    stems=[o for o in root.allOccurrences if o.component.name=='stem'];assert len(stems)==23
    assert all(abs(o.bRepBodies.item(0).boundingBox.maxPoint.z*10-10.2)<1e-6 for o in stems)
    choc=next(o for o in root.occurrences if o.component.name=='CHOC_SWITCHES_AND_SOCKETS_REFERENCE_23_PAIRS');assert choc.childOccurrences.count==46
    battery=next(o for o in root.occurrences if o.component.name=='BATTERY_ASSEMBLY_CELL42_WIRE40_PROVISIONAL');assert battery.childOccurrences.count==5
    studies=next(o for o in root.allOccurrences if o.component.name=='CLEARANCE_STUDIES_NOT_PARTS');assert studies.childOccurrences.count==10
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues
    assert not d.snapshots.hasPendingSnapshot
    assert doc.save('Nominal40mm battery service loop: R3/D3 study, separate 0/2/5/8/10mm poses checked by exact curve distances. Reserve PCB6x2 bonding site only; no completed strain relief. Preserve cases, source parts and Choc placement.')
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(BASE/'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d')))
    current=[]
    for o in root.allOccurrences:
        if o.component.name in ['BATTERY_ASSEMBLY_CELL42_WIRE40_PROVISIONAL','CLEARANCE_STUDIES_NOT_PARTS']:continue
        current.append({'name':o.component.name,'path':o.fullPathName,'matrix':list(o.transform2.asArray()),'bodies':o.component.bRepBodies.count,'volumes':[b.volume*1000 for b in o.component.bRepBodies]})
    (BASE/'docs/current-approved-component-state.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    out={'date':'2026-11-08','baselineCloudVersion':24,'cloudVersionAtSaveRequest':doc.dataFile.versionNumber,
         'previousApprovedRecordsChecked':len(approved),'currentApprovedRecords':len(current),
         'ChocOriginsPreserved':46,'stemTopsChecked':23,'pin3Absent':True,'timelineIssues':issues,
         'batteryPhysicalOccurrences':4,'batteryStudyOccurrences':10,'currentF3DUpdated':True,
         'caseSTEPVersions':{'upper':22,'lower':20},'caseGeometryChanged':False,
         'continuousMotionCertified':False,'strainReliefImplemented':False,'nominalR3LoopPosesChecked_mm':[0,2,5,8,10]}
    (BASE/'docs/battery-service-loop-final-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out))
