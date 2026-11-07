"""Fusion MCP: verify revised parts, then save and export the working design."""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'
NAME='left_case_two_stands_v05_NOT_FOR_MANUFACTURE'


def run(_context: str):
    a=adsk.core.Application.get();doc=next(x for x in a.documents if x.name==NAME);doc.activate()
    d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent;assert not doc.dataFile.isReadOnly
    def find(prefix):return next(o for o in root.occurrences if o.component.name.startswith(prefix))
    upper=find('Upper_L_');lower=find('Lower_L_');cover=find('MCU_RAISED_');sweep=find('KEYCAP_SWEEP_');cable=find('USB_CABLE_')
    assert d.computeAll()
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    def analyze(occs):
        ent=adsk.core.ObjectCollection.create()
        for o in occs:ent.add(o)
        i=d.createInterferenceInput(ent);i.areCoincidentFacesIncluded=False;r=d.analyzeInterference(i)
        return [dict(first=h.entityOne.name,second=h.entityTwo.name,volume_mm3=h.interferenceBody.volume*1000) for h in r]
    main=[o for o in root.occurrences if not o.component.name.startswith(('KEYCAP_SWEEP_','USB_CABLE_','XIAO_DETAILED_'))]
    main_hits=analyze(main);assert not main_hits,str(main_hits)
    cable_hits=analyze([cable,upper,cover]);assert not cable_hits,str(cable_hits)
    sweeps=[]
    for o in [lower,upper,cover]:
        hits=analyze([sweep,o]);assert not hits,str(hits);sweeps.append(dict(component=o.component.name,count=len(hits)))
    keys=json.load(open(BASE+'docs/lp-seating-revision-verification.json',encoding='utf-8'))['keys']
    # Use native component coordinates explicitly; upper occurrence is translated by -1 mm Z.
    body=upper.component.bRepBodies.item(0);INSIDE=adsk.fusion.PointContainment.PointInsidePointContainment
    checks=[]
    for k in keys:
        center=adsk.core.Point3D.create(k['x']/10,k['y']/10,.42)
        assert body.pointContainment(center)!=INSIDE
        for side in [-1,1]:
            x=k['x']+math.cos(k['angle'])*side*7.075;y=k['y']+math.sin(k['angle'])*side*7.075
            assert body.pointContainment(adsk.core.Point3D.create(x/10,y/10,.42))==INSIDE
        checks.append(k['reference'])
    assert abs(lower.component.bRepBodies.item(0).volume*1000-35980.3191099943)<.0001
    for o in [upper,lower,cover]:assert o.component.bRepBodies.count==1
    # Preserve modeled geometry, showing actual reused MCU rather than its clearance box.
    for o in root.occurrences:
        if o.component.name.startswith(('KEYCAP_SWEEP_','USB_CABLE_','SWITCH_','XIAO_KEY_SIDE_ENVELOPE_')):o.isLightBulbOn=False
    old=next(x for x in a.documents if x.dataFile and x.dataFile.id=='urn:adsk.wipprod:dm.lineage:mwqP27TVRxe5Ray66zFHMg')
    assert not old.isModified and old.dataFile.versionNumber==2
    assert doc.save('Correct nominal LP flange seating to Z3.8; raised-skirt cover, keycap sweep clearance, and reused detailed old XIAO reference. Physical fit and retention pending.')
    ex=d.exportManager
    assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/'+NAME+'.f3d'))
    for o,label in [(lower,'Lower_L'),(upper,'Upper_L_protective_roof'),(cover,'MCU_cover_concept')]:
        assert ex.execute(ex.createSTEPExportOptions(BASE+'cad/design/'+NAME+'_'+label+'_LOCAL.step',o.component))
    out=dict(date='2026-11-08',id=doc.dataFile.id,cloudVersion=doc.dataFile.versionNumber,
             cloudComplete=doc.dataFile.isComplete,modified=doc.isModified,roofTopZ_mm=3.8,roofBottomZ_mm=2.6,roofThickness_mm=1.2,
             mainAssemblyInterferences=main_hits,mainAssemblySolidCount=sum(o.component.bRepBodies.count for o in main),
             cableAccessInterferences=cable_hits,keycapSweepChecks=sweeps,assumedCapD_mm=3.0,keycapSweepLowerZ_mm=4.15,
             capToRoofNominalGap_mm=.35,capToRelievedRimNominalGap_mm=.25,
             openingsChecked=len(checks),roofLedgePointsChecked=46,lowerVolumeUnchanged=True,
             upperVolume_mm3=upper.component.bRepBodies.item(0).volume*1000,coverVolume_mm3=cover.component.bRepBodies.item(0).volume*1000,
             coverPlanGap_mm=.71934,oldXiaoSourceVersion=2,oldXiaoSourceUnmodified=True,timelineIssues=issues,
             limitations=['Nominal dimensions and assumed D3.0 cap seating, not measured physical fit',
                         'Full switch CAD, latch/socket/pin engagement and real cap underside still pending',
                         'Cover retention, lower openings, RF, tolerance and manufacturing review unresolved',
                         'Detailed old MCU provenance and real installed revision/placement unverified'])
    with open(BASE+'docs/lp-seating-final-verification.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False))
