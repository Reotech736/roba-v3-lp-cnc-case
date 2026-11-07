"""Fusion MCP. Fork support study; add parameter-driven dogbones and pocket fillets."""
import adsk.core, adsk.fusion, json, math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'
NAME='lp_support_cnc_corners_v02_NOT_FOR_MANUFACTURE'

def run(_context: str):
    a=adsk.core.Application.get()
    project=next(p for p in a.data.dataProjects if p.name=='roba-v3-lp-cnc-case')
    folder=next(f for f in project.rootFolder.dataFolders if f.name=='02_design')
    existing=next((f for f in folder.dataFiles if f.name==NAME),None)
    if existing:
        doc=next((x for x in a.documents if x.dataFile and x.dataFile.id==existing.id),None)
        assert not doc or not doc.isModified,'Discard the failed study before retry'
        doc=doc or a.documents.open(existing)
        doc.activate()
        assert adsk.fusion.Design.cast(a.activeProduct).userParameters.itemByName('corner_relief_radius') is None,'Completed study already exists'
    else:
        doc=next(d for d in a.documents if d.dataFile and d.dataFile.id=='urn:adsk.wipprod:dm.lineage:X1drcMRfTfiFc_K394dWvA')
        assert not doc.isModified
        doc.activate()
        assert doc.saveAs(NAME,folder,'Provisional CNC corner-relief support coupons, not fit-tested.','')
    d=adsk.fusion.Design.cast(a.activeProduct)
    d.userParameters.add('corner_relief_radius',adsk.core.ValueInput.createByString('0.5 mm'),'mm','Provisional cutter-radius candidate, vendor capability unconfirmed')
    d.userParameters.add('back_pocket_radius',adsk.core.ValueInput.createByString('1.5 mm'),'mm','Back pocket corner radius candidate')
    H=adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
    V=adsk.fusion.DimensionOrientations.VerticalDimensionOrientation
    records=[]
    for c in list(d.allComponents):
        if not c.name.startswith('Opening_'):continue
        lip=1.2 if c.name.endswith('1p2') else 1.3
        opening=14.1 if '14p1_' in c.name else 14.2 if '14p2_' in c.name else 14.0
        opening_name='opening_middle' if opening==14.1 else 'opening_large' if opening==14.2 else 'opening_small'
        before=c.bRepBodies.item(0).volume*1000
        edges=adsk.core.ObjectCollection.create()
        for edge in c.bRepBodies.item(0).edges:
            if not edge.startVertex or not edge.endVertex:continue
            p=edge.startVertex.geometry;q=edge.endVertex.geometry
            if abs(abs(p.x)-.9)<1e-6 and abs(abs(p.y)-.9)<1e-6 and abs(p.x-q.x)<1e-6 and abs(p.y-q.y)<1e-6 and abs(p.z-q.z)>.1:edges.add(edge)
        assert edges.count==4
        fi=c.features.filletFeatures.createInput()
        fi.edgeSetInputs.addConstantRadiusEdgeSet(edges,adsk.core.ValueInput.createByString('back_pocket_radius'),False)
        fillet=c.features.filletFeatures.add(fi);fillet.name='Back_pocket_vertical_corners_R1p5'
        expected_fillet=(4-math.pi)*1.5**2*(3-lip)
        assert abs(c.bRepBodies.item(0).volume*1000-before-expected_fillet)<.001
        offset=(opening/2-.5/math.sqrt(2))/10
        expression=opening_name+'/2 - corner_relief_radius/sqrt(2)'
        for sx,sy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            s=c.sketches.add(c.xYConstructionPlane);s.name='Dogbone_'+str(sx)+'_'+str(sy)+'_PARAMETER_DRIVEN'
            circle=s.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(sx*offset,sy*offset,0),.05)
            s.sketchDimensions.addDistanceDimension(s.originPoint,circle.centerSketchPoint,H,adsk.core.Point3D.create(sx*offset,sy*offset+.2,0)).parameter.expression=expression
            s.sketchDimensions.addDistanceDimension(s.originPoint,circle.centerSketchPoint,V,adsk.core.Point3D.create(sx*offset+.2,sy*offset,0)).parameter.expression=expression
            s.sketchDimensions.addRadialDimension(circle,adsk.core.Point3D.create(sx*offset+.1,sy*offset+.1,0)).parameter.expression='corner_relief_radius'
            assert s.profiles.count==1
            cut=c.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString('frame_height'),adsk.fusion.FeatureOperations.CutFeatureOperation)
            cut.name='Corner_relief_for_small_cutter_R0p5';s.isLightBulbOn=False
        expected=before+expected_fillet-(2*math.pi-4)*.5**2*lip
        assert abs(c.bRepBodies.item(0).volume*1000-expected)<.001
        records.append(dict(component=c.name,opening_mm=opening,lip_mm=lip,reliefRadius_mm=.5,openingMaximumSpan_mm=round(opening+2*.5*(1-1/math.sqrt(2)),6),nominal15mmFlangeEdgeMargin_mm=round((15-opening-2*.5*(1-1/math.sqrt(2)))/2,6),volume_mm3=round(expected,6)))
    # Verify corner and aperture parameters continue to work together.
    d.userParameters.itemByName('corner_relief_radius').expression='0.6 mm'
    d.userParameters.itemByName('opening_middle').expression='14.15 mm'
    assert d.computeAll()
    for c in d.allComponents:
        if c.name.startswith('Opening_14p1_'):
            lip=1.2 if c.name.endswith('1p2') else 1.3
            expected=(22**2-14.15**2)*3-(18**2-14.15**2)*(3-lip)+(4-math.pi)*1.5**2*(3-lip)-(2*math.pi-4)*.6**2*lip
            assert abs(c.bRepBodies.item(0).volume*1000-expected)<.001
    d.userParameters.itemByName('corner_relief_radius').expression='0.5 mm'
    d.userParameters.itemByName('opening_middle').expression='14.1 mm'
    assert d.computeAll()
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage]
    assert not issues,str(issues)
    assert doc.save('Add CNC corner candidates and verify parameter perturbation.')
    ex=d.exportManager
    assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/'+NAME+'.f3d'))
    for c in d.allComponents:
        if c.name.startswith('Opening_'):assert ex.execute(ex.createSTEPExportOptions(BASE+'cad/design/'+NAME+'_'+c.name+'.step',c))
    report=dict(name=NAME,id=doc.dataFile.id,date='2026-11-07',variants=records,timelineIssues=issues,parameterCheck='radius 0.5->0.6->0.5 and middle aperture 14.1->14.15->14.1; analytic volume checked',limitations=['Tool diameter 1 mm and depth access not confirmed by JLCCNC.','15 mm switch flange edge margin is a nominal plan-view calculation, not retention strength.','No fit, switch-corner or latch-deflection test; printed/physical validation pending.','Does not set PCB-to-plate height, cap clearance or assembled dimensions.'])
    with open(BASE+'cad/design/'+NAME+'.json','w',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    a.activeViewport.fit();print(json.dumps(report))
