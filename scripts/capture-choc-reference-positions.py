"""Fusion MCP: capture all instance transforms before recompute; verify every datum."""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'


def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    keys=json.load(open(BASE+'docs/lp-seating-revision-verification.json',encoding='utf-8'))['keys']
    groups=[]
    for kind,prefix,dx,dy,z in [('switch','CHOC_V2_RED_DETAILED_',0,0,1.6),('socket','CHOC_SOCKET_DETAILED_',0,-5.9,-1.85)]:
        refs=[o for o in root.occurrences if o.component.name.startswith(prefix)];assert len(refs)==23
        for o,k in zip(refs,keys):
            t=k['angle'];ct=math.cos(t);st=math.sin(t);m=adsk.core.Matrix3D.create()
            m.setWithCoordinateSystem(adsk.core.Point3D.create((k['x']+ct*dx-st*dy)/10,(k['y']+st*dx+ct*dy)/10,z/10),adsk.core.Vector3D.create(ct,st,0),adsk.core.Vector3D.create(-st,ct,0),adsk.core.Vector3D.create(0,0,1))
            o.transform2=m
        groups.append((kind,refs,dx,dy,z))
    assert d.snapshots.hasPendingSnapshot
    d.snapshots.add().name='Capture_46_Choc_component_positions_before_recompute'
    assert d.computeAll()
    records=[];origins=[]
    def walk(o,kind,key):
        for b in o.bRepBodies:
            bb=b.boundingBox;records.append(dict(kind=kind,key=key,component=o.component.name,body=b.name,boundsGlobal_mm=[[p.x*10,p.y*10,p.z*10] for p in [bb.minPoint,bb.maxPoint]]))
        for ch in o.childOccurrences:walk(ch,kind,key)
    for kind,refs,dx,dy,z in groups:
        for o,k in zip(refs,keys):
            t=k['angle'];ct=math.cos(t);st=math.sin(t);v=o.transform2.translation
            expected=[k['x']+ct*dx-st*dy,k['y']+st*dx+ct*dy,z]
            actual=[v.x*10,v.y*10,v.z*10]
            assert max(abs(a-b) for a,b in zip(actual,expected))<1e-6,str((actual,expected))
            origins.append(dict(kind=kind,key=k['reference'],actual_mm=actual,expected_mm=expected))
            walk(o,kind,k['reference'])
    assert len(records)==345 and len(origins)==46
    # Every stem top must now be at Z=10.2, proving placement in assembly context.
    stems=[r for r in records if r['kind']=='switch' and r['component']=='stem']
    assert len(stems)==23 and all(abs(r['boundsGlobal_mm'][1][2]-10.2)<1e-5 for r in stems)
    path=BASE+'docs/choc-v2-placement-verification.json';report=json.load(open(path,encoding='utf-8'))
    report.update(records=records,positionChecks=origins,positionsCaptured=True,datumCheck='46 origins and 23 released stem tops checked after computeAll',
                  invalidatedEarlierFitResults=True)
    json.dump(report,open(path,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(dict(positionChecks=46,stemTopChecks=23,stemTopZ_mm=10.2,positionsCaptured=True)))
