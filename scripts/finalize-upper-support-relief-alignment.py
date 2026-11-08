"""Fusion MCP: save aligned support reliefs after full current-support checks."""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'

def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber==21
    def read(n):return json.load(open(BASE+'docs/'+n,encoding='utf-8'))
    change=read('upper-support-relief-alignment.json');proof=read('upper-support-relief-verification.json');detailed=read('detailed-choc-fit-verification.json');fit=read('internal-retention-fit-verification.json');audit=read('fastening-and-overhang-current-audit.json')
    assert proof['activeReliefTiersMatched']==8 and proof['obsoleteDuplicateSuppressed']
    assert all(r['obstructingUpperMaterial_mm3']<1e-5 for r in proof['nominalCavityChecks'])
    assert all(r['count']==0 for r in detailed['results'])
    for key in ['coreInterferences','wireVsAssemblyInterferences','assumedPlugAccessVsCasesInterferences','slackSpaceVsAssemblyInterferences','pullTabAccessVsAssemblyInterferences','detailedSocketsVsNewPartsInterferences']:assert not fit[key],str((key,fit[key]))
    assert audit['obstructedM2Axes']==0
    upper=next(o for o in root.occurrences if o.component.name.startswith('Upper_L_'));assert abs(upper.component.bRepBodies.item(0).volume*1000-change['upperVolumeAfter_mm3'])<1e-5
    assert upper.component.bRepBodies.count==1
    # No pin3 reintroduced and corrected source variant remains shared by23 instances.
    refs=[o for o in root.allOccurrences if o.component.name.startswith('CHOC_V2_RED_DETAILED_')];assert len(refs)==23
    assert not any(o.component.name=='pin3' for o in root.allOccurrences)
    a.userInterface.activeSelections.clear()
    view=a.activeViewport;camera=view.camera;visible=[(o,o.isLightBulbOn) for o in root.occurrences]
    for o,flag in visible:o.isLightBulbOn=(o==upper)
    cam=view.camera;cam.viewOrientation=adsk.core.ViewOrientations.BottomViewOrientation;cam.isFitView=True;view.camera=cam;view.fit()
    assert view.saveAsImageFile(BASE+'docs/images/v22-upper-support-reliefs.png',1500,1100)
    assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE_Upper_L_protective_roof_LOCAL.step',upper.component))
    for o,flag in visible:o.isLightBulbOn=flag
    view.camera=camera
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    assert doc.save('Align expanded upper relief1 and both relief4 sketches with current PCB supports; suppress obsolete duplicate. Verify all8 relief tiers and4 nominal cavities, detail parts and M2 holes.')
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d'))
    change.update(status='ALL_CURRENT_SUPPORT_RELIEFS_ALIGNED',verification='upper-support-relief-verification.json',fitReports=['detailed-choc-fit-verification.json','internal-retention-fit-verification.json','fastening-and-overhang-current-audit.json'],allEightActiveReliefTiersMatch=True,timelineIssues=issues)
    json.dump(change,open(BASE+'docs/upper-support-relief-alignment.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    approved=[]
    for o in root.allOccurrences:
        if o.component.name in ['BATTERY_ASSEMBLY_CELL42_WIRE40_PROVISIONAL','CLEARANCE_STUDIES_NOT_PARTS']:continue
        approved.append(dict(name=o.component.name,path=o.fullPathName,matrix=list(o.transform2.asArray()),bodies=o.component.bRepBodies.count,volumes=[b.volume*1000 for b in o.component.bRepBodies]))
    json.dump(approved,open(BASE+'docs/current-approved-component-state.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(dict(activeReliefTiers=8,currentSupports=4,obsoleteDuplicateSuppressed=True,detailCaseAndWireChecksClear=True,M2HolesClear=True,upperVolume_mm3=upper.component.bRepBodies.item(0).volume*1000)))
