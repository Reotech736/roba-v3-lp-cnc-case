"""Fusion MCP: update editable v05 in place; preserve all source/old documents."""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'
NAME='left_case_two_stands_v05_NOT_FOR_MANUFACTURE'

def run(_context: str):
    a=adsk.core.Application.get();doc=next(x for x in a.documents if x.name==NAME)
    assert not doc.isModified and not doc.dataFile.isReadOnly
    doc.activate();d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert d.userParameters.itemByName('head_seat_depth') is None,'Development already applied'
    lower=next(c for c in d.allComponents if c.name=='Lower_L_FROM_PCB_OUTLINE_PROVISIONAL')
    upper=next(c for c in d.allComponents if c.name=='Upper_L_PERIMETER_ONLY_NO_SWITCH_PLATE')
    source=json.load(open(BASE+'cad/design/'+NAME+'.json',encoding='utf-8'))
    def rectangle(c,plane,xy):
        s=c.sketches.add(plane);x0,y0,x1,y1=xy
        for v in s.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(x0/10,y0/10,0),adsk.core.Point3D.create(x1/10,y1/10,0)):v.isFixed=True
        return s
    def cut(c,s,profile,expression,name):
        i=c.features.extrudeFeatures.createInput(profile,adsk.fusion.FeatureOperations.CutFeatureOperation)
        assert i.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(expression)),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        i.participantBodies=[c.bRepBodies.item(0)]
        e=c.features.extrudeFeatures.add(i);e.name=name;s.isLightBulbOn=False;return e
    for index,(x0,y0,x1,y1) in enumerate(source['edgeSupportsXY_mm']):
        s=rectangle(upper,upper.xYConstructionPlane,[x0-1.2,y0-1.2,x1+1.2,y1+1.2])
        cut(upper,s,s.profiles.item(0),'1 mm','Expanded_support_clearance_'+str(index+1))
    INSIDE=adsk.fusion.PointContainment.PointInsidePointContainment
    blends=[]
    for c in [lower,upper]:
        b=c.bRepBodies.item(0);edges=adsk.core.ObjectCollection.create()
        for e in b.edges:
            if e.geometry.objectType!='adsk::core::Line3D' or not e.startVertex or not e.endVertex:continue
            p=e.startVertex.geometry;q=e.endVertex.geometry
            if abs(p.x-q.x)>1e-6 or abs(p.y-q.y)>1e-6 or abs(p.z-q.z)<.1:continue
            if c==upper and abs(p.z-q.z)<.4:continue
            z=(p.z+q.z)/2
            n=sum(b.pointContainment(adsk.core.Point3D.create(p.x+dx,p.y+dy,z))==INSIDE for dx,dy in [(-.005,-.005),(-.005,.005),(.005,-.005),(.005,.005)])
            if n==3:edges.add(e)
        fi=c.features.filletFeatures.createInput();fi.edgeSetInputs.addConstantRadiusEdgeSet(edges,adsk.core.ValueInput.createByString('1 mm'),False)
        e=c.features.filletFeatures.add(fi);e.name='Concave_vertical_blends_R1'
        blends.append(dict(component=c.name,edges=edges.count,radius_mm=1))
    d.userParameters.add('head_seat_depth',adsk.core.ValueInput.createByString('2.2 mm'),'mm','Provisional socket head recess')
    s=lower.sketches.add(lower.xYConstructionPlane)
    for x,y in source['screwAxesXY_mm']:
        v=s.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(x/10,y/10,0),.21);v.isFixed=True
    profiles=adsk.core.ObjectCollection.create()
    for p in s.profiles:profiles.add(p)
    before=lower.bRepBodies.item(0).volume*1000
    cut(lower,s,profiles,'head_seat_depth','M2_head_seats_D4p2_depth2p2')
    assert abs(before-lower.bRepBodies.item(0).volume*1000-4*math.pi*(2.1**2-1.1**2)*2.2)<.001
    d.userParameters.itemByName('M2_pilot_depth').expression='4.5 mm'
    assert d.computeAll()
    def block(name,minimum,size):
        m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(*[v/10 for v in minimum])
        c=root.occurrences.addNewComponent(m).component;c.name=name
        s=rectangle(c,c.xYConstructionPlane,[0,0,size[0],size[1]])
        c.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString(str(size[2])+' mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation);s.isLightBulbOn=False
        return c
    block('Battery_L_ALLOWANCE_32x22x5p5_NOT_CELL',[-66,-51,-9],[32,22,5.5])
    # Conservative two-block envelope measured from old single-part XIAO v2.
    # Source X->case Y, source Z->case X, source Y->case Z.
    mcu=block('XIAO_KEY_SIDE_ENVELOPE_FROM_OLD_SINGLE_PART_UNVERIFIED',[-8.89,-20.955,1.6],[17.78,20.955,3.27])
    pi=mcu.constructionPlanes.createInput();assert pi.setByOffset(mcu.xYConstructionPlane,adsk.core.ValueInput.createByString('0.26 mm'));plane=mcu.constructionPlanes.add(pi);plane.isLightBulbOn=False
    s=rectangle(mcu,plane,[4.41267,15.18198,13.35267,22.48198])
    e=mcu.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString('4.2 mm'),adsk.fusion.FeatureOperations.JoinFeatureOperation);e.name='USB_shell_conservative_envelope';s.isLightBulbOn=False
    # Provisional USB/MCU-front access notch, open at the unfinished frame top.
    pi=upper.constructionPlanes.createInput();assert pi.setByOffset(upper.xYConstructionPlane,adsk.core.ValueInput.createByString('2 mm'));plane=upper.constructionPlanes.add(pi);plane.isLightBulbOn=False
    s=rectangle(upper,plane,[-6,0,6,18]);before=upper.bRepBodies.item(0).volume*1000
    cut(upper,s,s.profiles.item(0),'6 mm','USB_access_NOT_final_cable_fit_12mm_wide')
    removed=before-upper.bRepBodies.item(0).volume*1000
    assert removed>0,'Access volume does not intersect the frame'
    assert abs(lower.bRepBodies.item(0).boundingBox.maxPoint.z*10-11.3)<.001,'Support height changed'
    entities=adsk.core.ObjectCollection.create()
    for o in root.occurrences:entities.add(o)
    ii=d.createInterferenceInput(entities);ii.areCoincidentFacesIncluded=False;results=d.analyzeInterference(ii)
    collisions=[]
    for i in range(results.count):
        rr=results.item(i);bb=rr.interferenceBody.boundingBox
        collisions.append(dict(volume_mm3=rr.interferenceBody.volume*1000,min_mm=[v*10 for v in bb.minPoint.asArray()],max_mm=[v*10 for v in bb.maxPoint.asArray()]))
    assert results.count==0,str(collisions)
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    assert doc.save('Two stands retained; CNC blends, head seats, battery/XIAO envelopes and USB access. Verified component-scoped cuts.')
    ex=d.exportManager;assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/'+NAME+'.f3d'))
    for c,label in [(lower,'Lower_L'),(upper,'Upper_L_perimeter_only')]:assert ex.execute(ex.createSTEPExportOptions(BASE+'cad/design/'+NAME+'_'+label+'_LOCAL.step',c))
    source.update(id=doc.dataFile.id,fillets=blends,headSeats_mm=dict(diameter=4.2,depth=2.2),pilotDepth_mm=4.5,batteryAllowance_mm=[32,22,5.5],XIAOMountedTopZ_mm=6.06,USBAccessBounds_mm=[[-6,0,1],[6,18,7]],solidInterferences=results.count,collisionSet='lower, upper perimeter, unpopulated PCB, battery allowance, conservative XIAO envelope',timelineIssues=issues)
    source['limitations']=['Upper is an unfinished perimeter; no switch plate or keycap collision model.','XIAO is an approximate envelope from an old single-part model; solder interface and real version unverified.','USB notch uses assumed cable access; final plug, antenna window and structural review pending.','Stand finger access, deployed sweep and stability remain unverified.','M2 thread lead, grade, preload, tolerances and DFM remain provisional.']
    with open(BASE+'cad/design/'+NAME+'.json','w',encoding='utf-8') as f:json.dump(source,f,ensure_ascii=False,indent=2)
    a.activeViewport.fit();print(json.dumps(dict(name=NAME,fillets=blends,solidInterferences=results.count,USBRemoved_mm3=removed)))
