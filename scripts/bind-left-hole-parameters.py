"""Fusion MCP: bind the fastening candidate's existing hole sketches to named parameters."""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'
NAME='left_case_fastening_v03_NOT_FOR_MANUFACTURE'

def run(_context: str):
    a=adsk.core.Application.get();doc=next(x for x in a.documents if x.dataFile and x.dataFile.name==NAME);assert not doc.isModified
    doc.activate();d=adsk.fusion.Design.cast(a.activeProduct)
    assert d.userParameters.itemByName('head_seat_diameter') is None,'Parameters already bound'
    d.userParameters.add('head_seat_diameter',adsk.core.ValueInput.createByString('4.2 mm'),'mm','Provisional socket head seat diameter')
    bindings=[]
    for c in list(d.allComponents):
        if c.name not in ['Lower_L_FROM_PCB_OUTLINE_PROVISIONAL','Upper_L_PERIMETER_ONLY_NO_SWITCH_PLATE']:continue
        for s in list(c.sketches):
            for circle in list(s.sketchCurves.sketchCircles):
                parameter=next((name for radius,name in [(.3,'boss_diameter'),(.11,'M2_clearance'),(.08,'M2_tap_pilot'),(.21,'head_seat_diameter')] if abs(circle.radius-radius)<1e-7),None)
                if not parameter:continue
                circle.isFixed=False;circle.centerSketchPoint.isFixed=True
                p=circle.centerSketchPoint.geometry
                s.sketchDimensions.addRadialDimension(circle,adsk.core.Point3D.create(p.x+.3,p.y+.3,0)).parameter.expression=parameter+'/2'
                bindings.append(dict(component=c.name,parameter=parameter))
    assert len(bindings)==20
    lower=next(c for c in d.allComponents if c.name=='Lower_L_FROM_PCB_OUTLINE_PROVISIONAL')
    before=lower.bRepBodies.item(0).volume*1000
    d.userParameters.itemByName('M2_clearance').expression='2.3 mm';assert d.computeAll()
    expected=4*math.pi*(2.3**2-2.2**2)/4*(10.5-2.2)
    assert abs(before-lower.bRepBodies.item(0).volume*1000-expected)<.001
    d.userParameters.itemByName('M2_clearance').expression='2.2 mm';assert d.computeAll()
    assert abs(before-lower.bRepBodies.item(0).volume*1000)<.001
    ii_entities=adsk.core.ObjectCollection.create()
    for o in d.rootComponent.occurrences:ii_entities.add(o)
    ii=d.createInterferenceInput(ii_entities);ii.areCoincidentFacesIncluded=False;assert d.analyzeInterference(ii).count==0
    assert not any(t.errorOrWarningMessage for t in d.timeline)
    assert doc.save('Bind 20 boss/hole diameters and verify clearance-hole parameter perturbation.')
    ex=d.exportManager;assert ex.execute(ex.createFusionArchiveExportOptions(BASE+'cad/design/'+NAME+'.f3d'))
    path=BASE+'cad/design/'+NAME+'.json';report=json.load(open(path,encoding='utf-8'));report['diameterParameterBindings']=len(bindings);report['diameterParameterCheck']='M2_clearance 2.2 -> 2.3 -> 2.2 mm, analytic volume removal verified, zero interference after restore'
    json.dump(report,open(path,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(dict(bindings=len(bindings),check=report['diameterParameterCheck'])))
