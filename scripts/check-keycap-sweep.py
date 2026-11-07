"""Fusion MCP: create explicit D=3 mm provisional swept-volume tools and inspect cases."""
import adsk.core, adsk.fusion, json, math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'


def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert a.activeDocument.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE'
    assert not any(o.component.name.startswith('KEYCAP_SWEEP_') for o in root.occurrences)
    keys=json.load(open(BASE+'docs/lp-seating-revision-verification.json',encoding='utf-8'))['keys']
    c=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    c.name='KEYCAP_SWEEP_D3p0_18p8_SQUARE_ASSUMED_NOT_PARTS'
    i=c.constructionPlanes.createInput();i.setByOffset(c.xYConstructionPlane,adsk.core.ValueInput.createByString('4.15 mm'))
    plane=c.constructionPlanes.add(i);plane.isLightBulbOn=False;s=c.sketches.add(plane)
    for k in keys:
        q=9.4;t=k['angle'];x=k['x'];y=k['y']
        pp=[adsk.core.Point3D.create((x+math.cos(t)*i-math.sin(t)*j)/10,(y+math.sin(t)*i+math.cos(t)*j)/10,0) for i,j in [(-q,-q),(q,-q),(q,q),(-q,q)]]
        for p0,p1 in zip(pp,pp[1:]+pp[:1]):s.sketchCurves.sketchLines.addByTwoPoints(p0,p1).isFixed=True
    assert s.profiles.count==23
    profiles=adsk.core.ObjectCollection.create()
    for p in s.profiles:profiles.add(p)
    e=c.features.extrudeFeatures.addSimple(profiles,adsk.core.ValueInput.createByString('6.99 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    e.name='Swept_bounds_max_travel_3p05_plus_cap_height_3p94_D3p0';s.isLightBulbOn=False
    assert c.bRepBodies.count==23
    # Associate reference names spatially, not by Fusion body enumeration order.
    for b in c.bRepBodies:
        center=b.physicalProperties.centerOfMass
        k=min(keys,key=lambda k:math.hypot(k['x']-center.x*10,k['y']-center.y*10))
        b.name='Sweep_'+k['reference']+'_D3p0_ASSUMED'
    sweep=next(o for o in root.occurrences if o.component==c)
    out=[]
    for o in root.occurrences:
        if not o.component.name.startswith(('Upper_L_','Lower_L_','MCU_RAISED_')):continue
        entities=adsk.core.ObjectCollection.create();entities.add(sweep);entities.add(o)
        ii=d.createInterferenceInput(entities);ii.areCoincidentFacesIncluded=False;r=d.analyzeInterference(ii)
        out.append(dict(component=o.component.name,collisions=[dict(first=x.entityOne.name,second=x.entityTwo.name,volume_mm3=x.interferenceBody.volume*1000) for x in r]))
    sweep.isLightBulbOn=False
    report=dict(date='2026-11-08',assumedD_mm=3.0,footprint_mm=18.8,capHeight_mm=3.94,travelMax_mm=3.05,sweptZ_mm=[4.15,11.14],results=out,
                limitations=['Comparison volume, not a measured cap solid','Ignores real underside cavities and full rocking motion','Intentionally excludes switch bodies, which enter cap cavities'])
    with open(BASE+'docs/keycap-sweep-verification.json','w',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps(report,ensure_ascii=False))
