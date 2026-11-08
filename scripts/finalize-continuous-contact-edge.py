"""Fusion MCP: save the verified contact edge, export both case parts and full F3D."""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'

def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber==18
    def read(name):return json.load(open(BASE+'docs/'+name,encoding='utf-8'))
    dev=read('continuous-contact-edge-development.json');contact=read('continuous-contact-edge-verification.json');audit=read('fastening-and-overhang-current-audit.json');solid=read('corrected-stand-solid-verification.json');fit=read('internal-retention-fit-verification.json')
    assert contact['continuousEdge']['length_mm']==42 and all(not row['tablePenetrations'] for row in contact['tableTests'])
    assert audit['obstructedM2Axes']==0 and audit['sampledOverhangPoints']==0
    assert all(row['obstructingPocketMaterial_mm3']<1e-5 and row['missingResidualMaterial_mm3']<1e-5 for row in solid['pocketAndResidualVolumeChecks'])
    for key in ['coreInterferences','wireVsAssemblyInterferences','assumedPlugAccessVsCasesInterferences','slackSpaceVsAssemblyInterferences','pullTabAccessVsAssemblyInterferences','detailedSocketsVsNewPartsInterferences']:assert not fit[key],str((key,fit[key]))
    lower=next(o for o in root.occurrences if o.component.name.startswith('Lower_L_'));upper=next(o for o in root.occurrences if o.component.name.startswith('Upper_L_'))
    for o in [lower,upper]:assert abs(o.component.bRepBodies.item(0).volume*1000-dev['volumesAfter_mm3'][o.component.name])<1e-5
    view=a.activeViewport;camera=view.camera;visible=[(o,o.isLightBulbOn) for o in root.occurrences]
    for o,flag in visible:o.isLightBulbOn=(o==lower)
    edges=[]
    for e in lower.bRepBodies.item(0).edges:
        if not adsk.core.Line3D.cast(e.geometry):continue
        ends=[v.geometry for v in [e.startVertex,e.endVertex]]
        if all(abs(p.x*10-dev['contactEdgeX_mm'])<1e-5 and abs(p.z*10+11.5)<1e-5 for p in ends) and abs(e.length*10-42)<1e-5:edges.append(e)
    assert len(edges)==1
    a.userInterface.activeSelections.clear();assert a.userInterface.activeSelections.add(edges[0])
    cam=view.camera;cam.viewOrientation=adsk.core.ViewOrientations.BottomViewOrientation;cam.isFitView=True;view.camera=cam;view.fit()
    assert view.saveAsImageFile(BASE+'docs/images/v19-contact-edge-bottom.png',1500,1100)
    ex=d.exportManager
    assert ex.execute(ex.createSTEPExportOptions(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE_Lower_L_LOCAL.step',lower.component))
    upper.isLightBulbOn=True
    assert ex.execute(ex.createSTEPExportOptions(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE_Upper_L_protective_roof_LOCAL.step',upper.component))
    for o,flag in visible:o.isLightBulbOn=flag
    view.camera=camera
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    assert doc.save('Form continuous42mm contact edge at former M2 boss extrema; match upper/lower exterior and restore M2 holes/seats. Verify ideal tilt-table clearance and other component geometry unchanged.')
    assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d'))
    dev.update(status='CONTACT_EDGE_GEOMETRY_VERIFIED_PHYSICAL_SUPPORT_PENDING',verification='continuous-contact-edge-verification.json',holeAudit='fastening-and-overhang-current-audit.json',residualVerification='corrected-stand-solid-verification.json',fitReport='internal-retention-fit-verification.json',timelineIssues=issues)
    json.dump(dev,open(BASE+'docs/continuous-contact-edge-development.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(dict(contactEdge_mm=42,tableAnglesChecked_deg=[row['tilt_deg'] for row in contact['tableTests']],M2Blocked=0,caseBoundsUnchanged=True,lowerAndUpperSTEPUpdated=True,timelineIssues=issues)))
