"""Fusion MCP: reserve D3 bundle and slack space as an alternative to the initial D2 tool."""
import adsk.core,adsk.fusion,json,math
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'


def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    old=next(o for o in root.occurrences if o.component.name=='BATTERY_WIRE_ROUTE_D2_ASSUMED_CLEARANCE_NOT_PART')
    path=BASE+'docs/internal-retention-development.json';r=json.load(open(path,encoding='utf-8'))
    route=r['wireRouteCenters_mm'];initial=list(map(list,route));route[0]=[-33.3,-40,-6.6]
    root.features.removeFeatures.add(old).name='Retire_initial_D2_wire_tool_for_D3_comparison'
    mgr=adsk.fusion.TemporaryBRepManager.get()
    def pt(x):return adsk.core.Point3D.create(*[v/10 for v in x])
    body=mgr.createSphere(pt(route[0]),.15)
    for first,last in zip(route,route[1:]):
        assert mgr.booleanOperation(body,mgr.createCylinderOrCone(pt(first),.15,pt(last),.15),adsk.fusion.BooleanTypes.UnionBooleanType)
        assert mgr.booleanOperation(body,mgr.createSphere(pt(last),.15),adsk.fusion.BooleanTypes.UnionBooleanType)
    occ=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());c=occ.component;c.name='BATTERY_WIRE_ROUTE_D3_ASSUMED_CLEARANCE_NOT_PART'
    feature=c.features.baseFeatures.add();feature.name='D3_polyline_capsule_clearance_not_wire_bend_spec'
    assert feature.startEdit();c.bRepBodies.add(body,feature);assert feature.finishEdit();occ.isLightBulbOn=False
    slack=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());c=slack.component;c.name='BATTERY_SERVICE_SLACK_SPACE_10x10x4_NOT_PART'
    i=c.constructionPlanes.createInput();i.setByOffset(c.xYConstructionPlane,adsk.core.ValueInput.createByString('-7 mm'));pl=c.constructionPlanes.add(i);pl.isLightBulbOn=False
    s=c.sketches.add(pl)
    for v in s.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(-2.9,-4,0),adsk.core.Point3D.create(-1.9,-3,0)):v.isFixed=True
    c.features.extrudeFeatures.addSimple(s.profiles.item(0),adsk.core.ValueInput.createByString('4 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation);s.isLightBulbOn=False;slack.isLightBulbOn=False
    assert d.computeAll()
    length=sum(math.dist(a,b) for a,b in zip(route,route[1:]))
    r.update(initialD2RouteCenters_mm=initial,wireRouteCenters_mm=route,wireBundleEnvelopeDiameter_mm=3,
             wireEnvelopeBasis='JST PH data lists individual wire insulation OD 0.5 to 1.5 mm; D3 is a provisional two-wire bundle allowance, not measured actual wires',
             wireRouteLength_mm=length,wireLengthComparison_mm=length+15,serviceSlackReservationBounds_mm=[[-29,-40,-7],[-19,-30,-3]])
    json.dump(r,open(path,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(dict(bundleEnvelope_mm=3,routeLength_mm=length,lengthPlusAssumedSlack_mm=length+15,slackSpace_mm=[10,10,4])))
