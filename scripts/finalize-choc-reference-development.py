"""Fusion MCP: verify, save, and export detailed Choc + fastening + stand-access study."""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'
NAME='left_case_two_stands_v05_NOT_FOR_MANUFACTURE'


def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.name==NAME and not doc.dataFile.isReadOnly
    restored=json.load(open(BASE+'docs/stand-pocket-restoration-verification.json',encoding='utf-8'))
    assert any(t.name=='Restore_original_stand_pockets_after_finger_backing' for t in d.timeline)
    assert not d.snapshots.hasPendingSnapshot
    assert d.computeAll()
    def find(prefix):return next(o for o in root.occurrences if o.component.name.startswith(prefix))
    upper=find('Upper_L_');lower=find('Lower_L_');cover=find('MCU_RAISED_');pcb=find('PCB_L_');battery=find('Battery_L_');mcu=find('XIAO_KEY_SIDE_');cable=find('USB_CABLE_');sweep=find('KEYCAP_SWEEP_')
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    def analyze(entities):
        coll=adsk.core.ObjectCollection.create()
        for e in entities:coll.add(e)
        i=d.createInterferenceInput(coll);i.areCoincidentFacesIncluded=False;rr=d.analyzeInterference(i)
        return [dict(first=r.entityOne.parentComponent.name,second=r.entityTwo.parentComponent.name,volume_mm3=r.interferenceBody.volume*1000) for r in rr]
    main=[o for o in root.occurrences if o.component.name.startswith(('Upper_L_','Lower_L_','MCU_RAISED_','PCB_L_','Battery_L_','XIAO_KEY_SIDE_','SWITCH_'))]
    core=analyze(main);assert not core,str(core)
    cab=analyze([upper,cover,cable]);assert not cab,str(cab)
    caphits=analyze([upper,lower,cover,sweep]);assert not caphits,str(caphits)
    # Detailed MCU has internal model intersections; filter only collisions with case parts.
    mcu_parts=[]
    def walk(o):
        for b in o.bRepBodies:mcu_parts.append(b)
        for ch in o.childOccurrences:walk(ch)
    walk(find('XIAO_DETAILED_'));assert len(mcu_parts)==77
    names={o.component.name for o in [upper,lower,cover]}
    detailed=analyze([upper,lower,cover]+mcu_parts)
    detailed_case=[h for h in detailed if h['first'] in names or h['second'] in names]
    assert not detailed_case,str(detailed_case)
    placement=json.load(open(BASE+'docs/choc-v2-placement-verification.json',encoding='utf-8'));assert placement['positionsCaptured']
    # Verify all 46 origins against the recorded captured transforms after all geometry edits.
    coords=placement['positionChecks'];index=0
    for prefix in ['CHOC_V2_RED_DETAILED_','CHOC_SOCKET_DETAILED_']:
        occs=[o for o in root.allOccurrences if o.component.name.startswith(prefix)];assert len(occs)==23
        for o in occs:
            v=o.transform2.translation;expected=coords[index]['expected_mm'];actual=[v.x*10,v.y*10,v.z*10]
            assert max(abs(x-y) for x,y in zip(actual,expected))<1e-6;index+=1
    assert index==46
    keys=json.load(open(BASE+'docs/lp-seating-revision-verification.json',encoding='utf-8'))['keys']
    tab_gaps=[]
    for x in [-8,8]:
        gaps=[]
        for k in keys:
            dx=x-k['x'];dy=3.8-k['y'];t=k['angle'];xx=math.cos(t)*dx+math.sin(t)*dy;yy=-math.sin(t)*dx+math.cos(t)*dy
            gap=math.hypot(max(abs(xx)-9.4,0),max(abs(yy)-9.4,0))-1.8
            gaps.append((gap,k['reference']))
        tab_gaps.append(dict(x=x,gap_mm=min(gaps)[0],closestKey=min(gaps)[1]))
    assert min(g['gap_mm'] for g in tab_gaps)>.6
    for o in [upper,lower,cover]:assert o.component.bRepBodies.count==1
    old=next(x for x in a.documents if x.dataFile and x.dataFile.id=='urn:adsk.wipprod:dm.lineage:mwqP27TVRxe5Ray66zFHMg')
    assert not old.isModified and old.dataFile.versionNumber==2
    view=a.activeViewport;view.visualStyle=adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle;view.fit()
    assert view.saveAsImageFile(BASE+'docs/images/v05-detailed-choc-front-fastening.png',1500,1100)
    assert doc.save('Reuse detailed Choc V2 and sockets at captured 23 key datums; relocate PCB support, add provisional front MCU-cover screws and backed stand finger notches.')
    ex=d.exportManager
    assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/'+NAME+'.f3d'))
    for o,label in [(lower,'Lower_L'),(upper,'Upper_L_protective_roof'),(cover,'MCU_cover_concept')]:
        assert ex.execute(ex.createSTEPExportOptions(BASE+'cad/design/'+NAME+'_'+label+'_LOCAL.step',o.component))
    out=dict(date='2026-11-08',id=doc.dataFile.id,cloudVersion=doc.dataFile.versionNumber,cloudComplete=doc.dataFile.isComplete,modified=doc.isModified,
             coreSolids=52,coreInterferences=core,cableVsCasingInterferences=cab,assumedCapSweepVsCasingInterferences=caphits,
             detailedMCUVsCasingInterferences=detailed_case,detailedMCUInternalOverlaps=len(detailed)-len(detailed_case),
             checkedChocInstanceOrigins=46,standPocketVoidSamples=restored['pocketVoidSamples'],standFingerResidualSamples=restored['fingerResidualSamples'],coverTabPlanarGaps_mm=tab_gaps,minimumCapToCoverPlanarGap_mm=min(.71934,min(g['gap_mm'] for g in tab_gaps)),
             volumes_mm3={o.component.name:o.component.bRepBodies.item(0).volume*1000 for o in [lower,upper,cover]},
             oldMCUUnmodified=True,timelineIssues=issues,parts=[dict(name=o.component.name,bodyCount=o.component.bRepBodies.count,visible=o.isLightBulbOn) for o in root.occurrences],
             limitations=['Generic Choc V2 reference and provisional socket placement, not an exact measured populated PCB',
                          'Screw thread engagement, head standard, torque and cover rear stiffness remain provisional',
                          'Cap D3.0 and 18.8 mm footprints are assumptions; real cap insertion and rocking not verified',
                          'Stand left access, hinge sweep, tape, feet and physical deployment remain unverified',
                          'Public outline PCB omits functional switch holes and does not establish copper/insulation clearance',
                          'F3D includes third-party CC BY-NC-SA component references; case-only STEP exports exclude them'])
    json.dump(out,open(BASE+'docs/choc-reference-final-verification.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in out.items() if k!='parts'},ensure_ascii=False))
