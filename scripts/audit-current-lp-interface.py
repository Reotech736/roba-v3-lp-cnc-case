"""Fusion MCP readOnly: current 23-pair LP interface against unchanged balo43_L v5.

Open both documents before running. Uses temporary copies only; no save/activation.
Legacy PCB is mechanical evidence, never the user's electrical PCB revision.
"""
import adsk.core, adsk.fusion, json, math
from pathlib import Path
BASE = Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')


def run(context):
    app = adsk.core.Application.get()
    doc = next(x for x in app.documents if x.dataFile.id == 'urn:adsk.wipprod:dm.lineage:H9Nq8f1PSl6GXmxJMgIkbw')
    old = next(x for x in app.documents if x.name == 'balo43_L')
    assert not doc.isModified and not old.isModified
    assert doc.dataFile.versionNumber in [22,23,24,25] and old.dataFile.versionNumber == 5
    design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    legacy = adsk.fusion.Design.cast(old.products.itemByProductType('DesignProductType'))
    mgr = adsk.fusion.TemporaryBRepManager.get()
    root = design.rootComponent
    approved = json.loads((BASE/'docs/current-approved-component-state.json').read_text(encoding='utf-8'))
    actual = {o.fullPathName:o for o in root.allOccurrences}
    for row in approved:
        o = actual[row['path']]
        assert max(abs(a-b) for a,b in zip(o.transform2.asArray(),row['matrix'])) < 1e-8, row['path']
        assert o.component.bRepBodies.count == row['bodies']
        assert all(abs(b.volume*1000-v)<1e-5 for b,v in zip(o.component.bRepBodies,row['volumes']))
    board = json.loads((BASE/'cad/design/pcb_v2_layout_input.json').read_text(encoding='utf-8'))['boards'][0]
    u = next(f for f in board['footprints'] if f['reference']=='U1')
    ux,uy = map(float,u['at'][:2])
    source = next(c.bRepBodies.item(0) for c in legacy.allComponents if c.name=='roba_L_PCB')
    oldbody = mgr.copy(source)
    tr = adsk.core.Matrix3D.create();tr.translation = adsk.core.Vector3D.create(-ux/10,uy/10,0)
    assert mgr.transform(oldbody,tr)
    holes = []
    for face in oldbody.faces:
        g = face.geometry
        if g.objectType != adsk.core.Cylinder.classType() or abs(g.axis.z)<.999999:
            continue
        # Require a full-height cylindrical wall; excludes unrelated corner arcs.
        if face.boundingBox.maxPoint.z-face.boundingBox.minPoint.z < .1509:
            continue
        h = [g.origin.x*10,g.origin.y*10,g.radius*10]
        if not any(math.dist(h,q)<1e-5 for q in holes):holes.append(h)
    def intersect(first,second):
        aa,bb=first.boundingBox,second.boundingBox
        if any(min(getattr(aa.maxPoint,c),getattr(bb.maxPoint,c))-max(getattr(aa.minPoint,c),getattr(bb.minPoint,c))<=1e-7 for c in ['x','y','z']):
            return None
        b=mgr.copy(first)
        assert mgr.booleanOperation(b,second,adsk.fusion.BooleanTypes.IntersectionBooleanType)
        return b
    def overlap(first,second):
        b=intersect(first,second)
        return 0 if b is None else b.volume*1000
    def box(x0,y0,z0,x1,y1,z1):
        return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(
            adsk.core.Point3D.create((x0+x1)/20,(y0+y1)/20,(z0+z1)/20),
            adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),
            (x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
    def bodies(o):
        for b in o.bRepBodies:yield o.component.name,b
        for c in o.childOccurrences:yield from bodies(c)
    group=next(o for o in root.occurrences if o.component.name=='CHOC_SWITCHES_AND_SOCKETS_REFERENCE_23_PAIRS')
    keys=json.loads((BASE/'docs/lp-seating-revision-verification.json').read_text(encoding='utf-8'))['keys']
    switches=[o for o in group.childOccurrences if o.component.name.startswith('CHOC_V2_RED_')]
    sockets=[o for o in group.childOccurrences if o.component.name.startswith('CHOC_SOCKET_')]
    assert len(switches)==len(sockets)==len(keys)==23
    assert not any(o.component.name=='pin3' for o in root.allOccurrences)
    upper=next(o for o in root.occurrences if o.component.name.startswith('Upper_L_')).bRepBodies.item(0)
    rows=[]
    slab=box(-150,-150,0,50,50,1.51)
    for k,sw,so in zip(keys,switches,sockets):
        angle=k['chocModelAngle_rad'];ct,st=math.cos(angle),math.sin(angle)
        assert max(abs(sw.transform2.translation.asArray()[i]*10-v) for i,v in enumerate([k['x'],k['y'],1.6]))<1e-5
        assert abs(sw.transform2.asArray()[0]-ct)<1e-8 and abs(sw.transform2.asArray()[4]-st)<1e-8
        row={'key':k['reference'],'centerXY_mm':[k['x'],k['y']],'parts':[]}
        for kind,occ in [('switch',sw),('socket',so)]:
            for name,b in bodies(occ):
                assert name!='pin3'
                collision=overlap(b,oldbody)
                rec={'kind':kind,'component':name,'legacyPCBOverlap_mm3':collision,
                     'upperCaseOverlap_mm3':overlap(b,upper)}
                if name in ['pin1','pin2']:
                    cut=intersect(b,slab)
                    assert cut.volume>0
                    # De-rotate the actual pin section before taking its bounds.
                    # A rotated world AABB is biased by asymmetric rounded ends.
                    inverse=sw.transform2.copy();assert inverse.invert()
                    assert mgr.transform(cut,inverse)
                    bb=cut.boundingBox
                    local=adsk.core.Point3D.create((bb.minPoint.x+bb.maxPoint.x)/2,(bb.minPoint.y+bb.maxPoint.y)/2,0)
                    assert local.transformBy(sw.transform2)
                    p=[local.x*10,local.y*10]
                    nearest=min(holes,key=lambda h:math.dist(p,h[:2]))
                    rec.update(pinPCBSlabBoundsSwitchLocal_mm=[[v*10 for v in q.asArray()] for q in [bb.minPoint,bb.maxPoint]],
                               pinSlabCenterXY_mm=p,nearestHoleXYRadius_mm=nearest,
                               centerError_mm=math.dist(p,nearest[:2]))
                row['parts'].append(rec)
        centers=[]
        for dx,dy,radius in [(0,0,2.5),(0,-5.9,1.5),(-5,-3.7,1.5)]:
            p=[k['x']+ct*dx-st*dy,k['y']+st*dx+ct*dy]
            candidates=[h for h in holes if abs(h[2]-radius)<1e-4]
            h=min(candidates,key=lambda h:math.dist(p,h[:2]))
            centers.append({'role':'central_post' if radius==2.5 else 'socket_receiver',
                            'expectedXY_mm':p,'legacyXYRadius_mm':h,'error_mm':math.dist(p,h[:2])})
        row['holeCenters']=centers
        rows.append(row)
    issues=[t.errorOrWarningMessage for t in design.timeline if t.errorOrWarningMessage]
    summary={'keys':len(rows),'partsChecked':sum(len(r['parts']) for r in rows),
             'legacyPCBOverlapCount':sum(p['legacyPCBOverlap_mm3']>1e-5 for r in rows for p in r['parts']),
             'upperCaseOverlapCount':sum(p['upperCaseOverlap_mm3']>1e-5 for r in rows for p in r['parts']),
             'maxHoleCenterError_mm':max(h['error_mm'] for r in rows for h in r['holeCenters']),
             'pin1MaxCenterError_mm':max(p['centerError_mm'] for r in rows for p in r['parts'] if p['component']=='pin1'),
             'pin2MaxCenterError_mm':max(p['centerError_mm'] for r in rows for p in r['parts'] if p['component']=='pin2')}
    out={'date':'2026-11-08','cloudVersion':doc.dataFile.versionNumber,'geometryModified':False,'legacyCloudVersion':5,
         'legacyPCBThickness_mm':1.51,'currentPCBThicknessAssumed_mm':1.6,
         'legacyToCurrentTranslation_mm':[-ux,uy,0],'approvedStateMatched':True,'pin3Absent':True,
         'summary':summary,'timelineIssues':issues,'keys':rows,
         'limitations':['Legacy solid has mechanical holes but does not certify electrical pads, nets or actual PCB revision.',
                        'Pin centers use actual proxy material clipped to old PCB Z0..1.51; not whole component bounding boxes.',
                        '0.09 mm thickness difference remains. Generic Red is not exact Spring MINI geometry.',
                        'Static latch/case collision check does not demonstrate snap insertion, retention force or removal access.',
                        'No physical PCB, switch, socket, keycap or tolerance acceptance inferred.']}
    (BASE/'docs/current-lp-interface-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert not doc.isModified and not old.isModified
    print(json.dumps(summary))
