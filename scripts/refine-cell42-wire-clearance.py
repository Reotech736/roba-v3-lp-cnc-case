"""Fusion MCP: lift CELL42 wire reservation clear of stand backing; trim tab tool."""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'

def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert a.activeDocument.dataFile.versionNumber==15
    old=next(o for o in root.occurrences if o.component.name=='BATTERY_WIRE_ROUTE_D3_CELL42_40mm_BUDGET_NOT_PART')
    pull=next(o for o in root.occurrences if o.component.name=='CELL_ADHESIVE_PULL_TAB_ACCESS_RESERVATION_CELL42_NOT_PART')
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/checkpoints/v05_cell42_before_wire_clearance_refinement.f3d'))
    route=[[-11.8,-28.8,-4.8],[-8,-24,-3.5],[-8,-8,-3.5],[-1.38934,-6,-2.75]]
    mgr=adsk.fusion.TemporaryBRepManager.get()
    def pt(x):return adsk.core.Point3D.create(*[v/10 for v in x])
    b=mgr.createSphere(pt(route[0]),.15)
    for x,y in zip(route,route[1:]):
        assert mgr.booleanOperation(b,mgr.createCylinderOrCone(pt(x),.15,pt(y),.15),adsk.fusion.BooleanTypes.UnionBooleanType)
        assert mgr.booleanOperation(b,mgr.createSphere(pt(y),.15),adsk.fusion.BooleanTypes.UnionBooleanType)
    new=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());new.component.name=old.component.name
    f=new.component.features.baseFeatures.add();assert f.startEdit();new.component.bRepBodies.add(b,f);assert f.finishEdit();new.isLightBulbOn=False
    old.component.name='RETIRED_CELL42_INITIAL_'+old.component.name;old.isLightBulbOn=False
    c=pull.component;s=c.sketches.item(0)
    # Explicitly roll to the existing sketch before changing fixed geometry.
    d.timeline.markerPosition=s.timelineObject.index+1
    # Only left-edge points at X=-19 move to -18; other endpoints remain fixed.
    curves=list(s.sketchCurves)
    for x in curves:x.isFixed=False
    for x in list(s.sketchPoints)[1:]:x.isFixed=False
    for x in list(s.sketchPoints)[1:]:
        if abs(x.geometry.x*10+19)<1e-6:assert x.move(adsk.core.Vector3D.create(.1,0,0))
    for x in curves:x.isFixed=True
    d.timeline.moveToEnd();assert d.computeAll()
    r=json.load(open(BASE+'docs/battery42-layout-development.json',encoding='utf-8'))
    length=sum(math.dist(x,y) for x,y in zip(route,route[1:]));transition=math.dist(r['assumedCellExitCornerGlobal_mm'],route[0])
    r.update(wireRouteCenters_mm=route,routeLength_mm=length,assumedCornerToRouteTransition_mm=transition,nominalConnectionRouteIncludingCorner_mm=length+transition,remainingWireLengthBudget_mm=40-length-transition,pullTabAccessBoundsGlobal_mm=[[-18,-42,-8.3],[-5,-38,-8.1]])
    json.dump(r,open(BASE+'docs/battery42-layout-development.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(dict(routePlusCorner_mm=length+transition,remainingBudget_mm=40-length-transition)))
