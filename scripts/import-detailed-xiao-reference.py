"""Fusion MCP: reuse exported old XIAO component without editing its source."""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'


def run(_context: str):
    a=adsk.core.Application.get()
    doc=next(x for x in a.documents if x.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE')
    doc.activate();d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert not doc.dataFile.isReadOnly
    name='XIAO_DETAILED_FROM_OLD_V2_PLACEMENT_UNVERIFIED'
    assert not any(o.component.name==name for o in root.occurrences)
    # old X -> new Y; old Y -> new Z; old Z -> new X. Preserve all source solids.
    m=adsk.core.Matrix3D.create()
    assert m.setWithCoordinateSystem(adsk.core.Point3D.create(.61114,-1.228166,.185),
        adsk.core.Vector3D.create(0,1,0),adsk.core.Vector3D.create(0,0,1),adsk.core.Vector3D.create(1,0,0))
    wrapper=root.occurrences.addNewComponent(m);wrapper.component.name=name
    options=a.importManager.createSTEPImportOptions(BASE+'cad/reference/components/xiao-nrf52840-v3_old_v2.step')
    result=a.importManager.importToTarget2(options,wrapper.component);assert result is not None
    # Replacing the display reference does not remove the conservative clearance tool.
    for o in root.occurrences:
        if o.component.name=='XIAO_KEY_SIDE_ENVELOPE_FROM_OLD_SINGLE_PART_UNVERIFIED':o.isLightBulbOn=False
    occs=[]
    def walk(o):
        occs.append(o)
        for c in o.childOccurrences:walk(c)
    walk(wrapper)
    body_count=sum(o.bRepBodies.count for o in occs)
    bounds=[]
    for o in occs:
        for b in o.bRepBodies:
            bb=b.boundingBox
            bounds.append([[v*10 for v in (p.x,p.y,p.z)] for p in [bb.minPoint,bb.maxPoint]])
    bb=[[min(b[0][i] for b in bounds) for i in range(3)],[max(b[1][i] for b in bounds) for i in range(3)]]
    collision=[]
    for target in root.occurrences:
        if not target.component.name.startswith(('Upper_L_','Lower_L_','MCU_RAISED_')):continue
        # Pass the assembly-context bodies explicitly to avoid treating only the empty wrapper.
        ent=adsk.core.ObjectCollection.create();ent.add(target)
        for o in occs:
            for b in o.bRepBodies:ent.add(b)
        ii=d.createInterferenceInput(ent);ii.areCoincidentFacesIncluded=False;r=d.analyzeInterference(ii)
        # Internal component overlaps are recorded separately, not casing collisions.
        hits=[]
        for hit in r:
            one=hit.entityOne;two=hit.entityTwo
            if one.parentComponent==target.component or two.parentComponent==target.component:
                hits.append(dict(first=one.name,second=two.name,volume_mm3=hit.interferenceBody.volume*1000))
        collision.append(dict(component=target.component.name,collisions=hits,totalIncludingInternal=r.count))
    out=dict(date='2026-11-08',sourceId='urn:adsk.wipprod:dm.lineage:mwqP27TVRxe5Ray66zFHMg',sourceVersion=2,
             sourceUnmodified=True,bodyCount=body_count,boundsGlobal_mm=bb,transform=m.asArray(),results=collision,
             limitations=['Old model provenance and match to installed revision not established','Placement uses existing PCB-top and connector datum assumptions','Conservative envelope retained as hidden clearance tool'])
    with open(BASE+'docs/detailed-xiao-reference-verification.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False))
