"""One-timev29: suppress all three historical lower relief cuts and two pilots.

Keep feature history, current unsaved state backup, M2 case holes, both42mm
sides, reference models and retired fixture definitions. Do not patch with a
generic rectangular plug that could intrude into adjacent functional geometry.
"""
import adsk.core,adsk.fusion,json
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')
def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:H9Nq8f1PSl6GXmxJMgIkbw' and doc.dataFile.versionNumber==29
    prior=json.loads((BASE/'docs/current-approved-component-state.json').read_text(encoding='utf-8'));live={o.fullPathName:o for o in root.allOccurrences};assert len(prior)==589
    for r in prior:
        o=live[r['path']];assert r['bodies']==o.component.bRepBodies.count
        assert max(abs(a-b) for a,b in zip(r['matrix'],o.transform2.asArray()))<1e-8
        assert all(abs(v-b.volume*1000)<1e-5 for v,b in zip(r['volumes'],o.component.bRepBodies))
    checkpoint=BASE/'cad/design/checkpoints/v05_cloud_v29_WORKING_before_remove_retired_fixture_machining.f3d';assert not checkpoint.exists()
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(checkpoint)))
    names=['Restore_existing_lower_wire_bracket_relief_after_straight_wall','Recut_wire_bracket_relief_after_backing_join_0p3_clearance','Case_wire_bracket_M1p6_pilots_D1p25_depth3p6_THREAD_NOT_MODELED','Case_wire_bracket_removable_lower_clearance_0p3']
    cases=[next(o for o in root.occurrences if o.component.name.startswith(p)) for p in ['Lower_L_','Upper_L_']]
    bounds=lambda b:[[v*10 for v in p.asArray()] for p in [b.preciseBoundingBox.minPoint,b.preciseBoundingBox.maxPoint]]
    before={o.component.name:{'volume_mm3':o.component.bRepBodies.item(0).volume*1000,'boundsGlobal_mm':bounds(o.bRepBodies.item(0))} for o in cases}
    suppressed=[]
    for name in names:
        matches=[t for t in d.timeline if t.name==name];assert len(matches)==1 and not matches[0].isSuppressed
        feature=matches[0].entity;feature.isSuppressed=True;assert feature.isSuppressed;suppressed.append({'name':name,'timelineIndex':matches[0].index})
    assert d.computeAll();issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues
    after={}
    for o in cases:
        assert o.component.bRepBodies.count==1 and o.component.bRepBodies.item(0).material.name=='JLCCNC_6061_T6_SUPPLIER_MINIMUM_PROVISIONAL'
        after[o.component.name]={'volume_mm3':o.component.bRepBodies.item(0).volume*1000,'boundsGlobal_mm':bounds(o.bRepBodies.item(0))}
        assert max(abs(a-b) for aa,bb in zip(before[o.component.name]['boundsGlobal_mm'],after[o.component.name]['boundsGlobal_mm']) for a,b in zip(aa,bb))<1e-5
    for r in prior:
        o=live[r['path']];assert max(abs(a-b) for a,b in zip(r['matrix'],o.transform2.asArray()))<1e-8
        if not o.component.name.startswith(('Upper_L_','Lower_L_')):assert r['bodies']==o.component.bRepBodies.count and all(abs(v-b.volume*1000)<1e-5 for v,b in zip(r['volumes'],o.component.bRepBodies))
    result={'date':'2026-11-10','baselineCloudVersion':29,'suppressedCuts':suppressed,'before':before,'after':after,'previousRecordsChecked':589,'onlyCaseVolumesChanged':True,'allPreviousTransformsPreserved':True,'caseBoundsUnchanged':True,'singleSolidCases':2,'timelineIssues':issues,'saved':False,'limitations':['Removed only retired fixture machining; actual taped attachment, realwire bending and manufacturing remain unqualified']}
    (BASE/'docs/remove-retired-fixture-machining-development.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
