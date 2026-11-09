"""One-time follow-up to unsaved v25 bracket development: join backing, recut,
reinforce the web, and open screw-head/driver seats before final verification.
"""
import adsk.core,adsk.fusion,json
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')


def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber==25 and doc.isModified
    lower=next(o.component for o in root.occurrences if o.component.name.startswith('Lower_L_'))
    bracket=next(o.component for o in root.allOccurrences if o.component.name.startswith('WIRE_STRAIN_RELIEF_CASE_BRACKET_'))
    assert lower.bRepBodies.count==2 and bracket.bRepBodies.count==1
    def point(x,y):return adsk.core.Point3D.create(x/10,y/10,0)
    def plane(c,z):
        i=c.constructionPlanes.createInput();i.setByOffset(c.xYConstructionPlane,adsk.core.ValueInput.createByString(f'{z} mm'));p=c.constructionPlanes.add(i);p.isLightBulbOn=False;return p
    def join(c,target,tools,name):
        coll=adsk.core.ObjectCollection.create()
        for b in tools:coll.add(b)
        i=c.features.combineFeatures.createInput(target,coll);i.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation
        c.features.combineFeatures.add(i).name=name
    def cut(c,s,h,name):
        ps=adsk.core.ObjectCollection.create()
        for p in s.profiles:ps.add(p)
        i=c.features.extrudeFeatures.createInput(ps,adsk.fusion.FeatureOperations.CutFeatureOperation)
        i.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(f'{h} mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection);i.participantBodies=[c.bRepBodies.item(0)]
        c.features.extrudeFeatures.add(i).name=name;s.isLightBulbOn=False
    join(lower,lower.bRepBodies.item(0),[lower.bRepBodies.item(1)],'Explicitly_join_wire_bracket_backing_to_lower_SINGLE_SOLID')
    assert lower.bRepBodies.count==1
    s=lower.sketches.add(plane(lower,6.3))
    for line in s.sketchCurves.sketchLines.addTwoPointRectangle(point(10.7,-27.2),point(14.9,-18.6)):line.isFixed=True
    cut(lower,s,4.2,'Recut_wire_bracket_relief_after_backing_join_0p3_clearance')
    # Add an inboard web before opening both D3.4 head/compact-driver seats.
    s=bracket.sketches.add(plane(bracket,-4.9))
    for line in s.sketchCurves.sketchLines.addTwoPointRectangle(point(10.3,-24),point(11.1,-20)):line.isFixed=True
    original=bracket.bRepBodies.item(0)
    e=bracket.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString('3.9 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation);e.name='Inboard_web_reinforcement_before_head_seat_relief';s.isLightBulbOn=False
    join(bracket,original,[b for b in bracket.bRepBodies if b!=original],'Join_inboard_web_to_nonmetal_bracket')
    s=bracket.sketches.add(plane(bracket,-5.1))
    for y in [-25,-21.5]:s.sketchCurves.sketchCircles.addByCenterRadius(point(12.8,y),.17).isFixed=True
    cut(bracket,s,2.9,'D3p4_open_head_and_driver_seats_to_underhead_Zminus2p2')
    assert d.computeAll()
    assert lower.bRepBodies.count==bracket.bRepBodies.count==1
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues
    p=BASE/'docs/case-wire-bracket-development.json';r=json.loads(p.read_text(encoding='utf-8'))
    r.update(backingExplicitlyJoined=True,lowerSingleSolid=True,headSeatsDiameter_mm=3.4,
             inboardWebAddedGlobal_mm=[10.3,-24,-4.9,11.1,-20,-1],
             bracketVolume_mm3=bracket.bRepBodies.item(0).volume*1000,timelineIssues=issues,
             correction='Initial backing remained a second body and was omitted from the first relief; explicitly join and re-cut. Add inboard web and D3.4 head seats to avoid screw-head contact.')
    r['caseVolumesAfter_mm3'][lower.name]=lower.bRepBodies.item(0).volume*1000
    p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'lowerBodies':1,'bracketBodies':1,'lowerVolume_mm3':lower.bRepBodies.item(0).volume*1000,'bracketVolume_mm3':r['bracketVolume_mm3'],'timelineIssues':issues}))
