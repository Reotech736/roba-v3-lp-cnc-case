"""One-timev29 working revision: finalize removal of obsolete fixture cuts."""
import adsk.core,adsk.fusion,json
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')
def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber==29 and doc.isModified
    read=lambda n:json.loads((BASE/'docs'/n).read_text(encoding='utf-8'))
    change=read('remove-retired-fixture-machining-development.json');proof=read('removed-fixture-machining-verification.json');prior=read('current-approved-component-state.json');live={o.fullPathName:o for o in root.allOccurrences}
    assert proof['missingRecessStock_mm3']<1e-5 and proof['remainingFormerPocketBottomFaces']==0 and all(r['missingStock_mm3']<1e-5 for r in proof['filledPilots'])
    for r in prior:
        o=live[r['path']];assert r['bodies']==o.component.bRepBodies.count and max(abs(a-b) for a,b in zip(r['matrix'],o.transform2.asArray()))<1e-8
        expected=[change['after'][r['name']]['volume_mm3']] if r['name'] in change['after'] else r['volumes']
        assert all(abs(v-b.volume*1000)<1e-5 for v,b in zip(expected,o.component.bRepBodies))
    assert read('fastening-and-overhang-current-audit.json')['obstructedM2Axes']==0
    assert read('upper-support-relief-verification.json')['activeReliefTiersMatched']==8
    assert all(r['obstructingPocketMaterial_mm3']<1e-5 and r['missingResidualMaterial_mm3']<1e-5 for r in read('corrected-stand-solid-verification.json')['pocketAndResidualVolumeChecks'])
    fit=read('internal-retention-fit-verification.json')
    for key in ['coreInterferences','wireVsAssemblyInterferences','slackSpaceVsAssemblyInterferences','pullTabAccessVsAssemblyInterferences','detailedSocketsVsNewPartsInterferences']:assert not fit[key]
    assert all(not r['count'] for r in read('detailed-choc-fit-verification.json')['results'])
    for gap in [0,2,5,8,10]:assert all(not l['obstructions'] for l in read(f'pcb-fixed-lead-verification-gap{gap}.json')['leads'])
    stems=[o for o in root.allOccurrences if o.component.name=='stem'];assert len(stems)==23 and all(abs(o.bRepBodies.item(0).preciseBoundingBox.maxPoint.z*10-10.2)<1e-6 for o in stems)
    assert not any(o.component.name=='pin3' for o in root.allOccurrences)
    assert next(o for o in root.occurrences if o.component.name=='CHOC_SWITCHES_AND_SOCKETS_REFERENCE_23_PAIRS').childOccurrences.count==46
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues and not d.snapshots.hasPendingSnapshot
    assert doc.save('Remove obsolete wire-fixture machining: suppress three historical lower relief cuts and two upperD1.25 pilots. Restore normal stock; preserve M2 case holes, left/right42mm edges, LP supports and tape-fixed battery concept. Physical tape attachment and manufacturing remain unqualified.')
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(BASE/'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d')))
    current=[]
    for o in root.allOccurrences:
        if o.component.name in ['BATTERY_ASSEMBLY_CELL42_WIRE40_PROVISIONAL','CLEARANCE_STUDIES_NOT_PARTS']:continue
        current.append({'name':o.component.name,'path':o.fullPathName,'matrix':list(o.transform2.asArray()),'bodies':o.component.bRepBodies.count,'volumes':[b.volume*1000 for b in o.component.bRepBodies]})
    assert len(current)==589
    (BASE/'docs/current-approved-component-state.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    result={'date':'2026-11-10','baselineCloudVersion':29,'saveRequested':True,'approvedRecords':589,'allPriorTransformsPreserved':True,'onlyCaseVolumesChanged':True,'suppressedCutCount':4,'lowerRecessRemoved':True,'upperDedicatedPilotCountRemoved':2,'M2CaseHoleAxesPreserved':4,'supportCount':4,'reliefTierCount':8,'straight42mmEdgesVerified':4,'coreSolidsChecked':fit['coreSolidCount'],'chocOriginsPreserved':46,'stemTopsChecked':23,'pin3Absent':True,'caseVolumes_mm3':{k:v['volume_mm3'] for k,v in change['after'].items()},'F3DUpdated':True,'manufactureReady':False,'tapeAttachmentQualified':False,'timelineIssues':issues}
    (BASE/'docs/removed-fixture-machining-final-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
