"""Fusion MCP: distinguish actual case collisions from internal component overlaps."""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'


def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    placement=json.load(open(BASE+'docs/choc-v2-placement-verification.json',encoding='utf-8'))
    assert placement.get('positionsCaptured'), 'Capture and verify instance positions before fit analysis'
    keys=json.load(open(BASE+'docs/lp-seating-revision-verification.json',encoding='utf-8'))['keys']
    targets=[o for o in root.occurrences if o.component.name.startswith(('Upper_L_','Lower_L_','MCU_RAISED_','Battery_L_','XIAO_KEY_SIDE_ENVELOPE_'))]
    target_names={o.component.name for o in targets};out=[]
    for kind,prefix in [('switch','CHOC_V2_RED_DETAILED_'),('socket','CHOC_SOCKET_DETAILED_')]:
        refs=[o for o in root.occurrences if o.component.name.startswith(prefix)];assert len(refs)==23
        entities=adsk.core.ObjectCollection.create();lookup={}
        for o in targets:entities.add(o)
        def walk(o,key):
            for b in o.bRepBodies:
                entities.add(b);lookup[o.fullPathName]=key
            for child in o.childOccurrences:walk(child,key)
        for o,k in zip(refs,keys):walk(o,k['reference'])
        i=d.createInterferenceInput(entities);i.areCoincidentFacesIncluded=False;r=d.analyzeInterference(i)
        hits=[];internal=0
        for h in r:
            one=h.entityOne;two=h.entityTwo
            if one.parentComponent.name not in target_names and two.parentComponent.name not in target_names:
                internal+=1;continue
            if one.parentComponent.name in target_names:target,part=one,two
            else:target,part=two,one
            bb=h.interferenceBody.boundingBox
            hits.append(dict(key=lookup.get(part.assemblyContext.fullPathName) if part.assemblyContext else None,
                target=target.parentComponent.name,component=part.parentComponent.name,volume_mm3=h.interferenceBody.volume*1000,
                boundsGlobal_mm=[[p.x*10,p.y*10,p.z*10] for p in [bb.minPoint,bb.maxPoint]]))
        out.append(dict(kind=kind,count=len(hits),collisions=hits,internalOverlapsExcluded=internal))
    report=dict(date='2026-11-08',coincidentFacesIncluded=False,results=out,
                positionsCaptured=True,excluded='Public outline PCB and hidden coarse switch envelopes; neither is the populated PCB or exact switch solid')
    json.dump(report,open(BASE+'docs/detailed-choc-fit-verification.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(report,ensure_ascii=False))
