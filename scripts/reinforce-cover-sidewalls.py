"""Fusion MCP: increase nonmetal rear/side walls to 1.2 mm within existing outline."""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'


def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    c=next(o.component for o in root.occurrences if o.component.name.startswith('MCU_RAISED_'))
    assert not any(f.name=='Cover_side_and_rear_walls_1p2_PROVISIONAL' for f in c.features.combineFeatures)
    before=c.bRepBodies.item(0).volume*1000;target=c.bRepBodies.item(0);tools=adsk.core.ObjectCollection.create()
    for rect in [(-8.5,-19.55,-8.1,1.6),(8.1,-19.55,8.5,1.6),(-8.5,-19.55,8.5,-19.15)]:
        i=c.constructionPlanes.createInput();i.setByOffset(c.xYConstructionPlane,adsk.core.ValueInput.createByString('5.2 mm'))
        pl=c.constructionPlanes.add(i);pl.isLightBulbOn=False;s=c.sketches.add(pl)
        def p(x,y):return adsk.core.Point3D.create(x/10,y/10,0)
        for edge in s.sketchCurves.sketchLines.addTwoPointRectangle(p(*rect[:2]),p(*rect[2:])):edge.isFixed=True
        e=c.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString('2.3 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        e.name='Inside_wall_thickening_above_MCU_main_block';s.isLightBulbOn=False;tools.add(e.bodies.item(0))
    i=c.features.combineFeatures.createInput(target,tools);i.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation
    c.features.combineFeatures.add(i).name='Cover_side_and_rear_walls_1p2_PROVISIONAL'
    assert d.computeAll();assert c.bRepBodies.count==1
    assert abs(c.bRepBodies.item(0).volume*1000-before-53.82)<.001
    def section_I(wall):
        width=18.6;roof=1.2;h=2.3
        a0=width*roof;a1=2*wall*h;z0=h+roof/2;z1=h/2
        zbar=(a0*z0+a1*z1)/(a0+a1)
        return width*roof**3/12+a0*(z0-zbar)**2+2*wall*h**3/12+a1*(z1-zbar)**2
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    out=dict(date='2026-11-08',previousSideWall_mm=.8,newSideWall_mm=1.2,newRearWall_mm=1.2,
             frontWall_mm=.8,skirtBottomGlobalZ_mm=5.2,coarseMCUMainBlockClearanceZ_mm=.33,externalOutlineUnchanged=True,
             volumes_mm3=[before,c.bRepBodies.item(0).volume*1000],addedVolume_mm3=53.82,
             idealUSectionI_mm4=dict(previous=section_I(.8),revised=section_I(1.2),ratio=section_I(1.2)/section_I(.8)),
             timelineIssues=issues,limitations=['Section comparison only; openings, screw feet, joint flexibility, torsion, material modulus and creep excluded',
             'Not FEA or a prediction of actual cover deflection; rear is still a front-fastened overhang',
             'Polymer material/process and RF performance remain unselected/unverified'])
    json.dump(out,open(BASE+'docs/cover-sidewall-reinforcement-verification.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False))
