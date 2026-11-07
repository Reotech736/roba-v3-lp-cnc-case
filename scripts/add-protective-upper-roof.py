"""Fusion MCP: protect the left PCB with a perforated roof and a removable-cover concept."""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'
NAME='left_case_two_stands_v05_NOT_FOR_MANUFACTURE'

def run(_context: str):
    a=adsk.core.Application.get();doc=next(x for x in a.documents if x.name==NAME)
    assert not doc.isModified and not doc.dataFile.isReadOnly
    doc.activate();d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert d.userParameters.itemByName('roof_lip_thickness') is None,'Roof already present'
    upper=next(c for c in d.allComponents if c.name=='Upper_L_PERIMETER_ONLY_NO_SWITCH_PLATE')
    frame=upper.bRepBodies.item(0)
    for name,value in [('roof_top_global',4.5),('roof_lip_thickness',1.2),('roof_outline_offset',1.8)]:
        d.userParameters.add(name,adsk.core.ValueInput.createByString(str(value)+' mm'),'mm','Provisional upper roof; switch seating/physical fit unverified')
    data=json.load(open(BASE+'cad/design/pcb_v2_layout_input.json',encoding='utf-8'))['boards'][0]
    u=next(f for f in data['footprints'] if f['reference']=='U1');ux,uy=map(float,u['at'][:2])
    def item(e,k):return next(v for v in e if isinstance(v,list) and v[0]==k)
    def xy(v):return [float(v[0])-ux,uy-float(v[1])]
    path=[]
    pending=[dict(start=xy(item(e,'start')[1:3]),end=xy(item(e,'end')[1:3]),mid=xy(item(e,'mid')[1:3]) if e[0]=='gr_arc' else None) for e in data['edges']]
    path.append(pending.pop(0))
    def near(p,q):return math.hypot(p[0]-q[0],p[1]-q[1])<.0001
    while pending:
        i=next(i for i,e in enumerate(pending) if near(path[-1]['end'],e['start']) or near(path[-1]['end'],e['end']))
        e=pending.pop(i)
        if not near(path[-1]['end'],e['start']):e['start'],e['end']=e['end'],e['start']
        path.append(e)
    vertices=[]
    for e in path:
        vertices.append(e['start'])
        if e['mid']:vertices.append(e['mid'])
    if sum(p[0]*q[1]-p[1]*q[0] for p,q in zip(vertices,vertices[1:]+vertices[:1]))<0:path=[dict(start=e['end'],end=e['start'],mid=e['mid']) for e in reversed(path)]
    def p(x,y):return adsk.core.Point3D.create(x/10,y/10,0)
    def plane(c,expression):
        i=c.constructionPlanes.createInput();assert i.setByOffset(c.xYConstructionPlane,adsk.core.ValueInput.createByString(expression));v=c.constructionPlanes.add(i);v.isLightBulbOn=False;return v
    def profiles(s):
        out=adsk.core.ObjectCollection.create()
        for v in s.profiles:out.add(v)
        return out
    def cut(c,s,target,distance,name):
        i=c.features.extrudeFeatures.createInput(profiles(s),adsk.fusion.FeatureOperations.CutFeatureOperation)
        assert i.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(distance)),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        i.participantBodies=[target];e=c.features.extrudeFeatures.add(i);e.name=name;s.isLightBulbOn=False;return e
    def rect(s,x0,y0,x1,y1):
        for line in s.sketchCurves.sketchLines.addTwoPointRectangle(p(x0,y0),p(x1,y1)):line.isFixed=True
    def rotated_square(s,x,y,size,t):
        h=size/2;points=[(-h,-h),(h,-h),(h,h),(-h,h)]
        points=[(x+math.cos(t)*i-math.sin(t)*j,y+math.sin(t)*i+math.cos(t)*j) for i,j in points]
        for first,last in zip(points,points[1:]+points[:1]):s.sketchCurves.sketchLines.addByTwoPoints(p(*first),p(*last)).isFixed=True
        return points
    def join(c,target,tools,name):
        coll=adsk.core.ObjectCollection.create()
        for b in tools:coll.add(b)
        i=c.features.combineFeatures.createInput(target,coll);i.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation;i.isKeepToolBodies=False
        e=c.features.combineFeatures.add(i);e.name=name;return e
    roof_plane=plane(upper,'roof_top_global - roof_lip_thickness + 1 mm')
    s=upper.sketches.add(roof_plane);s.name='Independent_PCB_outline_plus_roof_margin'
    curves=[];s.isComputeDeferred=True
    for e in path:
        v=s.sketchCurves.sketchArcs.addByThreePoints(p(*e['start']),p(*e['mid']),p(*e['end'])) if e['mid'] else s.sketchCurves.sketchLines.addByTwoPoints(p(*e['start']),p(*e['end']))
        v.isFixed=True;curves.append(v)
    s.isComputeDeferred=False
    oi=s.geometricConstraints.createOffsetInput(curves,adsk.core.ValueInput.createByString('roof_outline_offset'));oi.isTopologyMatched=False
    offset=s.geometricConstraints.addOffset2(oi)
    for v in offset.childCurves:v.isConstruction=False
    for v in curves:v.isConstruction=True
    assert s.profiles.count==1
    # A new body prevents a temporary join with the MCU reference before the opening is cut.
    roof_feature=upper.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString('roof_lip_thickness'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    roof_feature.name='Protective_roof_between_keys_1p2mm_PROVISIONAL';s.isLightBulbOn=False;roof=roof_feature.bodies.item(0)
    keys=[]
    for f in data['footprints']:
        if 'SW_MX' not in f['name']:continue
        pad=next(v for v in f['pads'] if v['drill'] and len(v['drill'])==1 and float(v['drill'][0])==5)
        t=math.radians(float(f['at'][2]) if len(f['at'])>2 else 0);px,py=map(float,pad['at'][:2]);fx,fy=map(float,f['at'][:2])
        keys.append(dict(reference=f['reference'],x=fx+math.cos(t)*px+math.sin(t)*py-ux,y=uy-fy+math.sin(t)*px-math.cos(t)*py,angle=t))
    assert len(keys)==23
    s=upper.sketches.add(roof_plane);s.name='23_switch_openings_14p1_FROM_PUBLIC_CENTERS'
    for k in keys:rotated_square(s,k['x'],k['y'],14.1,k['angle'])
    assert s.profiles.count==23
    before=roof.volume*1000;cut(upper,s,roof,'roof_lip_thickness','Twenty_three_LP_openings_14p1')
    assert abs(before-roof.volume*1000-23*14.1**2*1.2)<.001
    s=upper.sketches.add(roof_plane);s.name='Switch_corner_tool_reliefs_R0p5'
    for k in keys:
        q=14.1/2-.5/math.sqrt(2);t=k['angle']
        for i,j in [(-q,-q),(-q,q),(q,-q),(q,q)]:
            x=k['x']+math.cos(t)*i-math.sin(t)*j;y=k['y']+math.sin(t)*i+math.cos(t)*j
            s.sketchCurves.sketchCircles.addByCenterRadius(p(x,y),.05).isFixed=True
    assert s.profiles.count==92
    before=roof.volume*1000;cut(upper,s,roof,'roof_lip_thickness','Ninety_two_corner_reliefs_R0p5')
    assert abs(before-roof.volume*1000-23*(2*math.pi-4)*.5**2*1.2)<.001
    s=upper.sketches.add(roof_plane);rect(s,-9.5,-21.1,9.5,2.6)
    cut(upper,s,roof,'roof_lip_thickness','Controller_opening_for_separate_nonmetal_cover')
    join(upper,frame,[roof],'Join_perforated_roof_to_perimeter_only')
    upper.name='Upper_L_PROTECTIVE_ROOF_23_LP_OPENINGS_PROVISIONAL'
    # Controller opening already clears the roof above the existing USB notch.
    # Nonmetal concept cover: low sidewalls; raised back-wall lower edge clears the MCU.
    m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,0,.45)
    cap=root.occurrences.addNewComponent(m).component;cap.name='MCU_NONMETAL_COVER_CONCEPT_RETENTION_PENDING'
    cp=plane(cap,'3 mm');s=cap.sketches.add(cp);rect(s,-9.9,-20.95,9.9,3)
    e=cap.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString('1.2 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation);s.isLightBulbOn=False;lid=e.bodies.item(0)
    for xy,z,h in [([-9.9,-20.95,-9.1,3],0,3),([9.1,-20.95,9.9,3],0,3),([-9.9,2.2,9.9,3],0,3),([-9.9,-20.95,9.9,-20.15],.7,2.3)]:
        cp=plane(cap,str(z)+' mm');s=cap.sketches.add(cp);rect(s,*xy)
        e=cap.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString(str(h)+' mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation);s.isLightBulbOn=False
    join(cap,lid,[b for b in cap.bRepBodies if b!=lid],'Join_nonmetal_cover_roof_and_skirts')
    s=cap.sketches.add(cap.xYConstructionPlane);rect(s,-6,1.5,6,4)
    cut(cap,s,cap.bRepBodies.item(0),'3 mm','Open_front_for_USB_cable')
    # Max-size switch housings. Latches and caps are deliberately not claimed as modeled.
    sw=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component;sw.name='SWITCH_MAX_HOUSING_14mm_ENVELOPES_NOT_LATCHES'
    sp=plane(sw,'1.6 mm');s=sw.sketches.add(sp)
    for k in keys:rotated_square(s,k['x'],k['y'],14,k['angle'])
    assert s.profiles.count==23
    sw.features.extrudeFeatures.addSimple(profiles(s),adsk.core.ValueInput.createByString('2.9 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation);s.isLightBulbOn=False
    assert sw.bRepBodies.count==23
    # SAT checks lateral keycap allowance (18.1 mm + 0.35 mm per side) vs cover.
    cover=[(-9.9,-20.95),(9.9,-20.95),(9.9,3),(-9.9,3)]
    def separated(poly,other):
        for shape in (poly,other):
            for p0,p1 in zip(shape,shape[1:]+shape[:1]):
                ax,ay=-(p1[1]-p0[1]),p1[0]-p0[0]
                one=[x*ax+y*ay for x,y in poly];two=[x*ax+y*ay for x,y in other]
                if max(one)<min(two) or max(two)<min(one):return True
        return False
    for k in keys:
        q=18.8/2;t=k['angle'];poly=[(k['x']+math.cos(t)*x-math.sin(t)*y,k['y']+math.sin(t)*x+math.cos(t)*y) for x,y in [(-q,-q),(q,-q),(q,q),(-q,q)]]
        assert separated(poly,cover),'Cover overlaps expanded keycap footprint '+k['reference']
    assert upper.bRepBodies.count==1 and cap.bRepBodies.count==1
    entities=adsk.core.ObjectCollection.create()
    for o in root.occurrences:entities.add(o)
    ii=d.createInterferenceInput(entities);ii.areCoincidentFacesIncluded=False;rr=d.analyzeInterference(ii)
    assert rr.count==0,'Interference: '+str([rr.item(i).interferenceBody.volume*1000 for i in range(rr.count)])
    # The cable access reservation overlaps the USB connector intentionally,
    # so test it only against the protective upper and the removable cover.
    m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,0,.1)
    access_occ=root.occurrences.addNewComponent(m);access=access_occ.component;access.name='USB_CABLE_ACCESS_ASSUMED_NOT_A_PART'
    s=access.sketches.add(access.xYConstructionPlane);rect(s,-6,0,6,18)
    e=access.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString('6 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation);s.isLightBulbOn=False
    access_entities=adsk.core.ObjectCollection.create();access_entities.add(access_occ)
    for o in root.occurrences:
        if o.component==upper or o.component==cap:access_entities.add(o)
    ai=d.createInterferenceInput(access_entities);ai.areCoincidentFacesIncluded=False;access_results=d.analyzeInterference(ai)
    assert access_results.count==0,'USB cable access blocked'
    access_occ.isLightBulbOn=False
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    assert doc.save('Add protective roof, 23 LP openings, separate nonmetal MCU cover and switch housing envelopes; fit remains provisional.')
    ex=d.exportManager;assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/'+NAME+'.f3d'))
    for c,label in [(upper,'Upper_L_protective_roof'),(cap,'MCU_cover_concept')]:assert ex.execute(ex.createSTEPExportOptions(BASE+'cad/design/'+NAME+'_'+label+'_LOCAL.step',c))
    report=dict(name=NAME,date='2026-11-07',id=doc.dataFile.id,roofTopZ_mm=4.5,roofThickness_mm=1.2,opening_mm=14.1,cornerReliefR_mm=.5,switchCount=23,controllerOpeningXY_mm=[[-9.5,-21.1],[9.5,2.6]],coverBounds_mm=[[-9.9,-20.95,4.5],[9.9,3,8.7]],keycapSource='https://shop.tai-hao.com/products/black',keycapNominal_mm=[18.1,18.1,3.94],keycapLateralAllowancePerSide_mm=.35,keycapFootprintChecks=23,solidInterferences=rr.count,cableAccessInterferences=access_results.count,timelineIssues=issues,limitations=['Roof Z and thickness are provisional; actual latch retention/PCB seating and cap mounting depth unverified.','Switch bodies are 14 mm box envelopes, not full switch/latch CAD.','Keycaps checked only in XY against controller cover; vertical pressed/released motion and extraction not modeled.','Cover is a nonmetal concept with retention pending; back lower edge raised to clear MCU.','No RF validation, cover seal, material/process choice or final DFM approval.','Stand opening sweep/finger access and PCB-edge trace clearance still pending.'])
    with open(BASE+'cad/design/upper-roof-development.json','w',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    a.activeViewport.fit();print(json.dumps(report))
