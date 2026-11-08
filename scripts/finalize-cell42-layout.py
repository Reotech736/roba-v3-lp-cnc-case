"""Fusion MCP: verify and save the 42x20x5 / 40mm battery layout candidate."""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'

def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber==15 and not doc.dataFile.isReadOnly
    def get(prefix):return next(o for o in root.occurrences if o.component.name.startswith(prefix))
    report=json.load(open(BASE+'docs/battery42-layout-development.json',encoding='utf-8'))
    fit=json.load(open(BASE+'docs/internal-retention-fit-verification.json',encoding='utf-8'))
    for key in ['coreInterferences','wireVsAssemblyInterferences','assumedPlugAccessVsCasesInterferences','slackSpaceVsAssemblyInterferences','pullTabAccessVsAssemblyInterferences','detailedSocketsVsNewPartsInterferences']:assert not fit[key],str((key,fit[key]))
    def hits(items):
        col=adsk.core.ObjectCollection.create()
        for x in items:col.add(x)
        i=d.createInterferenceInput(col);i.areCoincidentFacesIncluded=False
        return [dict(first=h.entityOne.parentComponent.name,second=h.entityTwo.parentComponent.name,volume_mm3=h.interferenceBody.volume*1000) for h in d.analyzeInterference(i)]
    obstacles=[o for o in root.occurrences if o.component.name.startswith(('Lower_L_','Upper_L_','PCB_L_','BATTERY_REMOVABLE_CARRIER_','B1_JST_'))]
    for o in root.allOccurrences:
        if o.component.name.startswith('CHOC_SOCKET_DETAILED_'):obstacles.append(o)
    install=get('CELL42_INSTALLATION_SPACE_');installation_hits=hits(obstacles+[install]);assert not installation_hits,str(installation_hits)
    lower=get('Lower_L_');upper=get('Upper_L_');cover=get('MCU_RAISED_');tray=get('BATTERY_REMOVABLE_CARRIER_');cell=get('BATTERY_CELL_NOMINAL_42')
    for o in [lower,upper,cover]:assert abs(o.component.bRepBodies.item(0).volume*1000-report['metalVolumes_mm3'][o.component.name])<1e-4
    assert tray.component.bRepBodies.count==1 and cell.component.bRepBodies.count==1
    assert not hits([upper,cover,get('USB_CABLE_')]);assert not hits([lower,upper,cover,get('KEYCAP_SWEEP_')])
    # The short exit transition intentionally touches the cell at its assumed terminal corner.
    # Check its D3 reservation against other parts using temporary world-space BRep copies.
    mgr=adsk.fusion.TemporaryBRepManager.get()
    def pt(v):return adsk.core.Point3D.create(*[x/10 for x in v])
    first=report['assumedCellExitCornerGlobal_mm'];last=report['wireRouteCenters_mm'][0]
    transition=mgr.createSphere(pt(first),.15)
    assert mgr.booleanOperation(transition,mgr.createCylinderOrCone(pt(first),.15,pt(last),.15),adsk.fusion.BooleanTypes.UnionBooleanType)
    assert mgr.booleanOperation(transition,mgr.createSphere(pt(last),.15),adsk.fusion.BooleanTypes.UnionBooleanType)
    transition_hits=[]
    for o in obstacles:
        for b in o.component.bRepBodies:
            world=mgr.copy(b);assert mgr.transform(world,o.transform2)
            test=mgr.copy(transition);assert mgr.booleanOperation(test,world,adsk.fusion.BooleanTypes.IntersectionBooleanType)
            if test.volume>1e-8:transition_hits.append([o.component.name,test.volume*1000])
    assert not transition_hits,str(transition_hits)
    placement=json.load(open(BASE+'docs/choc-v2-placement-verification.json',encoding='utf-8'));n=0
    for prefix in ['CHOC_V2_RED_DETAILED_','CHOC_SOCKET_DETAILED_']:
        refs=[o for o in root.allOccurrences if o.component.name.startswith(prefix)];assert len(refs)==23
        for o in refs:
            t=o.transform2.translation;e=placement['positionChecks'][n]['expected_mm'];assert max(abs(x-y) for x,y in zip([t.x*10,t.y*10,t.z*10],e))<1e-6;n+=1
    retired=[o for o in root.occurrences if o.component.name.startswith(('RETIRED_V15_','RETIRED_CELL42_INITIAL_'))]
    assert len(retired)==8
    group=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());group.component.name='RETIRED_BATTERY_LAYOUTS_NOT_CURRENT'
    for o in retired:
        expected=o.transform2.asArray();moved=o.moveToComponent(group);assert moved
        assert max(abs(x-y) for x,y in zip(expected,moved.transform2.asArray()))<1e-8
    group.isLightBulbOn=False
    if d.snapshots.hasPendingSnapshot:d.snapshots.add()
    assert d.computeAll();issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    view=a.activeViewport;camera=view.camera;visibility=[(o,o.isLightBulbOn) for o in root.occurrences]
    for o,flag in visibility:o.isLightBulbOn=o.component.name.startswith(('Lower_L_','BATTERY_REMOVABLE_CARRIER_','BATTERY_CELL_NOMINAL_42','BATTERY_WIRE_ROUTE_D3_CELL42','B1_JST_'))
    view.fit();assert view.saveAsImageFile(BASE+'docs/images/v05-cell42-and-wire40-layout.png',1500,1100)
    for o,flag in visibility:o.isLightBulbOn=flag
    view.camera=camera
    assert doc.save('Fit requested 42x20x5 battery with 43x21 carrier and 40mm wire budget; case unchanged, 31.08mm assumed connection route. Actual battery/terminal fit pending.')
    ex=d.exportManager
    assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.f3d'))
    visible=tray.isLightBulbOn;tray.isLightBulbOn=True
    assert ex.execute(ex.createSTEPExportOptions(BASE+'cad/design/battery_carrier_provisional_NONMETAL_NOT_FOR_MANUFACTURE_LOCAL.step',tray.component))
    tray.isLightBulbOn=visible
    report.update(installationSpaceInterferences=installation_hits,cornerTransitionInterferences=transition_hits,fitReport='internal-retention-fit-verification.json',checkedChocDatums=n,coreSolidCount=fit['coreSolidCount'],timelineIssues=issues,retiredLayoutsGrouped=8,cloudVersionAtSaveRequest=doc.dataFile.versionNumber)
    json.dump(report,open(BASE+'docs/battery42-layout-development.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(dict(installationHits=installation_hits,transitionHits=transition_hits,chocDatums=n,timelineIssues=issues,routeIncludingCorner_mm=report['nominalConnectionRouteIncludingCorner_mm'],wireBudget_mm=40,caseUnchanged=True)))
