"""Fusion MCP: 1 mm carrier floor candidate, maintaining the adhesive stack above it."""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'


def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    c=next(o.component for o in root.occurrences if o.component.name.startswith('BATTERY_REMOVABLE_CARRIER_'))
    floor=next(f for f in c.features.extrudeFeatures if f.name=='Carrier_floor_0p5')
    distance=next(p for p in c.modelParameters if p.createdBy==floor and p.role=='AlongDistance')
    distance.expression='1 mm';floor.name='Carrier_floor_1p0_PROVISIONAL'
    changed=0
    for comp_prefix,old,new in [('BATTERY_REMOVABLE_CARRIER_',-8.8,-8.3),('CELL_REMOVABLE_ADHESIVE_',-8.8,-8.3),('BATTERY_CELL_NOMINAL_',-8.6,-8.1),('CELL_ADHESIVE_PULL_TAB_',-8.8,-8.3)]:
        comp=next(o.component for o in root.occurrences if o.component.name.startswith(comp_prefix))
        for p in comp.modelParameters:
            if p.role=='AlongDistance' and p.createdBy.objectType==adsk.fusion.ConstructionPlane.classType() and abs(p.value*10-old)<1e-6:
                p.expression=str(new)+' mm';changed+=1
    assert changed==5,str(changed)
    assert d.computeAll()
    assert c.bRepBodies.count==1
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    p=BASE+'docs/internal-retention-development.json';r=json.load(open(p,encoding='utf-8'))
    r['carrier'].update(floor_mm=1,boundsGlobal_mm=[[-66.3,-51.3,-9.3],[-33.7,-28.7,-6.3]])
    r['nominalCellBoundsGlobal_mm']=[[-65,-50,-8.1],[-35,-30,-4.1]]
    r['floorRevision']='0.5 to 1.0 mm candidate for prototype handling; no selected process or strength certification'
    json.dump(r,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(dict(carrierFloor_mm=1,raisedStackPlanes=changed,nominalCellTopZ_mm=-4.1,timelineIssues=issues)))
