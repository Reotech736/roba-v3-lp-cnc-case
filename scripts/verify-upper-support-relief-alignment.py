"""Fusion MCP read-only: compare every support relief tier against live pad locations."""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'

def run(_context: str):
    d=adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct);root=d.rootComponent;mgr=adsk.fusion.TemporaryBRepManager.get()
    c=next(o.component for o in root.occurrences if o.component.name.startswith('Upper_L_'));body=c.bRepBodies.item(0)
    supports=json.load(open(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.json',encoding='utf-8'))['edgeSupportsXY_mm']
    rows=[]
    for index,rect in enumerate(supports,1):
        for prefix,margin in [('Support_clearance_',.2),('Expanded_support_clearance_',1.2)]:
            name=prefix+str(index)+('_0p2mm' if margin==.2 else '')
            f=next(f for f in c.features.extrudeFeatures if f.name==name);assert not f.isSuppressed,name
            s=f.profile.parentSketch;pts=[p.geometry for line in s.sketchCurves.sketchLines for p in [line.startSketchPoint,line.endSketchPoint]]
            actual=[min(p.x*10 for p in pts),min(p.y*10 for p in pts),max(p.x*10 for p in pts),max(p.y*10 for p in pts)]
            expected=[rect[0]-margin,rect[1]-margin,rect[2]+margin,rect[3]+margin]
            assert max(abs(x-y) for x,y in zip(actual,expected))<1e-5,str((name,actual,expected))
            rows.append(dict(feature=name,support=index,margin_mm=margin,actualXYXY_mm=actual,matchesCurrentSupport=True))
    obsolete=next(f for f in c.features.extrudeFeatures if f.name=='Relocated_support_4_upper_relief_0p2mm');assert obsolete.isSuppressed
    cavities=[]
    for index,(x0,y0,x1,y1) in enumerate(supports,1):
        x0-=.2;y0-=.2;x1+=.2;y1+=.2
        tool=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create((x0+x1)/20,(y0+y1)/20,.05),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,.1))
        assert mgr.booleanOperation(tool,body,adsk.fusion.BooleanTypes.IntersectionBooleanType)
        overlap=tool.volume*1000;assert overlap<1e-5,str((index,overlap))
        cavities.append(dict(support=index,nominalXYClearanceEachSide_mm=.2,globalZRange_mm=[-1,0],obstructingUpperMaterial_mm3=overlap))
    inside=adsk.fusion.PointContainment.PointInsidePointContainment;restored=[]
    for x,y in [(-106.9,-60),(-106.9,-58),(-55,8.5),(-54,8.8),(-53.5,9)]:
        actual=body.pointContainment(adsk.core.Point3D.create(x/10,y/10,.05))==inside;assert actual
        restored.append(dict(pointGlobal_mm=[x,y,-.5],restoredMaterial=True))
    out=dict(activeReliefTiersMatched=8,currentSupportsChecked=4,reliefChecks=rows,obsoleteDuplicateSuppressed=True,nominalCavityChecks=cavities,oldReliefMaterialSamples=restored,
        limitation='Nominal geometric association/void checks only; root fillets, clearances and machining still require physical/DFM qualification')
    json.dump(out,open(BASE+'docs/upper-support-relief-verification.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False))
