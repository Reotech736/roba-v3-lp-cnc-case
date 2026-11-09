"""Fusion readOnly: audit live v26/v27/v28 configuration and bracket load path.

Checks existing evidence, does not certify material strength or manufacture.
"""
import adsk.core,adsk.fusion,json,math
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')


def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber in [26,27,28]
    approved=json.loads((BASE/'docs/current-approved-component-state.json').read_text(encoding='utf-8'))
    live={o.fullPathName:o for o in root.allOccurrences};matches=[];deviations=[]
    for row in approved:
        o=live.get(row['path'])
        if o is None:deviations.append({'path':row['path'],'reason':'missing'});continue
        matrixDelta=max(abs(a-b) for a,b in zip(row['matrix'],o.transform2.asArray()))
        vols=[b.volume*1000 for b in o.component.bRepBodies]
        volumeDelta=max([0]+[abs(a-b) for a,b in zip(row['volumes'],vols)])
        if matrixDelta>1e-8 or len(vols)!=row['bodies'] or volumeDelta>1e-5:deviations.append({'path':row['path'],'matrixDelta':matrixDelta,'volumeDelta_mm3':volumeDelta,'bodyCount':len(vols)})
        else:matches.append(row['path'])
    mgr=adsk.fusion.TemporaryBRepManager.get()
    def point(p):return adsk.core.Point3D.create(*[v/10 for v in p])
    def box(b):
        x0,y0,z0,x1,y1,z1=b
        return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(point([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2]),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
    def material(boxcoords,body):
        b=box(boxcoords);assert mgr.booleanOperation(b,mgr.copy(body),adsk.fusion.BooleanTypes.IntersectionBooleanType);return b.volume*1000
    bracket=next(o for o in root.allOccurrences if o.component.name.startswith('WIRE_STRAIN_RELIEF_CASE_BRACKET_')).bRepBodies.item(0)
    # Compare the top and bottom of the web/foot junction, independently of
    # single-body status. The added inboard web is X10.3..11.1, Y-24..-20.
    thickness=.01
    below=material([10.3,-24,-2.211,11.1,-20,-2.201],bracket)/thickness
    above=material([10.3,-24,-2.199,11.1,-20,-2.189],bracket)/thickness
    expected=.8*4
    # Min remaining upper wall beside new M1.6 major diameter, measured along X.
    upper=next(o for o in root.occurrences if o.component.name.startswith('Upper_L_')).bRepBodies.item(0)
    inside=adsk.fusion.PointContainment.PointInsidePointContainment
    wall=[];sleeves=[]
    for y in [-25,-21.5]:
        xs=[x/1000 for x in range(10000,16501,5)]
        occupied=[x for x in xs if upper.pointContainment(point([x,y,.8]))==inside]
        left=[x for x in occupied if x<12.8-.8];right=[x for x in occupied if x>12.8+.8]
        # This is a scan of radial stock beside the screw; no strength inference.
        wall.append({'axisXY_mm':[12.8,y],'samplePitch_mm':.005,'leftMaterialMinX_mm':min(left) if left else None,'rightMaterialMaxX_mm':max(right) if right else None})
        outer=mgr.createCylinderOrCone(point([12.8,y,-1]),.17,point([12.8,y,2.6]),.17)
        inner=mgr.createCylinderOrCone(point([12.8,y,-1.01]),.08,point([12.8,y,2.61]),.08)
        assert mgr.booleanOperation(outer,inner,adsk.fusion.BooleanTypes.DifferenceBooleanType)
        nominal=outer.volume*1000;sample=mgr.copy(outer)
        assert mgr.booleanOperation(sample,mgr.copy(upper),adsk.fusion.BooleanTypes.IntersectionBooleanType)
        sleeves.append({'axisXY_mm':[12.8,y],'threadMajorRadius_mm':.8,'comparisonOuterRadius_mm':1.7,'nominalRadialWall_mm':.9,'nominalSleeveVolume_mm3':nominal,'missingSleeveMaterial_mm3':max(0,nominal-sample.volume*1000)})
    report={'date':'2026-11-09','cloudVersion':doc.dataFile.versionNumber,'modified':doc.isModified,
            'approvedRecordsChecked':len(approved),'matchingApprovedRecords':len(matches),'approvedStateDeviations':deviations,
            'webFootJunction':{'webExpectedWidth_mm':.8,'webYLength_mm':4,'expectedFullLapArea_mm2':expected,
                              'sliceBelowFoot_mm2':below,'sliceAboveFoot_mm2':above,'fullLapMaterialFraction':above/expected,
                              'criterion':'Full inboard-web footprint should reach mounting foot; this is geometric continuity, not strength qualification.'},
            'upperMountWallScan':wall,'upperThreadRadialSleeves':sleeves,'pin3Absent':not any(o.component.name=='pin3' for o in root.allOccurrences),
            'timelineIssues':[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage]}
    suffix='v26-before' if doc.dataFile.versionNumber==26 and not doc.isModified else 'current'
    (BASE/f'docs/design-consistency-audit-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))
