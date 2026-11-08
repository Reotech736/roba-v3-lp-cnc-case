# Historical unsuccessful attempt; retained for investigation only.
# Do not run. Use organize-current-components.py and set-current-review-visibility.py.
"""Fusion MCP: group current battery parts and clearance studies, preserving poses."""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'

def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    raise RuntimeError('Historical failed attempt: use organize-current-components.py instead')
    assert doc.dataFile.versionNumber==16 and not any(o.component.name.startswith('BATTERY_ASSEMBLY_') for o in root.occurrences)
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/checkpoints/v05_cloud_v16_before_battery_browser_group.f3d'))
    prefixes=('BATTERY_REMOVABLE_CARRIER_','CARRIER_BASE_REMOVABLE_','CELL_REMOVABLE_ADHESIVE_','BATTERY_CELL_NOMINAL_42','CELL42_INSTALLATION_SPACE_','CELL_ADHESIVE_PULL_TAB_','BATTERY_WIRE_ROUTE_','BATTERY_SERVICE_SLACK_','B1_JST_','B1_MATING_')
    refs=[o for o in root.occurrences if o.component.name.startswith(prefixes)];assert len(refs)==10
    def state(o):
        b=o.boundingBox
        return dict(matrix=o.transform2.asArray(),bounds=[[p.x,p.y,p.z] for p in [b.minPoint,b.maxPoint]],visible=o.isLightBulbOn)
    preflight=json.load(open(BASE+'docs/battery-group-preflight.json',encoding='utf-8'))
    assert preflight['allTenStillAtRoot'] and preflight['version']==16
    expected={v['name']:v for v in preflight['objects']}
    assert {o.component.name for o in refs}==set(expected)
    for o in refs:
        assert max(abs(x-y) for x,y in zip(o.transform2.asArray(),expected[o.component.name]['matrix']))<1e-8
    before=[state(o) for o in refs]
    top=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());top.component.name='BATTERY_ASSEMBLY_CELL42_WIRE40_PROVISIONAL'
    physical=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());physical.component.name='BATTERY_PARTS_CELL_CARRIER_ADHESIVE'
    study=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());study.component.name='BATTERY_CLEARANCE_STUDIES_NOT_PARTS'
    physicalContext=physical;studyContext=study
    checks=[]
    for o,expected in zip(refs,before):
        ispart=o.component.name.startswith(('BATTERY_REMOVABLE_CARRIER_','CARRIER_BASE_REMOVABLE_','CELL_REMOVABLE_ADHESIVE_','BATTERY_CELL_NOMINAL_42'))
        moved=o.moveToComponent(physicalContext if ispart else studyContext);assert moved, 'MOVE_FAILED: '+o.component.name
        actual=state(moved)
        assert max(abs(x-y) for x,y in zip(actual['matrix'],expected['matrix']))<1e-8, 'MATRIX_CHANGED: '+moved.component.name
        assert max(abs(x-y) for p,q in zip(actual['bounds'],expected['bounds']) for x,y in zip(p,q))<1e-8, 'BOUNDS_CHANGED: '+moved.component.name
        assert actual['visible']==expected['visible'], 'VISIBILITY_CHANGED: '+moved.component.name;checks.append(dict(name=moved.component.name,physicalPart=ispart,poseBoundsVisibilityPreserved=True))
    assert physical.component.occurrences.count==4 and study.component.occurrences.count==6, 'COUNTS: '+str((physical.component.occurrences.count,study.component.occurrences.count))
    assert physical.moveToComponent(top)
    assert study.moveToComponent(top)
    # Preserve per-item flags; hide the study group using its new root-context occurrence.
    studyGroup=next(o for o in top.childOccurrences if o.component.name=='BATTERY_CLEARANCE_STUDIES_NOT_PARTS')
    studyGroup.isLightBulbOn=False
    if d.snapshots.hasPendingSnapshot:d.snapshots.add()
    assert d.computeAll();assert top.childOccurrences.count==2, 'TOP_COUNT: '+str(top.childOccurrences.count)
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    report=dict(date='2026-11-08',rootGroup=top.component.name,physicalGroup='BATTERY_PARTS_CELL_CARRIER_ADHESIVE',physicalOccurrences=4,studyGroup='BATTERY_CLEARANCE_STUDIES_NOT_PARTS',studyOccurrences=6,studyInitiallyHidden=True,checks=checks,timelineIssues=issues)
    json.dump(report,open(BASE+'docs/battery-browser-group-verification.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    assert doc.save('Group current 42mm battery parts and clearance studies for bulk visibility; preserve all placements, keep retired layouts separate.')
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d'))
    print(json.dumps(report,ensure_ascii=False))
