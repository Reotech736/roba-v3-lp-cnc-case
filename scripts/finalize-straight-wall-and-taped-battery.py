"""One-time finalize v28 working revision: right wall and fixture retirement."""
import adsk.core,adsk.fusion,json
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')
def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber==28 and doc.isModified
    read=lambda name:json.loads((BASE/'docs'/name).read_text(encoding='utf-8'))
    wall=read('positive-x-straight-wall-development.json');retired=read('battery-fixture-retirement.json');prior=read('current-approved-component-state.json')
    actual={o.fullPathName:o for o in root.allOccurrences};mapping={r['old']:r['new'] for r in retired['renameMap']}
    for r in prior:
        path=r['path']
        for old,new in mapping.items():path=path.replace(old+':',new+':')
        o=actual[path];assert max(abs(a-b) for a,b in zip(r['matrix'],o.transform2.asArray()))<1e-8;assert r['bodies']==o.component.bRepBodies.count
        expected=[wall['after'][r['name']]['volume_mm3']] if r['name'] in wall['after'] else r['volumes']
        assert all(abs(v-b.volume*1000)<1e-5 for v,b in zip(expected,o.component.bRepBodies))
    assert read('fastening-and-overhang-current-audit.json')['obstructedM2Axes']==0
    assert read('upper-support-relief-verification.json')['activeReliefTiersMatched']==8
    assert all(r['obstructingPocketMaterial_mm3']<1e-5 and r['missingResidualMaterial_mm3']<1e-5 for r in read('corrected-stand-solid-verification.json')['pocketAndResidualVolumeChecks'])
    assert all(not r['count'] for r in read('detailed-choc-fit-verification.json')['results'])
    assert not read('taped-battery-envelope-verification.json')['rows'][0]['collisions']
    for gap in [0,2,5,8,10]:assert all(not r['obstructions'] for r in read(f'pcb-fixed-lead-verification-gap{gap}.json')['leads'])
    mgr=adsk.fusion.TemporaryBRepManager.get();solidProof=[]
    for prefix,z0,z1 in [('Lower_L_',-11.5,-1),('Upper_L_',-1,4.5)]:
        o=next(o for o in root.occurrences if o.component.name.startswith(prefix));b=o.bRepBodies.item(0);assert o.component.bRepBodies.count==1
        # Complete thin outer stock strip, not just edge endpoints.
        strip=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create((16.276167+16.576167)/20,-3.8,(z0+z1)/20),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),.03,4.2,(z1-z0)/10))
        expected=strip.volume*1000;assert mgr.booleanOperation(strip,mgr.copy(b),adsk.fusion.BooleanTypes.IntersectionBooleanType);missing=expected-strip.volume*1000;assert abs(missing)<1e-5
        assert b.material.name=='JLCCNC_6061_T6_SUPPLIER_MINIMUM_PROVISIONAL'
        solidProof.append({'component':o.component.name,'outerStripThickness_mm':.3,'length_mm':42,'missingMaterial_mm3':max(0,missing)})
    assert not any(o.component.name=='pin3' for o in root.allOccurrences)
    stems=[o for o in root.allOccurrences if o.component.name=='stem'];assert len(stems)==23 and all(abs(o.bRepBodies.item(0).preciseBoundingBox.maxPoint.z*10-10.2)<1e-6 for o in stems)
    assert not [t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage] and not d.snapshots.hasPendingSnapshot
    assert doc.save('Straight right42mm wall atX16.576167; recut M2 holes and retained bracket relief. Retire optional battery receiver, wire fixture and old adhesives as hidden comparisons; provisionalPCB-side tape/insulation concept, same cell position. Actual bonding,bend,adhesion and PCB revision unqualified.')
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(BASE/'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d')))
    current=[]
    for o in root.allOccurrences:
        if o.component.name in ['BATTERY_ASSEMBLY_CELL42_WIRE40_PROVISIONAL','CLEARANCE_STUDIES_NOT_PARTS']:continue
        current.append({'name':o.component.name,'path':o.fullPathName,'matrix':list(o.transform2.asArray()),'bodies':o.component.bRepBodies.count,'volumes':[b.volume*1000 for b in o.component.bRepBodies]})
    assert len(current)==589
    (BASE/'docs/current-approved-component-state.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    result={'date':'2026-11-10','baselineCloudVersion':28,'saveRequested':True,'approvedRecords':589,'renameCount':len(mapping),'onlyCaseGeometryChanged':True,'allOriginalTransformsPreserved':True,'outerStraightStockProof':solidProof,'leftContactEdgePreserved':True,'batteryPhysicalCandidates':1,'retiredFixtureAndAdhesiveCandidates':4,'currentBatteryMountingConcept':'PCB-side tape and insulation, actual mounting face/padding/adhesion unqualified','dedicatedFixturesRequired':False,'rightM2HolesAndExistingBracketReliefPreserved':True,'currentCaseVolumes_mm3':{k:v['volume_mm3'] for k,v in wall['after'].items()},'actualAttachmentVerified':False,'manufactureReady':False,'F3DUpdated':True}
    (BASE/'docs/straight-wall-and-taped-battery-final-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
