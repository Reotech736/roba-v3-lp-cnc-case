"""Fusion MCP read-only: verify continuous edge and ideal tilted table support.

No claim about measured stand geometry, real feet, stability or tabletop compliance.
"""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'

def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent;mgr=adsk.fusion.TemporaryBRepManager.get()
    dev=json.load(open(BASE+'docs/continuous-contact-edge-development.json',encoding='utf-8'));baseline=json.load(open(BASE+'docs/contact-edge-baseline.json',encoding='utf-8'))['records']
    current=[dict(name=o.component.name,matrix=list(o.transform2.asArray()),volumes=[b.volume*1000 for b in o.component.bRepBodies],visible=o.isLightBulbOn) for o in root.allOccurrences]
    assert len(baseline)==len(current)
    for old,new in zip(baseline,current):
        assert old['name']==new['name'] and old['matrix']==new['matrix'] and old['visible']==new['visible']
        if old['name'] not in dev['affectedComponents']:
            assert len(old['volumes'])==len(new['volumes']) and max([0]+[abs(x-y) for x,y in zip(old['volumes'],new['volumes'])])<1e-5,old['name']
    x0=dev['contactEdgeX_mm'];z0=dev['contactEdgeGlobalZ_mm']
    def cylinder(x,y,zmin,zmax,r):return mgr.createCylinderOrCone(adsk.core.Point3D.create(x/10,y/10,zmin/10),r/10,adsk.core.Point3D.create(x/10,y/10,zmax/10),r/10)
    caseBodies=[]
    for o in root.occurrences:
        if o.component.name in dev['affectedComponents']:
            b=mgr.copy(o.component.bRepBodies.item(0));assert mgr.transform(b,o.transform2);caseBodies.append((o.component.name,b))
    axes=json.load(open(BASE+'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.json',encoding='utf-8'))['screwAxesXY_mm']
    hardware=[]
    for i,(x,y) in enumerate(axes):
        hardware.append(('M2_shank_'+str(i),cylinder(x,y,-9.3,2.7,1)))
        hardware.append(('M2_head_'+str(i),cylinder(x,y,-11.3,-9.3,1.9)))
    tableTests=[]
    for angle in [5,7,10,17,20,30]:
        t=math.radians(angle);normal=[math.sin(t),0,math.cos(t)];tangent=adsk.core.Vector3D.create(math.cos(t),0,-math.sin(t))
        center=adsk.core.Point3D.create((x0-normal[0]*50)/10,-3.8,(z0-normal[2]*50)/10)
        table=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(center,tangent,adsk.core.Vector3D.create(0,1,0),50,30,10))
        overlaps=[]
        for name,b in caseBodies+hardware:
            test=mgr.copy(b);assert mgr.booleanOperation(test,table,adsk.fusion.BooleanTypes.IntersectionBooleanType)
            if test.volume*1000>1e-5:overlaps.append([name,test.volume*1000])
        assert not overlaps,str((angle,overlaps))
        tableTests.append(dict(tilt_deg=angle,tablePenetrations=overlaps,oldBossPenetrationBelowOriginalSelectedEdgePlane_mm=2.5*math.sin(t)))
    roots=[o for o in root.occurrences if o.component.name.startswith(('Lower_L_','Upper_L_','PCB_L_','MCU_RAISED_','XIAO_DETAILED_','CHOC_SWITCHES_AND_SOCKETS_','PCB_SUPPORT_INSULATION_','BATTERY_ASSEMBLY_','COVER_M1p6x6_'))]
    physical=[]
    def walk(o):
        if o.component.name=='CLEARANCE_STUDIES_NOT_PARTS':return
        for b in o.bRepBodies:physical.append(b)
        for child in o.childOccurrences:walk(child)
    for o in roots:walk(o)
    for b in physical:
        bb=b.preciseBoundingBox
        assert bb.minPoint.x*10>=x0-1e-5 and bb.minPoint.z*10>=z0-1e-5,str((b.parentComponent.name,bb.minPoint.asArray()))
    # With dx>=0 and dz>=0, sin(theta)*dx+cos(theta)*dz>=0 for 0<=theta<=90.
    # Report only the intended positive-X lift interval, not a measured stand angle.
    lower=next(o for o in root.occurrences if o.component.name.startswith('Lower_L_'));contact=[]
    for e in lower.bRepBodies.item(0).edges:
        if not adsk.core.Line3D.cast(e.geometry):continue
        p=[[v.geometry.x*10,v.geometry.y*10,v.geometry.z*10] for v in [e.startVertex,e.endVertex]]
        if all(abs(q[0]-x0)<1e-5 and abs(q[2]-z0)<1e-5 for q in p):contact.append(dict(yInterval_mm=sorted([q[1] for q in p]),length_mm=e.length*10))
    assert len(contact)==1 and abs(contact[0]['length_mm']-42)<1e-5
    report=dict(baselineCloudVersion=18,contactEdgeX_mm=x0,contactEdgeZ_mm=z0,continuousEdge=contact[0],tablePlaneEquation='sin(theta)*(X-contactX)+cos(theta)*(Z-contactZ)=0; positive-X side lifted',
        tableTests=tableTests,physicalBodyBoundsChecked=len(physical),allPhysicalBodiesWithinPositiveContactQuadrant=True,componentTransformsAndVisibilityPreserved=True,otherComponentVolumesPreserved=True,
        limitations=['Rigid ideal geometry only; actual stand opening angle, legs, feet, tabletop compliance/friction and tip-over stability are unmeasured',
        'Nominal M2 head D3.8 H2 and nominal shank D2; screw purchase/tolerances/thread qualification remain pending',
        'No contact-edge chamfer or protective layer modeled; either would need a renewed support-plane check'])
    json.dump(report,open(BASE+'docs/continuous-contact-edge-verification.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(report,ensure_ascii=False))
