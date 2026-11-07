"""Fusion MCP entry point. Independent, parameter-driven LP support coupons."""
import adsk.core, adsk.fusion, json
BASE = 'C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'
NAME = 'lp_support_parameter_study_v01_NOT_FOR_MANUFACTURE'

def run(_context: str):
    a = adsk.core.Application.get()
    project = next(p for p in a.data.dataProjects if p.name == 'roba-v3-lp-cnc-case')
    folder = next(f for f in project.rootFolder.dataFolders if f.name == '02_design')
    assert not any(f.name == NAME for f in folder.dataFiles), 'Study already exists'
    doc = a.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    d = adsk.fusion.Design.cast(a.activeProduct)
    d.designType = adsk.fusion.DesignTypes.ParametricDesignType
    for name, value in [('coupon_width',22),('frame_height',3),('underside_relief',18),('opening_small',14),('opening_middle',14.1),('opening_large',14.2),('lip_thin',1.2),('lip_thick',1.3)]:
        d.userParameters.add(name,adsk.core.ValueInput.createByString(str(value)+' mm'),'mm','Provisional comparison dimension; fit unverified')
    H = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
    V = adsk.fusion.DimensionOrientations.VerticalDimensionOrientation
    def square(sketch, size, expression):
        half = size/20
        lines = sketch.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(-half,-half,0),adsk.core.Point3D.create(half,half,0))
        for index in (0,2):sketch.geometricConstraints.addHorizontal(lines.item(index))
        for index in (1,3):sketch.geometricConstraints.addVertical(lines.item(index))
        p = lines.item(0).startSketchPoint
        q = lines.item(0).endSketchPoint
        opposite = lines.item(1).endSketchPoint
        dims = sketch.sketchDimensions
        dims.addDistanceDimension(sketch.originPoint,p,H,adsk.core.Point3D.create(-half,-half-.3,0)).parameter.expression = expression+'/2'
        dims.addDistanceDimension(sketch.originPoint,p,V,adsk.core.Point3D.create(-half-.3,-half,0)).parameter.expression = expression+'/2'
        dims.addDistanceDimension(p,q,H,adsk.core.Point3D.create(0,-half-.6,0)).parameter.expression = expression
        dims.addDistanceDimension(q,opposite,V,adsk.core.Point3D.create(half+.3,0,0)).parameter.expression = expression
    result = []
    for row,(lip_name,lip) in enumerate([('lip_thin',1.2),('lip_thick',1.3)]):
        for col,(opening_name,opening) in enumerate([('opening_small',14),('opening_middle',14.1),('opening_large',14.2)]):
            label = 'Opening_'+str(opening).replace('.','p')+'_Lip_'+str(lip).replace('.','p')
            m = adsk.core.Matrix3D.create()
            m.translation = adsk.core.Vector3D.create(col*3,row*3,0)
            c = d.rootComponent.occurrences.addNewComponent(m).component
            c.name = label
            s = c.sketches.add(c.xYConstructionPlane)
            s.name = 'Centered_opening_and_outer_frame_PARAMETER_DRIVEN'
            square(s,22,'coupon_width')
            square(s,opening,opening_name)
            assert s.profiles.count == 2
            ring = max(s.profiles,key=lambda p:p.areaProperties().area)
            e = c.features.extrudeFeatures.addSimple(ring,adsk.core.ValueInput.createByString('frame_height'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            e.name = 'Frame_with_through_opening'
            s.isLightBulbOn = False
            relief = c.sketches.add(c.xYConstructionPlane)
            relief.name = 'Underside_relief_leaves_local_lip'
            square(relief,18,'underside_relief')
            cut = c.features.extrudeFeatures.addSimple(relief.profiles.item(0),adsk.core.ValueInput.createByString('frame_height - '+lip_name),adsk.fusion.FeatureOperations.CutFeatureOperation)
            cut.name = 'Underside_pocket_lip_'+str(lip)+'mm'
            relief.isLightBulbOn = False
            expected = (22*22-opening*opening)*3-(18*18-opening*opening)*(3-lip)
            actual = c.bRepBodies.item(0).volume*1000
            assert abs(expected-actual)<.001
            result.append(dict(component=label,opening_mm=opening,lip_mm=lip,volume_mm3=round(actual,5),analyticalVolume_mm3=round(expected,5)))
    # A meaningful parameter perturbation verifies that the centered aperture
    # and the resulting body volumes update; restore before saving/exporting.
    parameter = d.userParameters.itemByName('opening_middle')
    parameter.expression = '14.15 mm'
    assert d.computeAll()
    for c in d.allComponents:
        if c.name.startswith('Opening_14p1_'):
            lip = 1.2 if c.name.endswith('1p2') else 1.3
            expected = (22*22-14.15**2)*3-(18*18-14.15**2)*(3-lip)
            assert abs(c.bRepBodies.item(0).volume*1000-expected)<.001
    parameter.expression = '14.1 mm'
    assert d.computeAll()
    issues = [t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage]
    assert not issues,str(issues)
    assert doc.saveAs(NAME,folder,'Six provisional switch-support coupons: 14.0/14.1/14.2 mm apertures, 1.2/1.3 mm lips. Sharp internal corners are unresolved.','')
    ex = d.exportManager
    assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/'+NAME+'.f3d'))
    for c in d.allComponents:
        if c.bRepBodies.count:
            assert ex.execute(ex.createSTEPExportOptions(BASE+'cad/design/'+NAME+'_'+c.name+'.step',c))
    report = dict(name=NAME,id=doc.dataFile.id,date='2026-11-07',variants=result,parameterPerturbation='opening_middle 14.1 -> 14.15 -> 14.1 mm, recompute and analytic volume verified',timelineIssues=issues,limitations=['No physical switch fit or retention test.','Sharp internal corners are idealized, not a CNC toolpath; cutter radius and corner relief remain unresolved.','No PCB, socket, cap or removal-tool model. Coupon does not set final plate height relative to PCB.','Numbers are comparison candidates, not manufacturing tolerances.','Each STEP is component-local geometry.'])
    with open(BASE+'cad/design/'+NAME+'.json','w',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    a.activeViewport.fit()
    print(json.dumps(report))
