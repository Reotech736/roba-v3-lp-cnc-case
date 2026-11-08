"""Fusion MCP: save verified stand placement correction and refresh lower STEP/F3D."""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'

def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber==17
    def read(name):return json.load(open(BASE+'docs/'+name,encoding='utf-8'))
    correction=read('stand-and-M2-correction.json');audit=read('fastening-and-overhang-current-audit.json');solid=read('corrected-stand-solid-verification.json');foot=read('corrected-stand-footprint-verification.json');fit=read('internal-retention-fit-verification.json')
    assert audit['obstructedM2Axes']==0 and audit['sampledOverhangPoints']==0
    assert foot['allBackingsInsideOriginalBaseFootprint'] and all(r['outsideBaseFootprintArea_mm2']<1e-8 and r['minBackingToBaseBoundary_mm']>1 for r in foot['rows'])
    assert all(r['obstructingPocketMaterial_mm3']<1e-5 and r['missingResidualMaterial_mm3']<1e-5 for r in solid['pocketAndResidualVolumeChecks'])
    for key in ['coreInterferences','wireVsAssemblyInterferences','assumedPlugAccessVsCasesInterferences','slackSpaceVsAssemblyInterferences','pullTabAccessVsAssemblyInterferences','detailedSocketsVsNewPartsInterferences']:assert not fit[key],str((key,fit[key]))
    lower=next(o for o in root.occurrences if o.component.name.startswith('Lower_L_'));body=lower.component.bRepBodies.item(0)
    assert abs(body.volume*1000-correction['lowerVolumeAfter_mm3'])<1e-4
    # B1 floor remains at global Z=-6 and actual nominal envelope bottom at -5.5.
    inside=adsk.fusion.PointContainment.PointInsidePointContainment
    assert body.pointContainment(adsk.core.Point3D.create(-.138934,-1.5,.549))==inside
    assert body.pointContainment(adsk.core.Point3D.create(-.138934,-1.5,.551))!=inside
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    camera=a.activeViewport.camera;visibility=[(o,o.isLightBulbOn) for o in root.occurrences]
    assert a.activeViewport.saveAsImageFile(BASE+'docs/images/v18-corrected-selected-area.png',1500,1100)
    for o,flag in visibility:o.isLightBulbOn=(o==lower)
    cam=a.activeViewport.camera;cam.viewOrientation=adsk.core.ViewOrientations.BottomViewOrientation;cam.isFitView=True;a.activeViewport.camera=cam;a.activeViewport.fit()
    assert a.activeViewport.saveAsImageFile(BASE+'docs/images/v18-corrected-stand-bottom.png',1500,1100)
    assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE_Lower_L_LOCAL.step',lower.component))
    for o,flag in visibility:o.isLightBulbOn=flag
    a.activeViewport.camera=camera
    assert doc.save('Correct stand backing exterior overhang and blocked M2 hole by relocating pockets/backings. Verify full nominal void/residual solids, all M2 passages and heads, footprint containment and assembly clearance.')
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d'))
    correction.update(status='KNOWN_V17_FINDINGS_CORRECTED_OTHER_QUALIFICATION_PENDING',M2ObstructedAxes=0,M2NominalScrewCollisions=0,backingOutsideFloorArea_mm2=[r['outsideBaseFootprintArea_mm2'] for r in foot['rows']],backingToFloorMinimumDistances_mm=[r['minBackingToBaseBoundary_mm'] for r in foot['rows']],
        verificationReports=['fastening-and-overhang-current-audit.json','corrected-stand-solid-verification.json','corrected-stand-footprint-verification.json','internal-retention-fit-verification.json'],nominalB1BackingGap_mm=.5,timelineIssues=issues,
        unchangedLocalCoupon='stand_test_depth3p5_fingerD8_NOT_FOR_MANUFACTURE: local geometry unchanged; assembly pocket positions shifted only')
    json.dump(correction,open(BASE+'docs/stand-and-M2-correction.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(dict(status=correction['status'],M2Blocked=0,nominalM2Collisions=0,backingOutsideArea_mm2=correction['backingOutsideFloorArea_mm2'],residual_mm=2,lowerVolume_mm3=body.volume*1000,timelineIssues=issues)))
