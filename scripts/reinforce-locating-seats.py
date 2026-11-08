"""Fusion MCP: round/capsule local seats retain nominal 1 mm radial wall around pockets."""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'


def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    lower=next(o.component for o in root.occurrences if o.component.name.startswith('Lower_L_'))
    upper=next(o.component for o in root.occurrences if o.component.name.startswith('Upper_L_'))
    assert not any(f.name=='Locator_seat_reinforcement_min_radial_wall_1mm' for f in upper.features.combineFeatures)
    axes=[(-107.12,-72),(-107.12,-8)]
    def p(x,y):return adsk.core.Point3D.create(x/10,y/10,0)
    def profile(c,z,r):
        i=c.constructionPlanes.createInput();i.setByOffset(c.xYConstructionPlane,adsk.core.ValueInput.createByString(str(z)+' mm'))
        pl=c.constructionPlanes.add(i);pl.isLightBulbOn=False;s=c.sketches.add(pl)
        s.sketchCurves.sketchCircles.addByCenterRadius(p(*axes[0]),r/10).isFixed=True
        x,y=axes[1];e=.3
        s.sketchCurves.sketchLines.addByTwoPoints(p(x-r,y-e),p(x-r,y+e)).isFixed=True
        s.sketchCurves.sketchArcs.addByThreePoints(p(x-r,y+e),p(x,y+e+r),p(x+r,y+e)).isFixed=True
        s.sketchCurves.sketchLines.addByTwoPoints(p(x+r,y+e),p(x+r,y-e)).isFixed=True
        s.sketchCurves.sketchArcs.addByThreePoints(p(x+r,y-e),p(x,y-e-r),p(x-r,y-e)).isFixed=True
        coll=adsk.core.ObjectCollection.create()
        for pr in s.profiles:coll.add(pr)
        assert coll.count==2
        return s,coll
    for c,z,height in [(lower,9.5,1),(upper,0,2.5)]:
        target=c.bRepBodies.item(0);s,pr=profile(c,z,2)
        e=c.features.extrudeFeatures.addSimple(pr,adsk.core.ValueInput.createByString(str(height)+' mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        e.name='Round_and_slot_locator_seat_material';s.isLightBulbOn=False
        tools=adsk.core.ObjectCollection.create()
        for b in e.bodies:tools.add(b)
        i=c.features.combineFeatures.createInput(target,tools);i.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation
        c.features.combineFeatures.add(i).name='Locator_seat_reinforcement_min_radial_wall_1mm'
    # Restore the locating cavities after adding material, using exactly the original profiles.
    s,pr=profile(upper,0,1)
    i=upper.features.extrudeFeatures.createInput(pr,adsk.fusion.FeatureOperations.CutFeatureOperation)
    i.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('case_locator_socket_depth')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
    i.participantBodies=[upper.bRepBodies.item(0)]
    upper.features.extrudeFeatures.add(i).name='Restore_round_and_slot_cavities_after_reinforcement';s.isLightBulbOn=False
    assert d.computeAll()
    for c in [upper,lower]:assert c.bRepBodies.count==1
    # 24 radial/normal wall rays: cavity ends at R1, material extends to R2.
    inside=adsk.fusion.PointContainment.PointInsidePointContainment;count=0
    for idx,(x,y) in enumerate(axes):
        samples=[(x-1.99,y),(x+1.99,y),(x,y-(2.29 if idx else 1.99)),(x,y+(2.29 if idx else 1.99))]
        for xx,yy in samples:
            assert upper.bRepBodies.item(0).pointContainment(adsk.core.Point3D.create(xx/10,yy/10,.06))==inside
            count+=1
        assert upper.bRepBodies.item(0).pointContainment(adsk.core.Point3D.create(x/10,y/10,.06))!=inside
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    path=BASE+'docs/service-and-locating-development.json';r=json.load(open(path,encoding='utf-8'))
    r.update(locatorReinforcement=dict(roundOuterDiameter_mm=4,slotOuterXY_mm=[4,4.6],nominalRadialWall_mm=1,upperGlobalZ_mm=[-1,1.5],lowerGlobalZ_mm=[-2,-1],wallMaterialSamples=count),
             finalVolumes_mm3={c.name:c.bRepBodies.item(0).volume*1000 for c in [lower,upper]})
    r['limitations'][0]='Locator dimensions and local reinforcing pads remain provisional; tolerances, exterior steps and tool access need DFM review'
    json.dump(r,open(path,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(dict(reinforcement=r['locatorReinforcement'],timelineIssues=issues)))
