"""Fusion MCP: nominal LP seating revision and raised-skirt MCU cover candidate.

Runs once on the unmodified cloud-v6 working file. Does not save the cloud document;
verification and export are performed separately after inspecting the result.
"""
import adsk.core, adsk.fusion, json, math
BASE = 'C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'
NAME = 'left_case_two_stands_v05_NOT_FOR_MANUFACTURE'


def run(_context: str):
    a=adsk.core.Application.get(); doc=a.activeDocument
    assert doc.name==NAME and not doc.isModified and not doc.dataFile.isReadOnly
    assert doc.dataFile.versionNumber==6
    d=adsk.fusion.Design.cast(a.activeProduct); root=d.rootComponent
    assert d.userParameters.itemByName('lp_flange_nominal_z') is None
    ex=d.exportManager
    assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/checkpoints/v05_cloud_v6_before_lp_seating.f3d'))
    initial={c.name:sum(b.volume*1000 for b in c.bRepBodies) for c in d.allComponents}
    for name,value in [('lp_flange_nominal_z',3.8),('cover_half_width',9.3),('cover_rear_y',-20.35),('cover_front_y',2.4),('cover_skirt_bottom_z',5.2)]:
        d.userParameters.add(name,adsk.core.ValueInput.createByString(str(value)+' mm'),'mm','Nominal comparison; retention and physical tolerances unverified')
    d.userParameters.itemByName('roof_top_global').expression='lp_flange_nominal_z'
    sw=next(c for c in d.allComponents if c.name=='SWITCH_MAX_HOUSING_14mm_ENVELOPES_NOT_LATCHES')
    h=next(p for p in sw.modelParameters if p.role=='AlongDistance' and p.createdBy.objectType==adsk.fusion.ExtrudeFeature.classType())
    h.expression='lp_flange_nominal_z - 1.6 mm'
    sw.name='SWITCH_LOWER_14mm_PCB_SEATED_ENVELOPES_NOT_LATCHES'
    old=next(o for o in root.occurrences if o.component.name=='MCU_NONMETAL_COVER_CONCEPT_RETENTION_PENDING')
    root.features.removeFeatures.add(old).name='Retire_initial_low_skirt_cover_after_checkpoint'

    def p(x,y): return adsk.core.Point3D.create(x/10,y/10,0)
    def rect(s,x0,y0,x1,y1):
        for v in s.sketchCurves.sketchLines.addTwoPointRectangle(p(x0,y0),p(x1,y1)): v.isFixed=True
    def plane(c,expr):
        i=c.constructionPlanes.createInput(); assert i.setByOffset(c.xYConstructionPlane,adsk.core.ValueInput.createByString(expr))
        z=c.constructionPlanes.add(i); z.isLightBulbOn=False; return z
    def profiles(s):
        v=adsk.core.ObjectCollection.create()
        for x in s.profiles:v.add(x)
        return v
    def extrude(c,s,expr,name):
        v=c.features.extrudeFeatures.addSimple(profiles(s),adsk.core.ValueInput.createByString(expr),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        v.name=name;s.isLightBulbOn=False;return v
    def cut(c,s,target,expr,name):
        i=c.features.extrudeFeatures.createInput(profiles(s),adsk.fusion.FeatureOperations.CutFeatureOperation)
        assert i.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(expr)),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        i.participantBodies=[target];v=c.features.extrudeFeatures.add(i);v.name=name;s.isLightBulbOn=False

    # Component coordinates are global here, avoiding a hidden cover offset.
    cap=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    cap.name='MCU_RAISED_SKIRT_COVER_18p6_WIDE_RETENTION_PENDING'
    s=cap.sketches.add(plane(cap,'7.5 mm')); rect(s,-9.3,-20.35,9.3,2.4)
    lid=extrude(cap,s,'1.2 mm','Cover_roof_1p2mm').bodies.item(0)
    for coords in [(-9.3,-20.35,-8.5,2.4),(8.5,-20.35,9.3,2.4),(-9.3,-20.35,9.3,-19.55),(-9.3,1.6,9.3,2.4)]:
        s=cap.sketches.add(plane(cap,'cover_skirt_bottom_z'));rect(s,*coords)
        extrude(cap,s,'7.5 mm - cover_skirt_bottom_z','Raised_skirt_clears_MCU_main_block')
    tools=adsk.core.ObjectCollection.create()
    for b in cap.bRepBodies:
        if b!=lid:tools.add(b)
    i=cap.features.combineFeatures.createInput(lid,tools);i.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation
    cap.features.combineFeatures.add(i).name='Join_raised_skirts_and_roof'
    s=cap.sketches.add(plane(cap,'cover_skirt_bottom_z'));rect(s,-6,1.5,6,3)
    cut(cap,s,cap.bRepBodies.item(0),'7.5 mm - cover_skirt_bottom_z','USB_front_access_12mm')

    # Full square is a conservative upper housing/flange clearance envelope, not switch CAD.
    data=json.load(open(BASE+'cad/design/pcb_v2_layout_input.json',encoding='utf-8'))['boards'][0]
    u=next(f for f in data['footprints'] if f['reference']=='U1');ux,uy=map(float,u['at'][:2]);keys=[]
    for f in data['footprints']:
        if 'SW_MX' not in f['name']:continue
        pad=next(v for v in f['pads'] if v['drill'] and len(v['drill'])==1 and float(v['drill'][0])==5)
        t=math.radians(float(f['at'][2]) if len(f['at'])>2 else 0);px,py=map(float,pad['at'][:2]);fx,fy=map(float,f['at'][:2])
        keys.append(dict(reference=f['reference'],x=fx+math.cos(t)*px+math.sin(t)*py-ux,y=uy-fy+math.sin(t)*px-math.cos(t)*py,angle=t))
    flange=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    flange.name='SWITCH_UPPER_15p2_SQUARE_CONSERVATIVE_ENVELOPES_NOT_FULL_SWITCHES'
    s=flange.sketches.add(plane(flange,'lp_flange_nominal_z'))
    for k in keys:
        points=[(k['x']+math.cos(k['angle'])*x-math.sin(k['angle'])*y,k['y']+math.sin(k['angle'])*x+math.cos(k['angle'])*y) for x,y in [(-7.6,-7.6),(7.6,-7.6),(7.6,7.6),(-7.6,7.6)]]
        for first,last in zip(points,points[1:]+points[:1]):s.sketchCurves.sketchLines.addByTwoPoints(p(*first),p(*last)).isFixed=True
    assert s.profiles.count==23
    extrude(flange,s,'3.5 mm','Max_square_upper_housing_from_nominal_flange_plane')
    assert flange.bRepBodies.count==23
    for b,k in zip(flange.bRepBodies,keys):b.name='Upper_housing_clearance_'+k['reference']
    d.computeAll()
    upper=next(c for c in d.allComponents if c.name.startswith('Upper_L_PROTECTIVE'))
    assert upper.bRepBodies.count==1 and cap.bRepBodies.count==1
    lower=next(c for c in d.allComponents if c.name.startswith('Lower_L_'))
    assert abs(lower.bRepBodies.item(0).volume*1000-initial[lower.name])<.0001
    # Evaluate all solid components except the deliberately overlapping cable access tool.
    entities=adsk.core.ObjectCollection.create()
    for o in root.occurrences:
        if o.component.name!='USB_CABLE_ACCESS_ASSUMED_NOT_A_PART':entities.add(o)
    ii=d.createInterferenceInput(entities);ii.areCoincidentFacesIncluded=False;results=d.analyzeInterference(ii)
    collisions=[dict(first=r.entityOne.name,second=r.entityTwo.name,volume_mm3=r.interferenceBody.volume*1000) for r in results]
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage]
    out=dict(date='2026-11-08',checkpointCloudVersion=6,roofTopZ_mm=3.8,roofThickness_mm=1.2,
             coverBounds_mm=[[-9.3,-20.35,5.2],[9.3,2.4,8.7]],coverSkirtBottomZ_mm=5.2,
             lowerVolumeUnchanged=True,interferences=collisions,timelineIssues=issues,keys=keys,
             limitations=['Nominal seating, physical fit not proven','Upper switch squares overestimate tapered shape; pins, latches, stems and sockets omitted','Cover retention and lower skirt gaps unresolved'])
    with open(BASE+'docs/lp-seating-revision-verification.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False))
