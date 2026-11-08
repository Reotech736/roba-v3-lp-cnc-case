"""Fusion MCP: rotate 23 detailed Choc switches/socket pairs by180 about key centers.

Physical photo plus all23 legacy pin-hole pairs support the correction. Case geometry unchanged.
"""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'

def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE' and doc.dataFile.versionNumber==19 and not doc.dataFile.isReadOnly
    assert not d.snapshots.hasPendingSnapshot,'Resolve unrelated pending placement changes first'
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/checkpoints/v05_cloud_v19_before_choc_orientation_correction.f3d'))
    legacy=json.load(open(BASE+'docs/old-vs-current-choc-pin-orientation.json',encoding='utf-8'))
    assert len(legacy)==23 and all(row['variants'][1]['maxError_mm']<1e-4 for row in legacy)
    keys=json.load(open(BASE+'docs/lp-seating-revision-verification.json',encoding='utf-8'))['keys']
    group=next(o for o in root.occurrences if o.component.name=='CHOC_SWITCHES_AND_SOCKETS_REFERENCE_23_PAIRS')
    identity=adsk.core.Matrix3D.create().asArray();assert max(abs(x-y) for x,y in zip(group.transform2.asArray(),identity))<1e-8
    before=[]
    for o in root.allOccurrences:
        before.append(dict(name=o.component.name,path=o.fullPathName,matrix=list(o.transform2.asArray()),volumes=[b.volume*1000 for b in o.component.bRepBodies],visible=o.isLightBulbOn))
    json.dump(before,open(BASE+'docs/choc-orientation-correction-baseline.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    placements=[]
    for kind,prefix in [('switch','CHOC_V2_RED_DETAILED_'),('socket','CHOC_SOCKET_DETAILED_')]:
        refs=[o for o in group.childOccurrences if o.component.name.startswith(prefix)];assert len(refs)==23
        for o,k in zip(refs,keys):
            oldAngle=k['angle'];theta=oldAngle+math.pi;ct=math.cos(theta);st=math.sin(theta)
            dx=0;dy=-5.9 if kind=='socket' else 0;z=-1.85 if kind=='socket' else 1.6
            expectedOld=[k['x']-math.sin(oldAngle)*dy,k['y']+math.cos(oldAngle)*dy,z]
            translation=o.transform2.translation
            assert max(abs(x-y) for x,y in zip([translation.x*10,translation.y*10,translation.z*10],expectedOld))<1e-5,str((kind,k['reference']))
            m=adsk.core.Matrix3D.create();m.setWithCoordinateSystem(adsk.core.Point3D.create((k['x']+ct*dx-st*dy)/10,(k['y']+st*dx+ct*dy)/10,z/10),adsk.core.Vector3D.create(ct,st,0),adsk.core.Vector3D.create(-st,ct,0),adsk.core.Vector3D.create(0,0,1))
            old=list(o.transform2.asArray());o.transform2=m
            placements.append(dict(kind=kind,key=k['reference'],centerXY_mm=[k['x'],k['y']],oldAngle_rad=oldAngle,newAngle_rad=theta,oldMatrix=old,newMatrix=list(m.asArray()),expected_mm=[k['x']-st*dy,k['y']+ct*dy,z]))
    if d.snapshots.hasPendingSnapshot:d.snapshots.add()
    assert d.computeAll()
    actual=[]
    for kind,prefix in [('switch','CHOC_V2_RED_DETAILED_'),('socket','CHOC_SOCKET_DETAILED_')]:
        for o,expected in zip([o for o in group.childOccurrences if o.component.name.startswith(prefix)],[p for p in placements if p['kind']==kind]):
            assert max(abs(x-y) for x,y in zip(o.transform2.asArray(),expected['newMatrix']))<1e-8,expected['key']
            actual.append(dict(kind=kind,key=expected['key'],matrix=list(o.transform2.asArray())))
    after=[dict(name=o.component.name,path=o.fullPathName,matrix=list(o.transform2.asArray()),volumes=[b.volume*1000 for b in o.component.bRepBodies],visible=o.isLightBulbOn) for o in root.allOccurrences]
    assert len(before)==len(after)
    for old,new in zip(before,after):
        assert old['name']==new['name'] and old['volumes']==new['volumes'] and old['visible']==new['visible']
        if 'CHOC_SWITCHES_AND_SOCKETS_REFERENCE_23_PAIRS:1+' not in old['path']:assert old['matrix']==new['matrix'],old['name']
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    out=dict(date='2026-11-08',baselineCloudVersion=19,rotationCorrection_deg=180,correctedSwitches=23,correctedSockets=23,positionsCaptured=True,placements=placements,actualChecks=actual,
        legacyHolePairsMatched=23,legacyHoleMatchTolerance_mm=.0001,legacyBoard='balo43_L v5; read-only inspection, no edits',caseAndCarrierGeometryUnchanged=True,otherComponentTransformsUnchanged=True,timelineIssues=issues,
        limitations=['Legacy custom-drilled3D board is mechanical corroboration, not a PCB electrical revision/netlist certification',
        'Public v2 normal SW_MX footprints lack the added full-LP hole pairs; thumb SW_MX_Choc includes Choc holes',
        'Author generic ChocV2 pin2 center differs from socket/legacy hole by approx0.1mm; exact SpringMini variant and actual socket model remain unconfirmed',
        'Re-run case/socket/MCU/wire/support checks in the corrected orientation before declaring arrangement clear'])
    json.dump(out,open(BASE+'docs/choc-orientation-correction.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in out.items() if k not in ['placements','actualChecks']},ensure_ascii=False))
