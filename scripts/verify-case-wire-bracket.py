"""Fusion readOnly: local bracket, holes, tool shafts, wall and wire-end invariance."""
import adsk.core,adsk.fusion,json,math
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')


def run(_context: str):
    app=adsk.core.Application.get();doc=app.activeDocument;d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    assert doc.dataFile.versionNumber in [25,26,27]
    mgr=adsk.fusion.TemporaryBRepManager.get();intersect=adsk.fusion.BooleanTypes.IntersectionBooleanType
    def point(p):return adsk.core.Point3D.create(*[v/10 for v in p])
    def get(prefix):return next(o for o in root.allOccurrences if o.component.name.startswith(prefix))
    def walk(o):
        for b in o.bRepBodies:
            if b.isSolid:yield o.component.name,b
        for c in o.childOccurrences:yield from walk(c)
    def cylinder(x,y,z0,z1,r):return mgr.createCylinderOrCone(point([x,y,z0]),r/10,point([x,y,z1]),r/10)
    def box(b):
        x0,y0,z0,x1,y1,z1=b
        return mgr.createBox(adsk.core.OrientedBoundingBox3D.create(point([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2]),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
    def overlap(a,b):
        aa,bb=a.boundingBox,b.boundingBox
        if any(min(getattr(aa.maxPoint,v),getattr(bb.maxPoint,v))-max(getattr(aa.minPoint,v),getattr(bb.minPoint,v))<=1e-7 for v in ['x','y','z']):return 0
        c=mgr.copy(a);target=mgr.copy(b)
        assert mgr.booleanOperation(c,target,intersect);return c.volume*1000
    bracket=get('WIRE_STRAIN_RELIEF_CASE_BRACKET_').bRepBodies.item(0)
    lower=get('Lower_L_').bRepBodies.item(0);upper=get('Upper_L_').bRepBodies.item(0)
    targets=[]
    for o in root.allOccurrences:
        if o.component.name.startswith(('Lower_L_','Upper_L_','PCB_L_','MCU_RAISED_','XIAO_DETAILED_','CHOC_V2_RED_','CHOC_SOCKET_DETAILED_','BATTERY_CELL_NOMINAL_42','BATTERY_REMOVABLE_CARRIER_','PCB_SUPPORT_INSULATION_','BATTERY_WIRE_ROUTE_D3_DIRECT_')):targets.extend(walk(o))
    bracketHits=[{'target':n,'volume_mm3':v} for n,b in targets if (v:=overlap(bracket,b))>1e-5]
    hardware=[]
    for prefix in ['WIRE_BRACKET_M1p6x4_','WIRE_BRACKET_TIE_HEAD_']:
        for name,b in walk(get(prefix)):
            hits=[]
            for target,body in targets+[('bracket',bracket)]:
                if prefix.startswith('WIRE_BRACKET_M1p6x4') and target.startswith('Upper_L_'):continue
                v=overlap(b,body)
                if v>1e-5:hits.append({'target':target,'volume_mm3':v})
            hardware.append({'study':prefix,'body':b.name,'collisionsExcludingUpperThreadMajorOverlap':hits})
    axes=json.loads((BASE/'docs/case-wire-bracket-development.json').read_text())['axesXY_mm'];holes=[];tools=[]
    for x,y in axes:
        holes.append({'axisXY_mm':[x,y],'upperD1p25PilotObstruction_mm3':overlap(cylinder(x,y,-1,2.6,.625),upper),
                      'bracketD1p8ClearanceObstruction_mm3':overlap(cylinder(x,y,-2.2,-1,.9),bracket),
                      'headAnnulusSupportMissing_mm3':None})
        bearing=cylinder(x,y,-2.2,-2.19,1.5);inner=cylinder(x,y,-2.21,-2.18,.9)
        assert mgr.booleanOperation(bearing,inner,adsk.fusion.BooleanTypes.DifferenceBooleanType)
        holes[-1]['headAnnulusSupportMissing_mm3']=max(0,bearing.volume*1000-overlap(bearing,bracket))
        for diameter in [1.8,3]:
            tool=cylinder(x,y,-20,-3.1,diameter/2)
            hits=[{'target':name,'volume_mm3':v} for name,b in targets+[('bracket',bracket)] if not name.startswith('Lower_L_') and (v:=overlap(tool,b))>1e-5]
            tools.append({'axisXY_mm':[x,y],'shaftDiameter_mm':diameter,'lowerRemoved':True,'collisions':hits})
    # Exact residual rectangular wall within the intentionally added backing.
    wall=box([14.9,-27.2,-5.2,16,-18.6,-1]);missing=max(0,wall.volume*1000-overlap(wall,lower))
    currentBounds=[[v*10 for v in p.asArray()] for p in [lower.boundingBox.minPoint,lower.boundingBox.maxPoint]]
    preflight=json.loads((BASE/'docs/case-wire-bracket-preflight.json').read_text())
    assert max(abs(a-b) for aa,bb in zip(currentBounds,preflight['lowerBoundsBefore_mm']) for a,b in zip(aa,bb))<1e-5
    # The terminal arc/straight segment stay fixed in all sampled service poses.
    study=json.loads((BASE/'docs/battery-service-loop-study.json').read_text());poses=[p for p in study['poses'] if p['bendRadiusAssumed_mm']==3 and p['lowerDown_mm'] in [0,2,5,8,10]]
    terminal=poses[0]['bundleSegments'][-2:]
    deviations=[]
    for pose in poses:
        deviation=max(math.dist(a[key],b[key]) for a,b in zip(terminal,pose['bundleSegments'][-2:]) for key in ['start','end'])
        deviations.append({'lowerDown_mm':pose['lowerDown_mm'],'terminalCurveMaxEndpointDeviation_mm':deviation})
    out={'date':'2026-11-09','baselineCloudVersion':25,'bracketVsPhysicalAndWireCollisions':bracketHits,
         'hardwareStudies':hardware,'newHoleChecks':holes,'driverChecks':tools,'nominal1p1WallMissingMaterial_mm3':missing,
         'lowerMaxBoundsUnchanged':True,'lowerBounds_mm':currentBounds,'terminalCurveInvariance':deviations,
         'threadComparison':{'screw':'M1.6x4','grip_mm':1.2,'projection_mm':2.8,'cylindricalPilotDepth_mm':3.6,'bottomGap_mm':.8,'assumed118degDrillPointExtra_mm':.625/math.tan(math.radians(59))},
         'limitations':['Nominal geometry only; new 1.1mm local wall and cantilever need material, strength and DFM validation.',
             'A complete installed tie, contact force, friction and continuous opening/removal are not proven.',
             'D1.8 and D3 are assumed straight shafts; current D3.4 head seats clear both. Actual driver/handle unselected.']}
    (BASE/'docs/case-wire-bracket-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out))
