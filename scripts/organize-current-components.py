"""Fusion MCP: idempotent component organization; preserve geometry and placements.

Keep old comparison envelopes for conservative fit checks; never delete source data.
Use set-current-review-visibility.py afterwards to validate/save the review state.
"""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'

def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE' and not doc.dataFile.isReadOnly
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/checkpoints/v05_before_component_organization_v'+str(doc.dataFile.versionNumber)+'.f3d'))
    def group(owner,name):
        found=[o for o in owner.occurrences if o.component.name==name]
        if found:return found[0]
        o=owner.occurrences.addNewComponent(adsk.core.Matrix3D.create());o.component.name=name;return o
    def move(o,target):
        name=o.component.name;before=o.transform2.asArray();volumes=[b.volume*1000 for b in o.component.bRepBodies]
        result=o.moveToComponent(target);assert result,'Move failed: '+name
        assert max(abs(x-y) for x,y in zip(before,result.transform2.asArray()))<1e-8,name
        assert len(volumes)==result.component.bRepBodies.count,name
        assert max([0]+[abs(x-y) for x,y in zip(volumes,[b.volume*1000 for b in result.component.bRepBodies])])<1e-6,name
        return result
    old=next((o for o in root.occurrences if o.component.name in ['OLD_NOT_CURRENT','RETIRED_BATTERY_LAYOUTS_NOT_CURRENT']),None)
    if old is None:old=group(root,'OLD_NOT_CURRENT')
    old.component.name='OLD_NOT_CURRENT'
    oldPrefixes=('Battery_L_ALLOWANCE_','XIAO_KEY_SIDE_ENVELOPE_','SWITCH_LOWER_','SWITCH_UPPER_','RETIRED_V15_','RETIRED_CELL42_INITIAL_')
    for o in list(root.occurrences):
        if o.component.name.startswith(oldPrefixes):move(o,old).isLightBulbOn=False
    battery=group(root,'BATTERY_ASSEMBLY_CELL42_WIRE40_PROVISIONAL')
    batteryPrefixes=('BATTERY_REMOVABLE_CARRIER_','CARRIER_BASE_REMOVABLE_','CELL_REMOVABLE_ADHESIVE_','BATTERY_CELL_NOMINAL_42','CELL42_INSTALLATION_SPACE_','CELL_ADHESIVE_PULL_TAB_','BATTERY_WIRE_ROUTE_','BATTERY_SERVICE_SLACK_','B1_JST_','B1_MATING_')
    for o in list(root.occurrences):
        if o.component.name.startswith(batteryPrefixes):move(o,battery)
    # All source/target occurrences here are native to the same parent component.
    study=group(battery.component,'CLEARANCE_STUDIES_NOT_PARTS')
    studyPrefixes=('CELL42_INSTALLATION_SPACE_','CELL_ADHESIVE_PULL_TAB_','BATTERY_WIRE_ROUTE_','BATTERY_SERVICE_SLACK_','B1_JST_','B1_MATING_')
    for o in list(battery.component.occurrences):
        if o.component.name.startswith(studyPrefixes):move(o,study).isLightBulbOn=False
    old.isLightBulbOn=False;study.isLightBulbOn=False
    if d.snapshots.hasPendingSnapshot:d.snapshots.add()
    assert d.computeAll()
    assert old.component.occurrences.count==12
    assert battery.component.occurrences.count==5 and study.component.occurrences.count==6
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    print(json.dumps(dict(oldOccurrences=12,batteryPhysicalOccurrences=4,batteryStudyOccurrences=6,deletedComponents=0,timelineIssues=issues)))
