"""Fusion MCP: independent left tray and mating perimeter frame from public PCB outline."""
import adsk.core, adsk.fusion, json, math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'
NAME='left_case_structure_v01_NOT_FOR_MANUFACTURE'

def build(_context: str, name=NAME, two_stands=False):
    NAME=name
    a=adsk.core.Application.get()
    project=next(p for p in a.data.dataProjects if p.name=='roba-v3-lp-cnc-case')
    folder=next(f for f in project.rootFolder.dataFolders if f.name=='02_design')
    assert not any(f.name==NAME for f in folder.dataFiles),'Prototype already exists'
    data=json.load(open(BASE+'cad/design/pcb_v2_layout_input.json',encoding='utf-8'))['boards'][0]
    u=next(f for f in data['footprints'] if f['reference']=='U1');ux,uy=map(float,u['at'][:2])
    def child(e,k):return next(v for v in e if isinstance(v,list) and v[0]==k)
    def local(v):return [float(v[0])-ux,uy-float(v[1])]
    pending=[]
    for e in data['edges']:
        pending.append(dict(start=local(child(e,'start')[1:3]),end=local(child(e,'end')[1:3]),mid=local(child(e,'mid')[1:3]) if e[0]=='gr_arc' else None))
    path=[pending.pop(0)]
    def near(p,q):return math.hypot(p[0]-q[0],p[1]-q[1])<.0001
    while pending:
        i=next(i for i,e in enumerate(pending) if near(path[-1]['end'],e['start']) or near(path[-1]['end'],e['end']))
        e=pending.pop(i)
        if not near(path[-1]['end'],e['start']):e['start'],e['end']=e['end'],e['start']
        path.append(e)
    assert near(path[-1]['end'],path[0]['start'])
    vertices=[]
    for e in path:
        vertices.append(e['start'])
        if e['mid']:vertices.append(e['mid'])
    area=sum(p[0]*q[1]-p[1]*q[0] for p,q in zip(vertices,vertices[1:]+vertices[:1]))/2
    if area<0:path=[dict(start=e['end'],end=e['start'],mid=e['mid']) for e in reversed(path)]
    doc=a.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    d=adsk.fusion.Design.cast(a.activeProduct);d.designType=adsk.fusion.DesignTypes.ParametricDesignType
    for name,value in [('outside_offset',4),('PCB_side_clearance',1),('floor_thickness',2),('lower_wall_height',8.5),('upper_frame_height',5.5),('stand_depth',3.7),('stand_residual',2),('support_height',3.3),('M2_clearance',2.2),('M2_tap_pilot',1.6),('M2_pilot_depth',4),('boss_diameter',6)]:
        d.userParameters.add(name,adsk.core.ValueInput.createByString(str(value)+' mm'),'mm','Provisional study, actual hardware/fit not verified')
    root=d.rootComponent
    def point(p):return adsk.core.Point3D.create(p[0]/10,p[1]/10,0)
    def comp(name,z):
        m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(0,0,z/10)
        o=root.occurrences.addNewComponent(m);o.component.name=name
        return o.component
    def plane(c,expression):
        i=c.constructionPlanes.createInput();assert i.setByOffset(c.xYConstructionPlane,adsk.core.ValueInput.createByString(expression));p=c.constructionPlanes.add(i);p.isLightBulbOn=False;return p
    def outline(c,p):
        s=c.sketches.add(p);s.isComputeDeferred=True;curves=[]
        for e in path:
            v=s.sketchCurves.sketchArcs.addByThreePoints(point(e['start']),point(e['mid']),point(e['end'])) if e['mid'] else s.sketchCurves.sketchLines.addByTwoPoints(point(e['start']),point(e['end']))
            v.isFixed=True;curves.append(v)
        s.isComputeDeferred=False
        return s,curves
    def offset(s,curves,expression):
        i=s.geometricConstraints.createOffsetInput(curves,adsk.core.ValueInput.createByString(expression));i.isTopologyMatched=False
        v=s.geometricConstraints.addOffset2(i)
        for curve in v.childCurves:curve.isConstruction=False
        return v
    def outer_profile(c,p):
        s,curves=outline(c,p);offset(s,curves,'outside_offset')
        for v in curves:v.isConstruction=True
        assert s.profiles.count==1
        return s,s.profiles.item(0)
    def ring_profile(c,p):
        s,curves=outline(c,p);offset(s,curves,'outside_offset');offset(s,curves,'PCB_side_clearance')
        for v in curves:v.isConstruction=True
        rings=[p for p in s.profiles if p.profileLoops.count==2]
        assert len(rings)==1,'Unexpected wall profile topology'
        return s,rings[0]
    NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
    def extrude(c,s,p,expression,operation,name):
        if operation==CUT:
            i=c.features.extrudeFeatures.createInput(p,operation)
            extent=adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(expression))
            assert i.setOneSideExtent(extent,adsk.fusion.ExtentDirections.PositiveExtentDirection)
            i.participantBodies=[c.bRepBodies.item(0)]
            e=c.features.extrudeFeatures.add(i)
        else:e=c.features.extrudeFeatures.addSimple(p,adsk.core.ValueInput.createByString(expression),operation)
        e.name=name;s.isLightBulbOn=False;return e
    def rect(c,p,x0,y0,x1,y1):
        s=c.sketches.add(p)
        for v in s.sketchCurves.sketchLines.addTwoPointRectangle(point([x0,y0]),point([x1,y1])):v.isFixed=True
        return s
    lower=comp('Lower_L_FROM_PCB_OUTLINE_PROVISIONAL',-11.5)
    s,p=outer_profile(lower,lower.xYConstructionPlane)
    floor=extrude(lower,s,p,'floor_thickness',NEW,'Continuous_bottom_floor_2mm')
    bounds=floor.bodies.item(0).boundingBox
    assert abs(bounds.minPoint.x*10-(-104.619997-4))<.001 and abs(bounds.maxPoint.x*10-(19.31946179471142+4))<.001,'Offset did not expand outwards'
    floor_plane=plane(lower,'floor_thickness')
    s,p=ring_profile(lower,floor_plane)
    extrude(lower,s,p,'lower_wall_height',JOIN,'Perimeter_wall_nominal_3mm')
    pockets=[(-50,-71,56.8,14.8),(-50,-24.5,56.8,14.8)] if two_stands else [(-103.3,-65,14.8,56.8)]
    lands=[(-52,-73,8.8,-54.2),(-52,-26.5,8.8,-7.7)] if two_stands else [(-106.62,-67,-86.5,-6.2)]
    for i,b in enumerate(lands):
        s=rect(lower,floor_plane,*b)
        extrude(lower,s,s.profiles.item(0),'stand_depth + stand_residual - floor_thickness',JOIN,'Raised_stand_backing_'+str(i+1))
    for index,(x,y,w,h) in enumerate(pockets):
        s=lower.sketches.add(lower.xYConstructionPlane);r=2.2
        def pp(u,v):return point([x+u,y+v])
        specs=[((r,0),(w-r,0)),((w,r),(w,h-r)),((w-r,h),(r,h)),((0,h-r),(0,r))]
        curves=[s.sketchCurves.sketchLines.addByTwoPoints(pp(*p),pp(*q)) for p,q in specs]
        arcs=[((w-r,0),(w-r+r/math.sqrt(2),r-r/math.sqrt(2)),(w,r)),((w,h-r),(w-r+r/math.sqrt(2),h-r+r/math.sqrt(2)),(w-r,h)),((r,h),(r-r/math.sqrt(2),h-r+r/math.sqrt(2)),(0,h-r)),((0,r),(r-r/math.sqrt(2),r-r/math.sqrt(2)),(r,0))]
        curves.extend(s.sketchCurves.sketchArcs.addByThreePoints(pp(*p),pp(*m),pp(*q)) for p,m,q in arcs)
        for v in curves:v.isFixed=True
        before=lower.bRepBodies.item(0).volume*1000
        extrude(lower,s,s.profiles.item(0),'stand_depth',CUT,'Stand_pocket_'+str(index+1)+'_56p8x14p8_R2p2')
        removed=before-lower.bRepBodies.item(0).volume*1000
        expected_removed=(w*h-(4-math.pi)*r*r)*3.7
        assert abs(removed-expected_removed)<.001,'Pocket incomplete: actual '+str(removed)+' vs expected '+str(expected_removed)
    # Four edge support candidates protrude 0.8 mm beyond the provisional seam.
    support_plane=plane(lower,'8 mm') # global -3.5
    supports=[[-105.42,-61,-103.82,-53],[-105.42,-27,-103.82,-19],[9.276167,-43,11.576167,-37],[-60,6.254,-54,8.554]]
    # Left pads must overlap the wall (inner straight edge is x=-105.619997).
    supports[0][0]=supports[1][0]=-106.12
    for i,b in enumerate(supports):
        s=rect(lower,support_plane,*b)
        extrude(lower,s,s.profiles.item(0),'support_height',JOIN,'PCB_edge_support_'+str(i+1)+'_INSULATION_PENDING')
    axes=[[-108.119997,-59],[-108.119997,-17],[13.576167,-59],[13.576167,-17]]
    def circles(c,p,diameter):
        s=c.sketches.add(p)
        for xy in axes:
            v=s.sketchCurves.sketchCircles.addByCenterRadius(point(xy),diameter/20);v.isFixed=True
        pc=adsk.core.ObjectCollection.create()
        for p in s.profiles:pc.add(p)
        return s,pc
    upper=comp('Upper_L_PERIMETER_ONLY_NO_SWITCH_PLATE',-1)
    s,p=ring_profile(upper,upper.xYConstructionPlane)
    extrude(upper,s,p,'upper_frame_height',NEW,'Provisional_upper_rim_NO_KEYCAP_HEIGHT_CERTIFICATION')
    for c,height in [(lower,'floor_thickness + lower_wall_height'),(upper,'upper_frame_height')]:
        s,p=circles(c,c.xYConstructionPlane,6)
        extrude(c,s,p,height,JOIN,'Four_external_M2_bosses')
    s,p=circles(lower,lower.xYConstructionPlane,2.2)
    extrude(lower,s,p,'floor_thickness + lower_wall_height',CUT,'M2_clearance_holes_NO_HEAD_SEATS')
    s,p=circles(upper,upper.xYConstructionPlane,1.6)
    extrude(upper,s,p,'M2_pilot_depth',CUT,'M2_TAP_PILOTS_ONLY_THREAD_NOT_MODELED')
    for i,(x0,y0,x1,y1) in enumerate(supports):
        s=rect(upper,upper.xYConstructionPlane,x0-.2,y0-.2,x1+.2,y1+.2)
        extrude(upper,s,s.profiles.item(0),'1 mm',CUT,'Support_clearance_'+str(i+1)+'_0p2mm')
    pcb=comp('PCB_L_v2_OUTLINE_REFERENCE_ACTUAL_REVISION_UNKNOWN',0)
    s,curves=outline(pcb,pcb.xYConstructionPlane)
    for f in data['footprints']:
        if 'MountingHole' in f['name']:
            circle=s.sketchCurves.sketchCircles.addByCenterRadius(point(local(f['at'][:2])),float(f['pads'][0]['drill'][0])/20);circle.isFixed=True
    extrude(pcb,s,max(s.profiles,key=lambda p:p.areaProperties().area),'1.6 mm',NEW,'Public_PCB_reference_NOT_populated')
    assert lower.bRepBodies.count==1 and upper.bRepBodies.count==1
    assert abs(lower.bRepBodies.item(0).boundingBox.maxPoint.z*10-11.3)<.001,'PCB support tops were altered by another component cut'
    entities=adsk.core.ObjectCollection.create()
    for o in root.occurrences:entities.add(o)
    interference_input=d.createInterferenceInput(entities);interference_input.areCoincidentFacesIncluded=False
    interference=d.analyzeInterference(interference_input)
    assert interference.count==0,'Prototype solid interference remains'
    # Local tray z=0 is global -11.5. Verify the actual solid, not just bounds.
    body=lower.bRepBodies.item(0)
    INSIDE=adsk.fusion.PointContainment.PointInsidePointContainment
    checks=[]
    locations=[('battery_floor',-50,-40,1,True),('battery_cavity',-50,-40,3,False)]
    for index,(x,y,w,h) in enumerate(pockets):
        locations.extend([(str(index)+'_stand_void',x+w/2,y+h/2,2,False),(str(index)+'_stand_residual',x+w/2,y+h/2,4.7,True),(str(index)+'_stand_above',x+w/2,y+h/2,6,False)])
    for label,x,y,z,expected in locations:
        actual=body.pointContainment(adsk.core.Point3D.create(x/10,y/10,z/10))==INSIDE
        assert actual==expected,label
        checks.append(dict(label=label,inside=actual))
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage]
    assert not issues,str(issues)
    assert doc.saveAs(NAME,folder,'Independent left lower tray, upper perimeter frame, M2 pilot candidates, PCB supports and stand recess. Not for manufacture.','')
    ex=d.exportManager
    assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/'+NAME+'.f3d'))
    for c,label in [(lower,'Lower_L'),(upper,'Upper_L_perimeter_only')]:
        assert ex.execute(ex.createSTEPExportOptions(BASE+'cad/design/'+NAME+'_'+label+'_LOCAL.step',c))
    bodies=[]
    for o in root.occurrences:
        b=o.bRepBodies.item(0);bb=b.boundingBox
        bodies.append(dict(component=o.component.name,min_mm=[round(v*10,6) for v in bb.minPoint.asArray()],max_mm=[round(v*10,6) for v in bb.maxPoint.asArray()],volume_mm3=round(b.volume*1000,5)))
    report=dict(name=NAME,id=None,date='2026-11-07',standPocketsXYWH_mm=pockets,standBackingXYXY_mm=lands,coordinateSystem='Each U1 XY origin; PCB underside global z=0. Lower component z=-11.5, upper=-1. STEP files are component local.',screwAxesXY_mm=axes,edgeSupportsXY_mm=supports,pointChecks=checks,bodies=bodies,prototypeSolidInterferences=interference.count,timelineIssues=issues,limitations=['Upper component is a perimeter frame, not a finished keyboard top.','M2 pilots are geometry only; no thread callout, head seats, locating step or final screw selection.','Edge supports require trace/pad clearance and insulating interface verification.','No USB, reset, power switch, antenna window or battery retention detail.','No stand finger access or actual opening sweep yet.','Remaining small internal radii, floor-wall corners, finishing and tool reach require machining review.','Real LP PCB, keycaps and all populated components not validated. Right case not created.'])
    with open(BASE+'cad/design/'+NAME+'.json','w',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    a.activeViewport.fit();print(json.dumps(report))
    return report

def run(_context: str):
    return build(_context)
