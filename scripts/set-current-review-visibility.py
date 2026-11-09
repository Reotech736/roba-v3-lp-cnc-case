"""Fusion MCP: validate organized hierarchy, enable current assembly, save and export."""
import adsk.core,adsk.fusion,json,collections
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'

def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE'
    import os
    approvedFile=BASE+'docs/current-approved-component-state.json'
    approvedBaseline=os.path.exists(approvedFile)
    baseline=json.load(open(approvedFile if approvedBaseline else BASE+'docs/component-cleanup-preflight.json',encoding='utf-8'))
    def signature(v):
        name='OLD_NOT_CURRENT' if v['name']=='RETIRED_BATTERY_LAYOUTS_NOT_CURRENT' else v['name']
        return name,tuple(round(x,8) for x in v['matrix']),v['bodies'],tuple(sorted(round(x,5) for x in v['volumes']))
    correctionFile=BASE+'docs/stand-and-M2-correction.json'
    correction=json.load(open(correctionFile,encoding='utf-8')) if os.path.exists(correctionFile) else None
    if not approvedBaseline:
        if correction and correction.get('cloudVersion',0)>=18:
            for v in baseline:
                if v['name']==correction['changedComponent']:v['volumes']=[correction['lowerVolumeAfter_mm3']]
        contactFile=BASE+'docs/continuous-contact-edge-development.json'
        contact=json.load(open(contactFile,encoding='utf-8')) if os.path.exists(contactFile) else None
        if contact and contact.get('cloudVersion',0)>=19:
            for v in baseline:
                if v['name'] in contact['volumesAfter_mm3']:v['volumes']=[contact['volumesAfter_mm3'][v['name']]]
    before=collections.Counter(signature(v) for v in baseline)
    newGroups={'BATTERY_ASSEMBLY_CELL42_WIRE40_PROVISIONAL','CLEARANCE_STUDIES_NOT_PARTS'}
    current=[dict(name=o.component.name,matrix=o.transform2.asArray(),bodies=o.component.bRepBodies.count,volumes=[b.volume*1000 for b in o.component.bRepBodies]) for o in root.allOccurrences if o.component.name not in newGroups]
    after=collections.Counter(signature(v) for v in current)
    assert before==after,'Current approved component transforms/body counts/volumes must match; refresh baseline only after verified design revisions'
    old=next(o for o in root.occurrences if o.component.name=='OLD_NOT_CURRENT');assert old.component.occurrences.count==12
    battery=next(o for o in root.occurrences if o.component.name=='BATTERY_ASSEMBLY_CELL42_WIRE40_PROVISIONAL')
    bracket=any(o.component.name.startswith('WIRE_STRAIN_RELIEF_CASE_BRACKET_') for o in battery.childOccurrences)
    retiredFixtures=[o for o in battery.childOccurrences if o.component.name.startswith('RETIRED_OPTIONAL_BATTERY_FIXTURE_')]
    assert battery.component.occurrences.count==1+len(retiredFixtures)+1 if retiredFixtures else battery.component.occurrences.count==(6 if bracket else 5)
    study=next(o for o in battery.childOccurrences if o.component.name=='CLEARANCE_STUDIES_NOT_PARTS')
    direct=any(o.component.name.startswith('BATTERY_WIRE_ROUTE_D3_DIRECT_SOLDER_') for o in study.childOccurrences)
    service=any(o.component.name.startswith('BATTERY_SERVICE_POSES_R3_') for o in study.childOccurrences)
    individual=any(o.component.name.startswith('BATTERY_TWO_D1_LEADS40_CLOSED_') for o in study.childOccurrences)
    assert study.childOccurrences.count==(14 if individual else 12 if bracket else 10 if service else 7 if direct else 6)
    fit=json.load(open(BASE+'docs/internal-retention-fit-verification.json',encoding='utf-8'))
    for key in ['coreInterferences','wireVsAssemblyInterferences','assumedPlugAccessVsCasesInterferences','slackSpaceVsAssemblyInterferences','pullTabAccessVsAssemblyInterferences','detailedSocketsVsNewPartsInterferences']:assert not fit[key],str((key,fit[key]))
    for o in root.allOccurrences:o.isLightBulbOn=False
    for c in d.allComponents:
        c.isSketchFolderLightBulbOn=False;c.isConstructionFolderLightBulbOn=False
    prefixes=('Lower_L_','Upper_L_','PCB_L_','MCU_RAISED_','XIAO_DETAILED_','CHOC_SWITCHES_AND_SOCKETS_','PCB_SUPPORT_INSULATION_','BATTERY_ASSEMBLY_')
    def enable(o):
        if o.component.name=='CLEARANCE_STUDIES_NOT_PARTS' or o.component.name.startswith('RETIRED_'):return
        o.isLightBulbOn=True;o.component.isBodiesFolderLightBulbOn=True
        for b in o.component.bRepBodies:b.isLightBulbOn=True
        for child in o.childOccurrences:enable(child)
    for o in root.occurrences:
        if o.component.name.startswith(prefixes):enable(o)
    old.isLightBulbOn=False;study.isLightBulbOn=False
    assert d.computeAll();issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    view=a.activeViewport;cam=view.camera;cam.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation;cam.isFitView=True;view.camera=cam;view.fit()
    assert view.saveAsImageFile(BASE+'docs/images/v05-organized-current-assembly.png',1500,1100)
    report=dict(date='2026-11-08',fileName=doc.name,baselineCloudVersion=16,rootGroups=[dict(name=o.component.name,visible=o.isLightBulbOn,children=o.childOccurrences.count) for o in root.occurrences],
        originalOccurrenceRecordsVerified=len(baseline),allTransformsAndBodyCountsPreserved=True,volumesMatchApprovedGeometryBaseline=True,approvedLowerCorrectionCloudVersion=correction.get('cloudVersion') if correction else None,deletedComponents=0,oldDirectOccurrences=12,
        batteryPhysicalOccurrences=1 if retiredFixtures else 5 if bracket else 4,retiredBatteryFixtureOccurrences=len(retiredFixtures),batteryStudyOccurrences=study.childOccurrences.count,batteryStudyGroupInitiallyHidden=True,coreSolids=fit['coreSolidCount'],fitReport='internal-retention-fit-verification.json',timelineIssues=issues,
        note='Coarse switch/MCU envelopes in OLD are retained for conservative checks. They are not manufacturing parts. Current battery dimensions42x20x5, wire budget40 remain unchanged.')
    json.dump(report,open(BASE+'docs/component-organization-verification.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    assert doc.save('Organize obsolete comparisons under OLD; group battery parts and study tools; enable current assembly. Preserve all original transforms and geometry.')
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d'))
    print(json.dumps(report,ensure_ascii=False))
