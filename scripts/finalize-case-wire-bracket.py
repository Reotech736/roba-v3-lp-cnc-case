"""One-time save/export after all local and regression checks on v25 working state.

The initial non-root lower export proved empty despite execute()==True. Do not
treat this stage as STEP delivery completion; run export-verify-current-case-steps.py
after cloud v26 is complete, and require its three round-trip results.
"""
import adsk.core,adsk.fusion,json
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')


def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber==25
    def read(name):return json.loads((BASE/'docs'/name).read_text(encoding='utf-8'))
    verification=read('case-wire-bracket-verification.json')
    assert not verification['bracketVsPhysicalAndWireCollisions']
    assert all(not r['collisionsExcludingUpperThreadMajorOverlap'] for r in verification['hardwareStudies'])
    assert all(not r['collisions'] for r in verification['driverChecks'])
    assert verification['nominal1p1WallMissingMaterial_mm3']<1e-5 and verification['lowerMaxBoundsUnchanged']
    for row in verification['newHoleChecks']:
        for key in ['upperD1p25PilotObstruction_mm3','bracketD1p8ClearanceObstruction_mm3','headAnnulusSupportMissing_mm3']:assert row[key]<1e-5
    fit=read('internal-retention-fit-verification.json')
    for key in ['coreInterferences','wireVsAssemblyInterferences','slackSpaceVsAssemblyInterferences','pullTabAccessVsAssemblyInterferences','detailedSocketsVsNewPartsInterferences']:assert not fit[key]
    assert read('fastening-and-overhang-current-audit.json')['obstructedM2Axes']==0
    assert read('upper-support-relief-verification.json')['activeReliefTiersMatched']==8
    assert not read('case-wire-bracket-contact-verification.json')['positiveQuadrantViolations']
    assert all(not r['count'] for r in read('detailed-choc-fit-verification.json')['results'])
    stand=read('corrected-stand-solid-verification.json')
    assert all(r['obstructingPocketMaterial_mm3']<1e-5 and r['missingResidualMaterial_mm3']<1e-5 for r in stand['pocketAndResidualVolumeChecks'])
    for gap in [0,2,5,8,10]:assert not read(f'battery-service-loop-verification-gap{gap}.json')['rows'][0]['obstructions']
    lower=next(o for o in root.occurrences if o.component.name.startswith('Lower_L_'));upper=next(o for o in root.occurrences if o.component.name.startswith('Upper_L_'))
    bracket=next(o for o in root.allOccurrences if o.component.name.startswith('WIRE_STRAIN_RELIEF_CASE_BRACKET_'))
    assert lower.component.bRepBodies.count==upper.component.bRepBodies.count==bracket.component.bRepBodies.count==1
    before=read('case-wire-bracket-baseline.json');actual={o.fullPathName:o for o in root.allOccurrences}
    changed={lower.component.name,upper.component.name}
    for row in before:
        o=actual.get(row['path'])
        if o is None:
            assert row['name'].startswith('PCB_WIRE_STRAIN_RELIEF_BOND_FOOTPRINT_')
            o=next(o for o in root.allOccurrences if o.component.name=='RETIRED_PCB_BONDING_ALTERNATIVE_'+row['name'])
        assert max(abs(a-b) for a,b in zip(row['matrix'],o.transform2.asArray()))<1e-8
        if o.component.name not in changed:
            assert len(row['volumes'])==o.component.bRepBodies.count
            assert all(abs(v-b.volume*1000)<1e-5 for v,b in zip(row['volumes'],o.component.bRepBodies))
    choc=next(o for o in root.occurrences if o.component.name=='CHOC_SWITCHES_AND_SOCKETS_REFERENCE_23_PAIRS');assert choc.childOccurrences.count==46
    stems=[o for o in root.allOccurrences if o.component.name=='stem'];assert len(stems)==23 and all(abs(o.bRepBodies.item(0).boundingBox.maxPoint.z*10-10.2)<1e-6 for o in stems)
    assert not any(o.component.name=='pin3' for o in root.allOccurrences)
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues and not d.snapshots.hasPendingSnapshot
    for comp,file in [(lower.component,'left_case_two_stands_v05_NOT_FOR_MANUFACTURE_Lower_L_LOCAL.step'),(upper.component,'left_case_two_stands_v05_NOT_FOR_MANUFACTURE_Upper_L_protective_roof_LOCAL.step'),(bracket.component,'wire_strain_relief_case_bracket_NONMETAL_NOT_FOR_MANUFACTURE_LOCAL.step')]:
        assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(str(BASE/'cad/design'/file),comp))
    assert doc.save('Case-mounted nonmetal wire restraint prototype: two M1.6x4 mounts, D3.4 cradle, adjustable tie slots. Join/re-cut lower pocket backing; verify 1.1mm local wall, M2 holes, stands, support reliefs and42mm contact edge. Actual tie force/material/R3 wire bending unqualified.')
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(BASE/'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d')))
    current=[]
    for o in root.allOccurrences:
        if o.component.name in ['BATTERY_ASSEMBLY_CELL42_WIRE40_PROVISIONAL','CLEARANCE_STUDIES_NOT_PARTS']:continue
        current.append({'name':o.component.name,'path':o.fullPathName,'matrix':list(o.transform2.asArray()),'bodies':o.component.bRepBodies.count,'volumes':[b.volume*1000 for b in o.component.bRepBodies]})
    (BASE/'docs/current-approved-component-state.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    battery=next(o for o in root.occurrences if o.component.name=='BATTERY_ASSEMBLY_CELL42_WIRE40_PROVISIONAL');studies=next(o for o in root.allOccurrences if o.component.name=='CLEARANCE_STUDIES_NOT_PARTS')
    assert battery.childOccurrences.count==6 and studies.childOccurrences.count==12
    result={'date':'2026-11-09','baselineCloudVersion':25,'cloudVersionAtSaveRequest':doc.dataFile.versionNumber,'savedRequested':True,
            'approvedRecords':len(current),'previousRecordsChecked':len(before),'caseAndBracketSingleSolids':3,
            'caseSTEPsUpdated':True,'bracketSTEPExported':True,'currentF3DUpdated':True,'chocOriginsPreserved':46,'stemTopsChecked':23,'pin3Absent':True,'timelineIssues':issues,
            'batteryPhysicalCandidateOccurrences':5,'batteryStudyOccurrences':12,'PCBAdhesiveRequired':False,
            'wireODUserApprox_mm':1,'nominalEachLeadLength_mm':40,'wireMinimumBendRadiusVerified':False,'continuousOpeningVerified':False,
            'restraintHardwarePrototypeImplemented':True,'retentionForceQualified':False,
            'upperVolume_mm3':upper.component.bRepBodies.item(0).volume*1000,'lowerVolume_mm3':lower.component.bRepBodies.item(0).volume*1000,'bracketVolume_mm3':bracket.component.bRepBodies.item(0).volume*1000}
    (BASE/'docs/case-wire-bracket-final-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
