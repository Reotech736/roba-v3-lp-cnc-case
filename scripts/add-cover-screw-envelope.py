"""Fusion MCP: verify provisional screw head/shank envelopes, not thread solids."""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'


def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    name='COVER_M1p6x6_SCREW_ENVELOPES_HEAD_ASSUMED_THREAD_NOT_MODELED'
    assert not any(o.component.name==name for o in root.occurrences)
    occ=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());c=occ.component;c.name=name
    def circle(x,y,z,r):
        i=c.constructionPlanes.createInput();i.setByOffset(c.xYConstructionPlane,adsk.core.ValueInput.createByString(str(z)+' mm'))
        pl=c.constructionPlanes.add(i);pl.isLightBulbOn=False;s=c.sketches.add(pl)
        s.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(x/10,y/10,0),r/10).isFixed=True
        return s
    for x in [-8,8]:
        s=circle(x,3.8,2,.8)
        shaft=c.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString('6 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation).bodies.item(0);s.isLightBulbOn=False
        s=circle(x,3.8,8,1.6)
        head=c.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString('1.6 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation).bodies.item(0);s.isLightBulbOn=False
        tools=adsk.core.ObjectCollection.create();tools.add(head)
        i=c.features.combineFeatures.createInput(shaft,tools);i.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation
        c.features.combineFeatures.add(i)
    assert c.bRepBodies.count==2
    def check(prefixes):
        ent=adsk.core.ObjectCollection.create();ent.add(occ)
        for o in root.occurrences:
            if o.component.name.startswith(prefixes):ent.add(o)
        i=d.createInterferenceInput(ent);i.areCoincidentFacesIncluded=False;rr=d.analyzeInterference(i)
        return [dict(first=r.entityOne.parentComponent.name,second=r.entityTwo.parentComponent.name,volume_mm3=r.interferenceBody.volume*1000) for r in rr]
    hits=check(('MCU_RAISED_','Lower_L_','Battery_L_','PCB_L_','XIAO_KEY_SIDE_','KEYCAP_SWEEP_','USB_CABLE_'))
    # Access tool intersects the PCB and MCU by definition, so isolate screw-involving pairs.
    screw_hits=[h for h in hits if name in [h['first'],h['second']]]
    assert not screw_hits,str(screw_hits)
    upper_hits=check(('Upper_L_',))
    assert len(upper_hits)==2 # Major-diameter cylinders overlap pilot holes intentionally.
    occ.isLightBulbOn=False
    out=dict(date='2026-11-08',screwCount=2,screw='M1.6x6 nominal envelope',headAssumedDiameter_mm=3.2,headAssumedHeight_mm=1.6,
             headSeatZ_mm=8,tipZ_mm=2,nominalProjectionIntoUpper_mm=2.5,nominalPilotBottomGap_mm=.7,
             casingAndSweepInterferences=screw_hits,expectedThreadPilotOverlap=upper_hits,
             limitations=['Nominal major-diameter cylinder is not a modeled thread','Head standard and actual screw supply still unconfirmed','Preload, resin creep, rear cantilever stiffness and physical fit remain unverified'])
    json.dump(out,open(BASE+'docs/cover-screw-envelope-verification.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False))
