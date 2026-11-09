"""One-time unsavedv28: retire optional receiver/wire fixture, preserve models.

User prefers tape fixation; PCB-side retention is provisional. All original
geometry remains as hidden comparison. No unverified flat PCB bonding face is
introduced, and the agreed case holes/relief are retained for this iteration.
"""
import adsk.core,adsk.fusion,json
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')
def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber==28 and doc.isModified
    assert (BASE/'cad/design/checkpoints/v05_cloud_v28_WORKING_before_positive_x_straight_wall.f3d').exists()
    before=[(o.component,list(o.transform2.asArray()),[b.volume*1000 for b in o.component.bRepBodies],o.fullPathName) for o in root.allOccurrences]
    mapping=[]
    for prefix in ['BATTERY_REMOVABLE_CARRIER_','CARRIER_BASE_REMOVABLE_','CELL_REMOVABLE_ADHESIVE_','WIRE_STRAIN_RELIEF_CASE_BRACKET_']:
        o=next(o for o in root.allOccurrences if o.component.name.startswith(prefix));old=o.component.name
        o.component.name='RETIRED_OPTIONAL_BATTERY_FIXTURE_'+old;o.isLightBulbOn=False
        o.component.attributes.add('DesignStatus','Role','Historical comparison; not required for current tape-fixed battery concept; do not manufacture')
        mapping.append({'old':old,'new':o.component.name,'reason':'Dedicated hardware removed from required configuration; retained read-only by workflow as comparison'})
    for name in ['BATTERY_SERVICE_POSES_R3_LENGTH40_CENTERLINES_NOT_PARTS','BATTERY_TWO_D1_LEADS40_OPEN_POSES_NOT_CONTINUOUS_MOTION']:
        o=next(o for o in root.allOccurrences if o.component.name==name);o.component.name='RETIRED_LOWER_MOVING_BATTERY_'+name;o.isLightBulbOn=False
        mapping.append({'old':name,'new':o.component.name,'reason':'Historical lower-mounted battery motion; new provisional mount follows PCB side'})
    cell=next(o for o in root.allOccurrences if o.component.name.startswith('BATTERY_CELL_NOMINAL_42'))
    cell.component.attributes.add('DesignStatus','Mounting','PCB-side tape/insulation concept; current location retained as clearance reservation; bonding face/material/strength unqualified')
    assert d.computeAll() and not [t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage]
    # Definitions can be instanced more than once: compare by unchanged occurrence
    # order rather than using component dictionary for duplicated switch parts.
    after=list(root.allOccurrences);assert len(before)==len(after)
    for (component,matrix,volumes,path),o in zip(before,after):
        assert o.component==component and max(abs(a-b) for a,b in zip(matrix,o.transform2.asArray()))<1e-8
        assert all(abs(v-b.volume*1000)<1e-5 for v,b in zip(volumes,o.component.bRepBodies))
    result={'date':'2026-11-10','baselineCloudVersion':28,'physicalCandidatesRetired':4,'retiredFixtureAndAdhesiveDefinitions':mapping[:4],'retiredMotionStudies':mapping[4:],'renameMap':mapping,'allGeometryAndTransformsPreserved':True,'batteryCurrentPhysicalCandidateCount':1,'batteryXYZUnchanged':True,'newMountingConcept':'PCB-side insulation/padding and removable tape; no certified bonding site or tape material','oldDedicatedBracketSTEPCurrent':False,'oldBatteryCarrierSTEPCurrent':False,'existingCasePilotHolesAndBracketReliefRetained':True,'fixedPCBToBatteryNominalGap_mm':3.1,'actualAttachmentVerified':False,'saved':False}
    (BASE/'docs/battery-fixture-retirement.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
