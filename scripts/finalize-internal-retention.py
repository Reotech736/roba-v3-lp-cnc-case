"""Fusion MCP: verify/export provisional insulation, carrier, routing and strengthened cover."""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'
NAME='left_case_two_stands_v05_NOT_FOR_MANUFACTURE'


def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.name==NAME and not doc.dataFile.isReadOnly and not d.snapshots.hasPendingSnapshot
    assert d.computeAll()
    def get(prefix):return next(o for o in root.occurrences if o.component.name.startswith(prefix))
    lower=get('Lower_L_');upper=get('Upper_L_');cover=get('MCU_RAISED_');carrier=get('BATTERY_REMOVABLE_CARRIER_')
    fit=json.load(open(BASE+'docs/internal-retention-fit-verification.json',encoding='utf-8'))
    dev=json.load(open(BASE+'docs/internal-retention-development.json',encoding='utf-8'))
    for key in ['coreInterferences','wireVsAssemblyInterferences','assumedPlugAccessVsCasesInterferences','slackSpaceVsAssemblyInterferences','pullTabAccessVsAssemblyInterferences','detailedSocketsVsNewPartsInterferences']:assert not fit[key],str((key,fit[key]))
    baseline=json.load(open(BASE+'docs/service-and-locating-verification.json',encoding='utf-8'))
    assert abs(upper.component.bRepBodies.item(0).volume*1000-baseline['volumes_mm3'][upper.component.name])<.0001
    assert abs(lower.component.bRepBodies.item(0).volume*1000-dev['standPocketRevision']['lowerVolumes_mm3'][1])<.0001
    def hits(items):
        c=adsk.core.ObjectCollection.create()
        for item in items:c.add(item)
        i=d.createInterferenceInput(c);i.areCoincidentFacesIncluded=False;r=d.analyzeInterference(i)
        return [dict(first=h.entityOne.parentComponent.name,second=h.entityTwo.parentComponent.name,volume_mm3=h.interferenceBody.volume*1000) for h in r]
    cable=hits([upper,cover,get('USB_CABLE_')]);assert not cable,str(cable)
    cap=hits([upper,lower,cover,get('KEYCAP_SWEEP_')]);assert not cap,str(cap)
    detailed=[]
    def walk(o):
        for b in o.bRepBodies:detailed.append(b)
        for child in o.childOccurrences:walk(child)
    walk(get('XIAO_DETAILED_'));assert len(detailed)==77
    probe=get('RESET_NONCONDUCTIVE_');names={o.component.name for o in [lower,upper,cover,probe]}
    r=hits([lower,upper,cover,probe]+detailed);external=[h for h in r if h['first'] in names or h['second'] in names];assert not external,str(external)
    inside=adsk.fusion.PointContainment.PointInsidePointContainment
    def point(x,y,z):return adsk.core.Point3D.create(x/10,y/10,z/10)
    cb=carrier.component.bRepBodies.item(0)
    assert cb.pointContainment(point(-50,-40,-9.2))==inside
    assert cb.pointContainment(point(-50,-40,-8.25))!=inside
    assert cb.pointContainment(point(-65.9,-49,-7.5))==inside
    assert cb.pointContainment(point(-65.9,-40,-7.5))!=inside # Open left lead exit.
    # Verify the actual floor directly below B1, using native lower coordinates.
    lb=lower.component.bRepBodies.item(0)
    assert lb.pointContainment(point(-1.38934,-15,5.49))==inside
    assert lb.pointContainment(point(-1.38934,-15,5.51))!=inside
    for b in get('PCB_SUPPORT_INSULATION_').component.bRepBodies:
        bb=b.boundingBox;assert abs(bb.minPoint.z*10+.2)<1e-6 and abs(bb.maxPoint.z*10)<1e-6
    # New reference parts were created at their final transforms; ensure old placements stay captured.
    placement=json.load(open(BASE+'docs/choc-v2-placement-verification.json',encoding='utf-8'));idx=0
    for prefix in ['CHOC_V2_RED_DETAILED_','CHOC_SOCKET_DETAILED_']:
        for o in [o for o in root.allOccurrences if o.component.name.startswith(prefix)]:
            t=o.transform2.translation;expected=placement['positionChecks'][idx]['expected_mm']
            assert max(abs(a-b) for a,b in zip([t.x*10,t.y*10,t.z*10],expected))<1e-6;idx+=1
    assert idx==46
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    for o in [lower,upper,cover,carrier]:assert o.component.bRepBodies.count==1
    view=a.activeViewport;camera=view.camera;visible=[(o,o.isLightBulbOn) for o in root.occurrences]
    review_prefixes=('Lower_L_','BATTERY_REMOVABLE_CARRIER_','CARRIER_BASE_REMOVABLE_','CELL_REMOVABLE_ADHESIVE_','BATTERY_CELL_NOMINAL_','BATTERY_WIRE_ROUTE_','B1_JST_PH_SMD_')
    for o,flag in visible:o.isLightBulbOn=o.component.name.startswith(review_prefixes)
    view.fit();assert view.saveAsImageFile(BASE+'docs/images/v05-battery-carrier-and-route.png',1500,1100)
    for o,flag in visible:o.isLightBulbOn=(o==carrier)
    view.fit();assert view.saveAsImageFile(BASE+'docs/images/v05-battery-carrier-only.png',1300,950)
    for o,flag in visible:o.isLightBulbOn=(o==cover)
    cam=view.camera;cam.viewOrientation=adsk.core.ViewOrientations.BottomViewOrientation;cam.isFitView=True;view.camera=cam
    assert view.saveAsImageFile(BASE+'docs/images/v05-cover-reinforced-underside.png',1300,950)
    for o,flag in visible:o.isLightBulbOn=flag
    view.camera=camera;view.fit()
    assert doc.save('Add dielectric/carrier/wire studies and 1.2mm cover sides; revise stand pockets to depth3.5 with residual2 and nominal B1 gap0.5. Actual parts/materials unverified.')
    ex=d.exportManager;assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/'+NAME+'.f3d'))
    for o,label in [(lower,'Lower_L'),(upper,'Upper_L_protective_roof'),(cover,'MCU_cover_concept')]:assert ex.execute(ex.createSTEPExportOptions(BASE+'cad/design/'+NAME+'_'+label+'_LOCAL.step',o.component))
    assert ex.execute(ex.createSTEPExportOptions(BASE+'cad/design/battery_carrier_provisional_NONMETAL_NOT_FOR_MANUFACTURE_LOCAL.step',carrier.component))
    dev.update(caseVolumesUnchanged=False,metalCaseVolumesUnchanged=False,upperMetalCaseUnchanged=True)
    json.dump(dev,open(BASE+'docs/internal-retention-development.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    out=dict(date='2026-11-08',id=doc.dataFile.id,cloudVersion=doc.dataFile.versionNumber,cloudComplete=doc.dataFile.isComplete,modified=doc.isModified,
             metalCaseVolumesUnchanged=False,upperMetalCaseUnchanged=True,standPocketDepth_mm=3.5,standResidual_mm=2,coreSolidCount=fit['coreSolidCount'],fitReport='internal-retention-fit-verification.json',
             cableInterferences=cable,capSweepInterferences=cap,detailedMCUAndResetProbeInterferences=external,internalMCUOverlapsExcluded=len(r)-len(external),
             checkedInstanceDatums=46,pcbPadStacks=4,carrierMaterialPointChecks=4,headerFloorPointChecks=2,
             timelineIssues=issues,nominalHeaderFloorGap_mm=.5,wireRouteLength_mm=dev['wireRouteLength_mm'],wireLengthIncludingAssumedSlack_mm=dev['wireLengthComparison_mm'],
             singleSolidExportParts=4,volumes_mm3={o.component.name:o.component.bRepBodies.item(0).volume*1000 for o in [lower,upper,cover,carrier]},
             currentParts=[dict(name=o.component.name,bodies=o.component.bRepBodies.count,visible=o.isLightBulbOn) for o in root.occurrences],
             limitations=dev['limitations']+['B1 nominal 0.5 mm floor gap requires installed-part/tolerance confirmation before manufacturing','Shallower stand pockets increase folded protrusion by 0.2 mm; foot height is provisional','Cover sidewall section comparison is not structural or RF qualification'])
    json.dump(out,open(BASE+'docs/internal-retention-final-verification.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in out.items() if k!='currentParts'},ensure_ascii=False))
