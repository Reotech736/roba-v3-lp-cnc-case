"""One-time finalize verified v26 working audit correction as v27."""
import adsk.core,adsk.fusion,json
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')
def run(_context: str):
 app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 assert doc.dataFile.versionNumber==26 and doc.isModified
 def read(n):return json.loads((BASE/'docs'/n).read_text(encoding='utf-8'))
 audit=read('design-consistency-audit-current.json');assert len(audit['approvedStateDeviations'])==1
 assert audit['approvedStateDeviations'][0]['path'].startswith('Upper_L_') and audit['approvedStateDeviations'][0]['matrixDelta']==0
 assert all(r['missingSleeveMaterial_mm3']<1e-5 for r in audit['upperThreadRadialSleeves'])
 bracket=read('case-wire-bracket-verification.json');assert not bracket['bracketVsPhysicalAndWireCollisions']
 assert all(not r['collisionsExcludingUpperThreadMajorOverlap'] for r in bracket['hardwareStudies'])
 assert all(not r['collisions'] for r in bracket['driverChecks'])
 fit=read('internal-retention-fit-verification.json')
 for k in ['coreInterferences','wireVsAssemblyInterferences','slackSpaceVsAssemblyInterferences','pullTabAccessVsAssemblyInterferences','detailedSocketsVsNewPartsInterferences']:assert not fit[k]
 assert read('fastening-and-overhang-current-audit.json')['obstructedM2Axes']==0
 assert read('upper-support-relief-verification.json')['activeReliefTiersMatched']==8
 assert all(not r['count'] for r in read('detailed-choc-fit-verification.json')['results'])
 assert all(r['obstructingPocketMaterial_mm3']<1e-5 and r['missingResidualMaterial_mm3']<1e-5 for r in read('corrected-stand-solid-verification.json')['pocketAndResidualVolumeChecks'])
 assert not read('case-wire-bracket-contact-verification.json')['positiveQuadrantViolations']
 assert not [t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage] and not d.snapshots.hasPendingSnapshot
 for prefix in ['Upper_L_','Lower_L_']:
  c=next(c for c in d.allComponents if c.name.startswith(prefix));assert c.bRepBodies.count==1
  assert c.material.name=='JLCCNC_6061_T6_SUPPLIER_MINIMUM_PROVISIONAL'
  assert c.bRepBodies.item(0).material.name==c.material.name
 assert doc.save('Audit correction: reinforce two upper M1.6 pilot outer walls; full0.9mm radial comparison sleeves. Set upper/lower6061T6 supplier minimum UTS290MPa/yield240MPa, supplier density2800. Material/threads/stand operation remain prototype-unqualified.')
 assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(BASE/'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d')))
 rows=[]
 for o in root.allOccurrences:
  if o.component.name in ['BATTERY_ASSEMBLY_CELL42_WIRE40_PROVISIONAL','CLEARANCE_STUDIES_NOT_PARTS']:continue
  rows.append({'name':o.component.name,'path':o.fullPathName,'matrix':list(o.transform2.asArray()),'bodies':o.component.bRepBodies.count,'volumes':[b.volume*1000 for b in o.component.bRepBodies]})
 assert len(rows)==587
 (BASE/'docs/current-approved-component-state.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'saveRequested':True,'cloudVersionAtRequest':doc.dataFile.versionNumber,'approvedRecords':len(rows),'F3DExported':True}))
