"""ReadOnly geometric evidence: restored stock, absent pocket face, four42mm edges."""
import adsk.core,adsk.fusion,json,math
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')
def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent;mgr=adsk.fusion.TemporaryBRepManager.get()
    assert doc.dataFile.versionNumber in [29,30]
    point=lambda p:adsk.core.Point3D.create(*[x/10 for x in p])
    lower=next(o for o in root.occurrences if o.component.name.startswith('Lower_L_')).bRepBodies.item(0)
    upper=next(o for o in root.occurrences if o.component.name.startswith('Upper_L_')).bRepBodies.item(0)
    strip=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(point([(11.08+14.9)/2,(-27.2-18.6)/2,(-5.2-1)/2]),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(14.9-11.08)/10,8.6/10,4.2/10))
    nominal=strip.volume*1000;assert mgr.booleanOperation(strip,mgr.copy(lower),adsk.fusion.BooleanTypes.IntersectionBooleanType);missing=max(0,nominal-strip.volume*1000);assert missing<1e-5
    pilots=[]
    for y in [-25.,-21.5]:
        c=mgr.createCylinderOrCone(point([12.8,y,-1]),.0625,point([12.8,y,2.6]),.0625);expected=c.volume*1000
        assert mgr.booleanOperation(c,mgr.copy(upper),adsk.fusion.BooleanTypes.IntersectionBooleanType);absent=max(0,expected-c.volume*1000);assert absent<1e-5
        pilots.append({'XY_mm':[12.8,y],'formerPilotDiameter_mm':1.25,'formerPilotDepth_mm':3.6,'restoredCylinderVolume_mm3':c.volume*1000,'missingStock_mm3':absent})
    edgeRows=[]
    for b,z in [(lower,-11.5),(upper,4.5)]:
        for x in [-111.119997,16.576167]:
            found=[]
            for e in b.edges:
                if e.geometry.objectType!=adsk.core.Line3D.classType():continue
                ends=[[v*10 for v in p.geometry.asArray()] for p in [e.startVertex,e.endVertex]]
                if all(abs(p[0]-x)<1e-5 and abs(p[2]-z)<1e-5 for p in ends):found.append(e.length*10)
            assert len(found)==1 and abs(found[0]-42)<1e-5
            edgeRows.append({'X_mm':x,'Z_mm':z,'singleEdgeLength_mm':found[0]})
    faces=[]
    for f in lower.faces:
        bb=f.boundingBox
        if abs(bb.minPoint.z*10+5.2)<1e-5 and abs(bb.maxPoint.z*10+5.2)<1e-5 and bb.minPoint.x*10>10 and bb.maxPoint.x*10<15 and bb.minPoint.y*10>=-27.2-1e-5 and bb.maxPoint.y*10<=-18.6+1e-5:faces.append(f.area*100)
    assert not faces
    result={'date':'2026-11-10','cloudVersion':doc.dataFile.versionNumber,'workingModified':doc.isModified,'formerRecessInteriorStockProbeGlobal_mm':[11.08,-27.2,-5.2,14.9,-18.6,-1],'nominalProbeVolume_mm3':nominal,'missingRecessStock_mm3':missing,'remainingFormerPocketBottomFaces':len(faces),'filledPilots':pilots,'straightEdges':edgeRows,'casesMaterialNames':[b.material.name for b in [lower,upper]],'scope':'Exact nominal restored stock and specified edges only; no manufacturing/strength certification'}
    (BASE/'docs/removed-fixture-machining-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
