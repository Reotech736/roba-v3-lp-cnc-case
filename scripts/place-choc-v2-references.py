"""Fusion MCP: instance author Choc V2 references at 23 public switch centers."""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'


def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE' and not doc.dataFile.isReadOnly
    sw=next(o for o in root.occurrences if o.component.name in ['CHOC_V2_RED_AUTHOR_REFERENCE_DATUM_PENDING','CHOC_V2_RED_DETAILED_AUTHOR_REFERENCE'])
    so=next(o for o in root.occurrences if o.component.name in ['CHOC_SOCKET_AUTHOR_REFERENCE_DATUM_PENDING','CHOC_SOCKET_DETAILED_AUTHOR_REFERENCE'])
    assert len([o for o in root.occurrences if o.component==sw.component])==1
    assert len([o for o in root.occurrences if o.component==so.component])==1
    sw.component.name='CHOC_V2_RED_DETAILED_AUTHOR_REFERENCE'
    so.component.name='CHOC_SOCKET_DETAILED_AUTHOR_REFERENCE'
    keys=json.load(open(BASE+'docs/lp-seating-revision-verification.json',encoding='utf-8'))['keys']
    switch_occs=[];socket_occs=[]
    for i,k in enumerate(keys):
        t=k['angle'];ct=math.cos(t);st=math.sin(t)
        def matrix(dx,dy,z):
            m=adsk.core.Matrix3D.create()
            m.setWithCoordinateSystem(adsk.core.Point3D.create((k['x']+ct*dx-st*dy)/10,(k['y']+st*dx+ct*dy)/10,z/10),adsk.core.Vector3D.create(ct,st,0),adsk.core.Vector3D.create(-st,ct,0),adsk.core.Vector3D.create(0,0,1))
            return m
        first=sw if i==0 else root.occurrences.addExistingComponent(sw.component,matrix(0,0,1.6))
        if i==0:first.transform2=matrix(0,0,1.6)
        first.isLightBulbOn=True;switch_occs.append(first)
        socket=so if i==0 else root.occurrences.addExistingComponent(so.component,matrix(0,-5.9,-1.85))
        if i==0:socket.transform2=matrix(0,-5.9,-1.85)
        socket.isLightBulbOn=False;socket_occs.append(socket)
    # Transform changes must be captured before recompute; always run
    # capture-choc-reference-positions.py next to assert all final instance datums.
    if d.snapshots.hasPendingSnapshot:d.snapshots.add()
    d.computeAll()
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    # Record actual body identities and world bounds for independent inspection.
    records=[]
    def walk(o,kind,key):
        for b in o.bRepBodies:
            bb=b.boundingBox
            records.append(dict(kind=kind,key=key,component=o.component.name,body=b.name,
                boundsGlobal_mm=[[p.x*10,p.y*10,p.z*10] for p in [bb.minPoint,bb.maxPoint]]))
        for ch in o.childOccurrences:walk(ch,kind,key)
    for occ,k in zip(switch_occs,keys):walk(occ,'switch',k['reference'])
    for occ,k in zip(socket_occs,keys):walk(occ,'socket',k['reference'])
    report=dict(date='2026-11-08',switchOccurrences=23,socketOccurrences=23,switchSolids=184,socketSolids=161,
                switchPCBSeatingZ_mm=1.6,socketTranslationNative_mm=[0,-5.9,-1.85],
                socketZSource='https://koktoh.hatenablog.com/entry/2023/06/05/173318',
                sourceCommit='2b6bcfac0032f1547e27b18b9a897e065e544b37',records=records,timelineIssues=issues,
                limitations=['Generic Choc V2 Red accepted as reference; not certified exact Spring Mini revision',
                'Socket XY and rotation are provisional; actual PCB holes/solder and installed orientation not validated',
                'Public outline PCB model omits functional switch holes; do not count its pin/locator overlaps as verified incompatibility'])
    assert len(records)==345
    json.dump(report,open(BASE+'docs/choc-v2-placement-verification.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k!='records'},ensure_ascii=False))
