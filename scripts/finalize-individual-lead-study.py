"""One-time save/export of v27 working study as next cloud version.

Only two clearance-study children are added; all587 previous records preserved.
Physical STEP geometry/material stays at v27, so no physical STEP re-export.
"""
import adsk.core,adsk.fusion,json,math
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')

def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber==27 and doc.isModified
    prior=json.loads((BASE/'docs/current-approved-component-state.json').read_text(encoding='utf-8'));live={o.fullPathName:o for o in root.allOccurrences}
    assert len(prior)==587
    for r in prior:
        o=live[r['path']];assert r['bodies']==o.component.bRepBodies.count
        assert max(abs(a-b) for a,b in zip(r['matrix'],o.transform2.asArray()))<1e-8
        assert all(abs(v-b.volume*1000)<1e-5 for v,b in zip(r['volumes'],o.component.bRepBodies))
    closed=next(o for o in root.allOccurrences if o.component.name=='BATTERY_TWO_D1_LEADS40_CLOSED_GEOMETRY_TRIAL_NOT_PARTS')
    opened=next(o for o in root.allOccurrences if o.component.name=='BATTERY_TWO_D1_LEADS40_OPEN_POSES_NOT_CONTINUOUS_MOTION')
    assert closed.component.bRepBodies.count==2 and opened.component.bRepBodies.count==8
    assert not closed.isLightBulbOn and not opened.isLightBulbOn
    volume=[b.volume*1000 for b in closed.component.bRepBodies];assert all(abs(v-10*math.pi)<1e-6 for v in volume)
    surfaceGap=app.measureManager.measureMinimumDistance(closed.bRepBodies.item(0),closed.bRepBodies.item(1)).value*10;assert surfaceGap>.24
    study=json.loads((BASE/'docs/individual-battery-lead-study.json').read_text(encoding='utf-8'));assert study['fixedTerminalLastFourSegmentsMaxDeviation_mm']<1e-8
    pairMargins=[]
    for gap in [0,2,5,8,10]:
        r=json.loads((BASE/f'docs/individual-lead-verification-gap{gap}.json').read_text(encoding='utf-8'))
        assert all(not lead['obstructions'] for lead in r['leads']);assert r['pairD1SurfaceMargin_mm']>.1;pairMargins.append(r['pairD1SurfaceMargin_mm'])
    assert not any(o.component.name=='pin3' for o in root.allOccurrences)
    stems=[o for o in root.allOccurrences if o.component.name=='stem'];assert len(stems)==23 and all(abs(o.bRepBodies.item(0).preciseBoundingBox.maxPoint.z*10-10.2)<1e-6 for o in stems)
    for prefix in ['Upper_L_','Lower_L_']:
        c=next(c for c in d.allComponents if c.name.startswith(prefix));assert c.bRepBodies.count==1 and c.bRepBodies.item(0).material.name=='JLCCNC_6061_T6_SUPPLIER_MINIMUM_PROVISIONAL'
    assert not [t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage] and not d.snapshots.hasPendingSnapshot
    assert doc.save('Individual40mm lead geometric trial: hidden twoD1 pipes and eight independent open-pose centerlines. Existing587 records and physical parts unchanged. R1/R1.5/R3, exit spacing and terminal exclusions remain assumptions; installed tie and real wire bending unqualified.')
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(BASE/'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d')))
    current=[]
    for o in root.allOccurrences:
        if o.component.name in ['BATTERY_ASSEMBLY_CELL42_WIRE40_PROVISIONAL','CLEARANCE_STUDIES_NOT_PARTS']:continue
        current.append({'name':o.component.name,'path':o.fullPathName,'matrix':list(o.transform2.asArray()),'bodies':o.component.bRepBodies.count,'volumes':[b.volume*1000 for b in o.component.bRepBodies]})
    assert len(current)==589
    (BASE/'docs/current-approved-component-state.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    result={'date':'2026-11-09','baselineCloudVersion':27,'cloudVersionAtSaveRequest':doc.dataFile.versionNumber,'saveRequested':True,'previousApprovedRecordsPreserved':587,'approvedRecords':589,'addedClosedD1StudySolids':2,'addedOpenPoseWireBodies':8,'physicalPartGeometryAndPlacementChanged':False,'physicalCaseMaterialPreserved':True,'physicalSTEPVersions':{'upper':27,'lower':27,'bracket':27},'closedPipeVolumes_mm3':volume,'closedPipeSurfaceGap_mm':surfaceGap,'minimumIndependentPosePairMargin_mm':min(pairMargins),'batteryStudyChildren':14,'pin3Absent':True,'stemTopsChecked':23,'actualMinimumBendSpecificationVerified':False,'installedTieRoutingVerified':False,'continuousFlexibleMotionVerified':False,'F3DExported':True}
    (BASE/'docs/individual-lead-final-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
