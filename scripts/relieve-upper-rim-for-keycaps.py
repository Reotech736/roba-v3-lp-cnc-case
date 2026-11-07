"""Fusion MCP: relieve only upper-rim material around provisional swept caps."""
import adsk.core, adsk.fusion, json, math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'


def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct)
    assert a.activeDocument.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE'
    upper=next(c for c in d.allComponents if c.name.startswith('Upper_L_PROTECTIVE'))
    assert not any(e.name=='Local_rim_clearance_for_18p9_caps_Z3p9' for e in upper.features.extrudeFeatures)
    before=upper.bRepBodies.item(0).volume*1000
    keys=json.load(open(BASE+'docs/lp-seating-revision-verification.json',encoding='utf-8'))['keys']
    # Upper local z = global z + 1 mm. Keep roof, bosses and all other components.
    i=upper.constructionPlanes.createInput();i.setByOffset(upper.xYConstructionPlane,adsk.core.ValueInput.createByString('4.9 mm'))
    plane=upper.constructionPlanes.add(i);plane.isLightBulbOn=False;s=upper.sketches.add(plane)
    s.name='Provisional_keycap_rim_clearance_18p9_not_switch_openings'
    for k in keys:
        q=18.9/2;t=k['angle'];x=k['x'];y=k['y']
        pp=[adsk.core.Point3D.create((x+math.cos(t)*u-math.sin(t)*v)/10,(y+math.sin(t)*u+math.cos(t)*v)/10,0) for u,v in [(-q,-q),(q,-q),(q,q),(-q,q)]]
        for first,last in zip(pp,pp[1:]+pp[:1]):s.sketchCurves.sketchLines.addByTwoPoints(first,last).isFixed=True
    profiles=adsk.core.ObjectCollection.create()
    for p in s.profiles:profiles.add(p)
    i=upper.features.extrudeFeatures.createInput(profiles,adsk.fusion.FeatureOperations.CutFeatureOperation)
    i.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('5 mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
    i.participantBodies=[upper.bRepBodies.item(0)]
    e=upper.features.extrudeFeatures.add(i);e.name='Local_rim_clearance_for_18p9_caps_Z3p9';s.isLightBulbOn=False
    assert upper.bRepBodies.count==1
    removed=before-upper.bRepBodies.item(0).volume*1000
    assert removed>0
    print(json.dumps(dict(beforeVolume_mm3=before,removedVolume_mm3=removed,afterVolume_mm3=upper.bRepBodies.item(0).volume*1000)))
