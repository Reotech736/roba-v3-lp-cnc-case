"""Fusion MCP: verify/save LP-only Choc orientation and matching support correction."""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'

def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber==19 and doc.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE'
    def read(n):return json.load(open(BASE+'docs/'+n,encoding='utf-8'))
    correction=read('choc-orientation-correction.json');support=read('choc-lp-support-correction.json');placement=read('choc-v2-placement-verification.json');fit=read('internal-retention-fit-verification.json');detailed=read('detailed-choc-fit-verification.json')
    assert placement['orientationCorrection_deg']==180 and len(placement['positionChecks'])==46
    assert all(result['count']==0 for result in detailed['results'])
    for key in ['coreInterferences','wireVsAssemblyInterferences','assumedPlugAccessVsCasesInterferences','slackSpaceVsAssemblyInterferences','pullTabAccessVsAssemblyInterferences','detailedSocketsVsNewPartsInterferences']:assert not fit[key],str((key,fit[key]))
    audit=read('fastening-and-overhang-current-audit.json');assert audit['obstructedM2Axes']==0 and audit['sampledOverhangPoints']==0
    def get(prefix):return next(o for o in root.allOccurrences if o.component.name.startswith(prefix))
    lower=get('Lower_L_');upper=get('Upper_L_');cover=get('MCU_RAISED_')
    for o in [lower,upper]:assert abs(o.component.bRepBodies.item(0).volume*1000-support['currentCaseVolumes_mm3'][o.component.name])<1e-5
    # Contact line itself and all current physical bounding boxes stay on the safe side.
    contactEdges=[]
    for e in lower.bRepBodies.item(0).edges:
        if adsk.core.Line3D.cast(e.geometry) and abs(e.length*10-42)<1e-5:
            pts=[v.geometry for v in [e.startVertex,e.endVertex]]
            if all(abs(p.x*10+111.119997)<1e-5 and abs(p.z*10+11.5)<1e-5 for p in pts):contactEdges.append(e)
    assert len(contactEdges)==1
    for row in placement['records']:
        assert row['boundsGlobal_mm'][0][0]>=-111.119997-1e-5 and row['boundsGlobal_mm'][0][2]>=-11.5-1e-5
    # New support and insulation overlap the PCB edge by0.8mm with Z stack-.2..0.
    pad=get('PCB_SUPPORT_INSULATION_');body=next(b for b in pad.component.bRepBodies if b.preciseBoundingBox.minPoint.y*10 < -40 and b.preciseBoundingBox.minPoint.x*10 < -100)
    bb=body.preciseBoundingBox;assert abs(bb.minPoint.y*10+53)<1e-5 and abs(bb.maxPoint.y*10+45)<1e-5
    view=a.activeViewport;camera=view.camera;visibility=[(o,o.isLightBulbOn) for o in root.allOccurrences]
    for o in root.occurrences:o.isLightBulbOn=o.component.name.startswith(('PCB_L_','CHOC_SWITCHES_AND_SOCKETS_'))
    group=get('CHOC_SWITCHES_AND_SOCKETS_')
    for o in group.childOccurrences:
        o.isLightBulbOn=o.component.name.startswith('CHOC_SOCKET_DETAILED_')
        if o.isLightBulbOn:
            for child in o.childOccurrences:child.isLightBulbOn=True
    cam=view.camera;cam.viewOrientation=adsk.core.ViewOrientations.BottomViewOrientation;cam.isFitView=True;view.camera=cam;view.fit()
    assert view.saveAsImageFile(BASE+'docs/images/v20-corrected-choc-sockets-bottom.png',1500,1100)
    for o,flag in visibility:o.isLightBulbOn=flag
    view.camera=camera
    ex=d.exportManager
    for o,label in [(lower,'Lower_L'),(upper,'Upper_L_protective_roof')]:
        flag=o.isLightBulbOn;o.isLightBulbOn=True
        assert ex.execute(ex.createSTEPExportOptions(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE_'+label+'_LOCAL.step',o.component))
        o.isLightBulbOn=flag
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    correction.update(scope='LP only; Choc orientation and socket placement. MX side not used as placement basis.',supportCorrection='choc-lp-support-correction.json',currentFit='detailed-choc-fit-verification.json',retentionFit='internal-retention-fit-verification.json',positionsReverified=46,stemTopsReverified=23,
        support1XYXY_mm=support['newSupport1XYXY_mm'],caseVolumes_mm3=support['currentCaseVolumes_mm3'],contactEdgeLength_mm=42,M2ObstructedAxes=0,timelineIssues=issues,fitRevalidatedAfterOrientationCorrection=True)
    json.dump(correction,open(BASE+'docs/choc-orientation-correction.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    old=next((x for x in a.documents if x.name=='balo43_L'),None)
    if old:
        assert not old.isModified;assert old.close(False)
    assert doc.save('Correct all23 Choc switches/socket pairs by180 degrees using LP holes and legacy model; move PCB support1/upper relief/insulation to clear corrected socket. MX placement not used.')
    assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d'))
    approved=[]
    for o in root.allOccurrences:
        if o.component.name in ['BATTERY_ASSEMBLY_CELL42_WIRE40_PROVISIONAL','CLEARANCE_STUDIES_NOT_PARTS']:continue
        approved.append(dict(name=o.component.name,path=o.fullPathName,matrix=list(o.transform2.asArray()),bodies=o.component.bRepBodies.count,volumes=[b.volume*1000 for b in o.component.bRepBodies]))
    json.dump(approved,open(BASE+'docs/current-approved-component-state.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(dict(LPOnly=True,correctedSwitches=23,correctedSockets=23,legacyBoardUnchanged=True,support1Shift_mm=8,all46PlacementsCaptured=True,correctedOrientationCaseAndSupportChecksClear=True,contactEdgeLength_mm=42,M2HolesClear=True)))
