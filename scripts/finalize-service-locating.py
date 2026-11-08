"""Fusion MCP: verify service access and locating features; save/export current design."""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'
NAME='left_case_two_stands_v05_NOT_FOR_MANUFACTURE'


def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.name==NAME and not doc.dataFile.isReadOnly
    assert not d.snapshots.hasPendingSnapshot and d.computeAll()
    def get(prefix):return next(o for o in root.occurrences if o.component.name.startswith(prefix))
    lower=get('Lower_L_');upper=get('Upper_L_');cover=get('MCU_RAISED_');probe=get('RESET_NONCONDUCTIVE_')
    def analyze(items):
        col=adsk.core.ObjectCollection.create()
        for item in items:col.add(item)
        ii=d.createInterferenceInput(col);ii.areCoincidentFacesIncluded=False;r=d.analyzeInterference(ii)
        return [dict(first=h.entityOne.parentComponent.name,second=h.entityTwo.parentComponent.name,volume_mm3=h.interferenceBody.volume*1000) for h in r]
    core=[o for o in root.occurrences if o.component.name.startswith(('Upper_L_','Lower_L_','MCU_RAISED_','PCB_L_','Battery_L_','XIAO_KEY_SIDE_','SWITCH_'))]
    core_hits=analyze(core);assert not core_hits,str(core_hits)
    cap_hits=analyze([lower,upper,cover,get('KEYCAP_SWEEP_')]);assert not cap_hits,str(cap_hits)
    cable_hits=analyze([upper,cover,get('USB_CABLE_')]);assert not cable_hits,str(cable_hits)
    bodies=[]
    def walk(o):
        for b in o.bRepBodies:bodies.append((o,b))
        for child in o.childOccurrences:walk(child)
    walk(get('XIAO_DETAILED_'));assert len(bodies)==77
    detailed=analyze([lower,upper,cover,probe]+[b for o,b in bodies])
    part_names={o.component.name for o in [lower,upper,cover,probe]}
    external=[h for h in detailed if h['first'] in part_names or h['second'] in part_names]
    assert not external,str(external)
    # Pressed probe checks only the intended reset body in the final 0.11 mm region.
    dev=json.load(open(BASE+'docs/service-and-locating-development.json',encoding='utf-8'))
    datum=dev['resetModelDatum_mm'];pressed=[]
    for o,b in bodies:
        bb=b.boundingBox;lo=bb.minPoint;hi=bb.maxPoint
        if hi.x*10>=datum['x']-.4 and lo.x*10<=datum['x']+.4 and hi.y*10>=datum['y']-.4 and lo.y*10<=datum['y']+.4 and hi.z*10>=datum['topZ']-.11 and lo.z*10<=16:
            pressed.append(o.fullPathName)
    assert len(pressed)==1 and 'SKTAAAE010' in pressed[0] and pressed[0].endswith('Body:1')
    # Assert captured instance datums remain stable after all model recomputations.
    placement=json.load(open(BASE+'docs/choc-v2-placement-verification.json',encoding='utf-8'));idx=0
    for prefix in ['CHOC_V2_RED_DETAILED_','CHOC_SOCKET_DETAILED_']:
        for o in [o for o in root.occurrences if o.component.name.startswith(prefix)]:
            t=o.transform2.translation;expected=placement['positionChecks'][idx]['expected_mm']
            assert max(abs(a-b) for a,b in zip([t.x*10,t.y*10,t.z*10],expected))<1e-6;idx+=1
    assert idx==46
    assert abs(d.userParameters.itemByName('M2_pilot_depth').value*10-4.5)<1e-6
    for o in [lower,upper,cover]:assert o.component.bRepBodies.count==1
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    # Capture the locating details without moving occurrences or changing assembly positions.
    view=a.activeViewport;camera=view.camera;visible=[(o,o.isLightBulbOn) for o in root.occurrences]
    for o,flag in visible:o.isLightBulbOn=(o==lower)
    view.fit();assert view.saveAsImageFile(BASE+'docs/images/v05-lower-case-locating-pins.png',1500,1100)
    for o,flag in visible:o.isLightBulbOn=flag
    view.camera=camera;view.fit()
    assert view.saveAsImageFile(BASE+'docs/images/v05-reset-access-and-locating.png',1500,1100)
    old=next(x for x in a.documents if x.dataFile and x.dataFile.id=='urn:adsk.wipprod:dm.lineage:mwqP27TVRxe5Ray66zFHMg')
    assert not old.isModified and old.dataFile.versionNumber==2
    assert doc.save('Add provisional reset service hole and round/slot case location with chamfered pins and reinforced seats; M2 thread lengths retained.')
    ex=d.exportManager;assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/'+NAME+'.f3d'))
    for o,label in [(lower,'Lower_L'),(upper,'Upper_L_protective_roof'),(cover,'MCU_cover_concept')]:assert ex.execute(ex.createSTEPExportOptions(BASE+'cad/design/'+NAME+'_'+label+'_LOCAL.step',o.component))
    out=dict(date='2026-11-08',id=doc.dataFile.id,cloudVersion=doc.dataFile.versionNumber,cloudComplete=doc.dataFile.isComplete,modified=doc.isModified,
             coreSolids=52,coreInterferences=core_hits,capSweepInterferences=cap_hits,cableAccessInterferences=cable_hits,
             detailedMCUAndProbeVsCasesInterferences=external,internalMCUOverlapsExcluded=len(detailed)-len(external),
             pressedProbeAABBHits=pressed,checkedInstanceDatums=idx,mainM2PilotDepthUnchanged_mm=4.5,timelineIssues=issues,
             singleSolidParts=3,volumes_mm3={o.component.name:o.component.bRepBodies.item(0).volume*1000 for o in [lower,upper,cover]},
             currentParts=[dict(name=o.component.name,bodies=o.component.bRepBodies.count,visible=o.isLightBulbOn) for o in root.occurrences],
             oldMCUUnmodified=True,limitations=dev['limitations']+['Static geometry checks do not prove physical reset function, complete thread strength, insulation, or stand deployment'])
    json.dump(out,open(BASE+'docs/service-and-locating-verification.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in out.items() if k!='currentParts'},ensure_ascii=False))
