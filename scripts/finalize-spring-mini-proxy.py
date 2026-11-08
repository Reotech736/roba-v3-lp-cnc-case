"""Fusion MCP: verify/save derived Spring MINI proxy without the old generic fix pin."""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'

def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber==20 and doc.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE'
    def read(n):return json.load(open(BASE+'docs/'+n,encoding='utf-8'))
    change=read('spring-mini-fix-pin-removal.json');placement=read('choc-v2-placement-verification.json');detailed=read('detailed-choc-fit-verification.json');fit=read('internal-retention-fit-verification.json')
    assert placement['derivedSpringMiniWithoutFixPin'] and placement['switchSolids']==161 and placement['socketSolids']==161
    assert all(r['count']==0 for r in detailed['results'])
    for key in ['coreInterferences','wireVsAssemblyInterferences','assumedPlugAccessVsCasesInterferences','slackSpaceVsAssemblyInterferences','pullTabAccessVsAssemblyInterferences','detailedSocketsVsNewPartsInterferences']:assert not fit[key],str((key,fit[key]))
    refs=[o for o in root.allOccurrences if o.component.name.startswith('CHOC_V2_RED_DETAILED_')];assert len(refs)==23
    def walk(o,counts):
        assert o.component.name!='pin3'
        for b in o.bRepBodies:counts['bodies']+=1
        for label in ['pin1','pin2','stem']:
            if o.component.name==label:counts[label]+=1
        for child in o.childOccurrences:walk(child,counts)
    for o in refs:
        counts=dict(bodies=0,pin1=0,pin2=0,stem=0);walk(o,counts);assert counts==dict(bodies=7,pin1=1,pin2=1,stem=1)
    primary=json.load(open(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.json',encoding='utf-8'))
    for o in root.occurrences:
        if o.component.name in primary['volumes_mm3']:assert abs(o.component.bRepBodies.item(0).volume*1000-primary['volumes_mm3'][o.component.name])<1e-5
    # Save an inspection view of one switch underside; restore user visibility and camera.
    view=a.activeViewport;camera=view.camera;visibility=[(o,o.isLightBulbOn) for o in root.allOccurrences]
    group=next(o for o in root.occurrences if o.component.name=='CHOC_SWITCHES_AND_SOCKETS_REFERENCE_23_PAIRS')
    for o in root.occurrences:o.isLightBulbOn=(o==group)
    first=refs[0]
    for o in group.childOccurrences:o.isLightBulbOn=(o.fullPathName==first.fullPathName)
    for child in first.childOccurrences:
        child.isLightBulbOn=True
        for leaf in child.childOccurrences:leaf.isLightBulbOn=True
    cam=view.camera;cam.viewOrientation=adsk.core.ViewOrientations.IsoBottomRightViewOrientation;cam.isFitView=True;view.camera=cam;view.fit()
    assert view.saveAsImageFile(BASE+'docs/images/v21-spring-mini-proxy-no-fix-pin.png',1200,950)
    for o,flag in visibility:o.isLightBulbOn=flag
    view.camera=camera
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    assert doc.save('Derive Spring MINI CAD proxy by omitting generic ChocV2 fix pin3 across23 switches. Two electrical contacts and all placements preserved; source STEP unchanged.')
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d'))
    change.update(fitReport='detailed-choc-fit-verification.json',retentionFitReport='internal-retention-fit-verification.json',placementReport='choc-v2-placement-verification.json',positionsRechecked=46,stemTopsRechecked=23,caseVolumesUnchanged=True,timelineIssues=issues)
    change['decisionBasis']='User suspects target lacks selected pin; manufacturer old fix-pin design and retailer Spring MINI underside photo corroborate omission from this target proxy.'
    json.dump(change,open(BASE+'docs/spring-mini-fix-pin-removal.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    approved=[]
    for o in root.allOccurrences:
        if o.component.name in ['BATTERY_ASSEMBLY_CELL42_WIRE40_PROVISIONAL','CLEARANCE_STUDIES_NOT_PARTS']:continue
        approved.append(dict(name=o.component.name,path=o.fullPathName,matrix=list(o.transform2.asArray()),bodies=o.component.bRepBodies.count,volumes=[b.volume*1000 for b in o.component.bRepBodies]))
    json.dump(approved,open(BASE+'docs/current-approved-component-state.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(dict(removedFixPins=23,electricalContactsRetained=46,stemsRetained=23,switchBodies=161,totalDetailedChocBodies=322,caseGeometryUnchanged=True,timelineIssues=issues)))
