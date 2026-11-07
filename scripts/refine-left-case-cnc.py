"""Fusion MCP: preserve v01; add concave-corner radii and verify battery allowance."""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'
NAME='left_case_structure_cnc_v02_NOT_FOR_MANUFACTURE'

def run(_context: str):
    a=adsk.core.Application.get();project=next(p for p in a.data.dataProjects if p.name=='roba-v3-lp-cnc-case');folder=next(f for f in project.rootFolder.dataFolders if f.name=='02_design')
    assert not any(f.name==NAME for f in folder.dataFiles),'Refined prototype already exists'
    doc=next(x for x in a.documents if x.dataFile and x.dataFile.name=='left_case_structure_v01_NOT_FOR_MANUFACTURE');assert not doc.isModified
    doc.activate();assert doc.saveAs(NAME,folder,'CNC corner and battery-clearance refinement; unfinished mechanical prototype.','')
    d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    lower=next(c for c in d.allComponents if c.name=='Lower_L_FROM_PCB_OUTLINE_PROVISIONAL')
    upper=next(c for c in d.allComponents if c.name=='Upper_L_PERIMETER_ONLY_NO_SWITCH_PLATE')
    source=json.load(open(BASE+'cad/design/left_case_structure_v01_NOT_FOR_MANUFACTURE.json',encoding='utf-8'))
    # Expand upper reliefs before rounding support roots; retain at least the
    # original 0.2 mm clearance after R1 blend additions.
    for i,(x0,y0,x1,y1) in enumerate(source['edgeSupportsXY_mm']):
        s=upper.sketches.add(upper.xYConstructionPlane)
        for v in s.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create((x0-1.2)/10,(y0-1.2)/10,0),adsk.core.Point3D.create((x1+1.2)/10,(y1+1.2)/10,0)):v.isFixed=True
        e=upper.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString('1 mm'),adsk.fusion.FeatureOperations.CutFeatureOperation);e.name='Expanded_support_root_clearance_'+str(i+1);s.isLightBulbOn=False
    INSIDE=adsk.fusion.PointContainment.PointInsidePointContainment
    fillets=[]
    for c in [lower,upper]:
        b=c.bRepBodies.item(0);edges=adsk.core.ObjectCollection.create()
        for edge in b.edges:
            if edge.geometry.objectType!='adsk::core::Line3D' or not edge.startVertex or not edge.endVertex:continue
            p=edge.startVertex.geometry;q=edge.endVertex.geometry
            if abs(p.x-q.x)>1e-6 or abs(p.y-q.y)>1e-6 or abs(p.z-q.z)<.1:continue
            # Keep short upper relief edges out of the first fillet pass.
            if c==upper and abs(p.z-q.z)<.4:continue
            z=(p.z+q.z)/2
            inside=sum(b.pointContainment(adsk.core.Point3D.create(p.x+dx,p.y+dy,z))==INSIDE for dx,dy in [(-.005,-.005),(-.005,.005),(.005,-.005),(.005,.005)])
            if inside==3:edges.add(edge)
        assert edges.count>0
        fi=c.features.filletFeatures.createInput();fi.edgeSetInputs.addConstantRadiusEdgeSet(edges,adsk.core.ValueInput.createByString('1 mm'),False)
        feature=c.features.filletFeatures.add(fi);feature.name='Concave_vertical_corner_candidates_R1'
        fillets.append(dict(component=c.name,edgeCount=edges.count,radius_mm=1))
    # A separate installation allowance verifies the available volume; it is
    # intentionally not a second nested battery body in the collision set.
    m=adsk.core.Matrix3D.create();m.translation=adsk.core.Vector3D.create(-6.6,-5.1,-.9)
    battery=root.occurrences.addNewComponent(m).component;battery.name='Battery_L_INSTALLATION_ALLOWANCE_32x22x5p5_NOT_CELL'
    s=battery.sketches.add(battery.xYConstructionPlane)
    for v in s.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(0,0,0),adsk.core.Point3D.create(3.2,2.2,0)):v.isFixed=True
    battery.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString('5.5 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation);s.isLightBulbOn=False
    entities=adsk.core.ObjectCollection.create()
    for o in root.occurrences:entities.add(o)
    ii=d.createInterferenceInput(entities);ii.areCoincidentFacesIncluded=False;results=d.analyzeInterference(ii)
    assert results.count==0,'Case/PCB/battery allowance interference'
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    assert lower.bRepBodies.count==1 and upper.bRepBodies.count==1
    assert doc.save('Round concave vertical corners; expanded support reliefs and installation allowance pass exact solid collision check.')
    ex=d.exportManager;assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/'+NAME+'.f3d'))
    for c,label in [(lower,'Lower_L'),(upper,'Upper_L_perimeter_only')]:assert ex.execute(ex.createSTEPExportOptions(BASE+'cad/design/'+NAME+'_'+label+'_LOCAL.step',c))
    report=dict(name=NAME,id=doc.dataFile.id,date='2026-11-07',baseDesign='left_case_structure_v01_NOT_FOR_MANUFACTURE',fillets=fillets,solidInterferences=results.count,collisionSet='lower tray, upper perimeter, unpopulated public PCB, battery installation allowance',timelineIssues=issues,limitations=['R1 is a candidate, not blanket JLCCNC approval: deep concavities, short upper notches and horizontal floor corners still require review.','No switch plate, ports, antenna window, locating feature, battery retention or screw head seats.','PCB supports still need physical trace clearance and insulation confirmation.','No actual populated component collision or stand operation test.'])
    with open(BASE+'cad/design/'+NAME+'.json','w',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    a.activeViewport.fit();print(json.dumps(report))
