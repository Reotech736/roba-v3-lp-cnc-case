"""Fusion readOnly: sampled hypothetical leaf against current lower only.

Not a product CAD model. Assumes all leaf material is below the hinge axis,
no material behind it, R2 corners and a 47.5x14.4x4.2 moving plate. Fixed base,
linkage, actual rubber and continuous/table-relative opening are excluded.
"""
import adsk.core,adsk.fusion,json,math
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')

def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct)
    assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:H9Nq8f1PSl6GXmxJMgIkbw'
    assert doc.dataFile.versionNumber==27 and not doc.isModified
    mgr=adsk.fusion.TemporaryBRepManager.get()
    lower=next(o for o in d.rootComponent.occurrences if o.component.name.startswith('Lower_L_')).bRepBodies.item(0)
    def point(x,y,z):return adsk.core.Point3D.create(x/10,y/10,z/10)
    def box(x0,y0,z0,x1,y1,z1):
        return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(point((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
    rows=[]
    for y in [-61.1,-17.1]:
        for z in [-8.,-10.1,-12.2]:
            x0=-43.6;x1=3.9;y0=y-7.2;y1=y+7.2;r=2.
            plate=box(x0+r,y0,z-4.2,x1-r,y1,z)
            assert mgr.booleanOperation(plate,box(x0,y0+r,z-4.2,x1,y1-r,z),adsk.fusion.BooleanTypes.UnionBooleanType)
            for cx in [x0+r,x1-r]:
                for cy in [y0+r,y1-r]:
                    cylinder=mgr.createCylinderOrCone(point(cx,cy,z-4.2),r/10,point(cx,cy,z),r/10)
                    assert mgr.booleanOperation(plate,cylinder,adsk.fusion.BooleanTypes.UnionBooleanType)
            hits=[]
            for angle in range(0,91,5):
                sample=mgr.copy(plate);matrix=adsk.core.Matrix3D.create()
                assert matrix.setToRotation(math.radians(angle),adsk.core.Vector3D.create(0,1,0),point(x0,y,z))
                assert mgr.transform(sample,matrix)
                assert mgr.booleanOperation(sample,mgr.copy(lower),adsk.fusion.BooleanTypes.IntersectionBooleanType)
                volume=sample.volume*1000
                if volume>1e-5:hits.append({'angle_deg':angle,'overlap_mm3':volume})
            rows.append({'centerY_mm':y,'hingeZ_mm':z,'sampledAngles':19,'collisions':hits})
    result={'date':'2026-11-09','cloudVersion':27,'modified':doc.isModified,'hingeOffsetUserApprox_mm':8.5,'assumedNegativeXEndReference':True,'hingeX_mm':-43.6,'hypotheticalLeafLengthWidthThicknessR_mm':[47.5,14.4,4.2,2.],
            'comparison':'Temporary rounded plate; two Y positions, three assumed hinge heights,19 angles0..90deg; against lower case only',
            'totalDiscreteComparisons':114,'rows':rows,'actualProductMotionVerified':False,
            'limitations':['Leaf behind/above axis, fixed base, support linkage and rubber shape not known','No continuous sweep proof, tolerances, ground trajectory or simultaneous hand access checked','Three hinge heights are hypothetical sensitivity cases, not measured bounds']}
    (BASE/'docs/stand-hinge-envelope-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert not doc.isModified
    print(json.dumps(result))
