import adsk.core, adsk.fusion, json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/cad/design/'
def run(_context: str):
    a=adsk.core.Application.get()
    with open(BASE+'pcb_v2_layout_input.json',encoding='utf-8') as f: data=json.load(f)
    project=next(p for p in a.data.dataProjects if p.name=='roba-v3-lp-cnc-case')
    folder=next(f for f in project.rootFolder.dataFolders if f.name=='02_design')
    name='pcb_v2_functional_reference_v01'
    assert not any(f.name==name for f in folder.dataFiles), 'Design already exists'
    doc=a.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    d=adsk.fusion.Design.cast(a.activeProduct)
    d.designType=adsk.fusion.DesignTypes.ParametricDesignType
    r=d.rootComponent
    def child(x,k): return next((t for t in x if isinstance(t,list) and t[0]==k),None)
    def component(name,tx):
        m=adsk.core.Matrix3D.create()
        m.translation=adsk.core.Vector3D.create(tx/10,0,0)
        o=r.occurrences.addNewComponent(m);o.component.name=name
        return o.component
    summary=[]
    for board in data['boards']:
        side=board['side']; tx=0 if side=='L' else 160
        c=component('PCB_'+side+'_v2_reference_NOT_VERIFIED',tx)
        u=next(f for f in board['footprints'] if f['reference']=='U1')
        ux,uy=map(float,u['at'][:2])
        def xy(x,y): return adsk.core.Point3D.create((float(x)-ux)/10,(uy-float(y))/10,0)
        s=c.sketches.add(c.xYConstructionPlane);s.name='Upstream_v2_outline_and_mount_holes'
        s.isComputeDeferred=True
        for e in board['edges']:
            start=xy(*child(e,'start')[1:3]);end=xy(*child(e,'end')[1:3])
            if e[0]=='gr_line': curve=s.sketchCurves.sketchLines.addByTwoPoints(start,end)
            else: curve=s.sketchCurves.sketchArcs.addByThreePoints(start,xy(*child(e,'mid')[1:3]),end)
            curve.isFixed=True
        mounts=[f for f in board['footprints'] if 'MountingHole' in f['name']]
        for f in mounts:
            dia=float(f['pads'][0]['drill'][0])
            circle=s.sketchCurves.sketchCircles.addByCenterRadius(xy(*f['at'][:2]),dia/20)
            circle.isFixed=True
        s.isComputeDeferred=False
        assert s.profiles.count==len(mounts)+1, 'Unexpected outline profiles'
        profile=max(s.profiles,key=lambda p:p.areaProperties().area)
        e=c.features.extrudeFeatures.addSimple(profile,adsk.core.ValueInput.createByString('1.6 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        e.name='Reference_PCB_thickness_1p6'
        e.bodies.item(0).name='PCB_envelope_mount_holes_only'
        s.isLightBulbOn=False
        markers=c.sketches.add(c.xYConstructionPlane);markers.name='Switch_5mm_drill_centers_NOT_plate_cutouts'
        count=0
        import math
        for f in board['footprints']:
            if 'SW_MX' not in f['name']: continue
            pad=next(p for p in f['pads'] if p['drill'] and len(p['drill'])==1 and float(p['drill'][0])==5)
            rad=math.radians(float(f['at'][2]) if len(f['at'])>2 else 0)
            px,py=map(float,pad['at'][:2]); fx,fy=map(float,f['at'][:2])
            x=fx+math.cos(rad)*px+math.sin(rad)*py;y=fy-math.sin(rad)*px+math.cos(rad)*py
            circle=markers.sketchCurves.sketchCircles.addByCenterRadius(xy(x,y),0.25);circle.isConstruction=True;circle.isFixed=True
            count+=1
        markers.isLightBulbOn=True
        bat=component('Battery_'+side+'_30x20x4_PARKED_NOT_INSTALLED',tx)
        bs=bat.sketches.add(bat.xYConstructionPlane);bs.name='Battery_body_approximate_no_wires'
        for l in bs.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(0,3,0),adsk.core.Point3D.create(3,5,0)):l.isFixed=True
        be=bat.features.extrudeFeatures.addSimple(bs.profiles.item(0),adsk.core.ValueInput.createByString('4 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        be.name='Battery_body_4mm_approximate';bs.isLightBulbOn=False
        summary.append(dict(side=side,originKiCad_mm=[ux,uy],displayTranslateX_mm=tx,mountingHoles=len(mounts),switchMarkers=count))
    assert not any(t.errorOrWarningMessage for t in d.timeline), 'Timeline issue'
    assert doc.saveAs(name,folder,'Provisional v2 PCB layout from upstream; actual revision unconfirmed. No case geometry. Batteries parked outside boards.','')
    ex=d.exportManager
    assert ex.execute(ex.createFusionArchiveExportOptions(BASE+name+'.f3d'))
    for c in d.allComponents:
        if c.bRepBodies.count:
            label='PCB_L' if c.name.startswith('PCB_L') else 'PCB_R' if c.name.startswith('PCB_R') else 'Battery_L' if c.name.startswith('Battery_L') else 'Battery_R'
            assert ex.execute(ex.createSTEPExportOptions(BASE+name+'_'+label+'.step',c))
    a.activeViewport.fit()
    print(json.dumps(dict(name=name,id=doc.dataFile.id,summary=summary,bodies=sum(c.bRepBodies.count for c in d.allComponents))))

