"""Fusion readOnly: battery wrapping envelope at current location vs PCB raised.

0.2mm wrapping per face is an assumption. No adhesive qualification or actual
PCB copper/solder protrusions represented. Do not infer a usable bonding face.
"""
import adsk.core,adsk.fusion,json
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')
def run(_context: str):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent;mgr=adsk.fusion.TemporaryBRepManager.get()
    cell=next(o for o in root.allOccurrences if o.component.name.startswith('BATTERY_CELL_NOMINAL_42')).bRepBodies.item(0)
    def walk(o):
        for b in o.bRepBodies:
            if b.isSolid:yield o.component.name,b
        for c in o.childOccurrences:yield from walk(c)
    targets=[]
    for o in root.occurrences:
        if o.component.name.startswith(('Lower_L_','Upper_L_','PCB_L_','MCU_RAISED_','XIAO_DETAILED_','CHOC_SWITCHES_AND_SOCKETS_','PCB_SUPPORT_INSULATION_')):targets.extend(walk(o))
    rows=[]
    for lift in [0.,2.6]:
        # Nominal cell boundsX-55..-13,Y-50..-30,Z-8.1..-3.1.
        envelope=mgr.createBox(adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create(-3.4,-4,(-5.6+lift)/10),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),4.24,2.04,.54))
        hits=[];checks=0
        for name,b in targets:
            aa,bb=envelope.boundingBox,b.boundingBox
            if any(min(getattr(aa.maxPoint,v),getattr(bb.maxPoint,v))-max(getattr(aa.minPoint,v),getattr(bb.minPoint,v))<=1e-7 for v in ['x','y','z']):continue
            c=mgr.copy(envelope);assert mgr.booleanOperation(c,mgr.copy(b),adsk.fusion.BooleanTypes.IntersectionBooleanType);checks+=1
            if c.volume*1000>1e-5:hits.append({'target':name,'volume_mm3':c.volume*1000})
        rows.append({'liftFromCurrentCell_mm':lift,'wrappedCellBoundsZ_mm':[-8.3+lift,-2.9+lift],'exactOverlapChecks':checks,'collisions':hits})
    pcb=next(o for o in root.occurrences if o.component.name.startswith('PCB_L_')).bRepBodies.item(0)
    result={'date':'2026-11-10','cloudVersion':app.activeDocument.dataFile.versionNumber,'wrappingPerFaceAssumed_mm':.2,'targetSolids':len(targets),'currentCellToPCBOutlineDistance_mm':app.measureManager.measureMinimumDistance(cell,pcb).value*10,'rows':rows,'conclusion':'Retain current battery elevation as provisional clearance allocation; raising toward PCB requires resolving populated underside collisions. No flat tape bonding face proven.','limitations':['Exact PCB revision,copper and solder protrusions unconfirmed','Tape type,insulation,adhesion,padding,removal,cell swelling and max pouch dimensions unqualified','0.2mm wrap is a sensitivity assumption, not chosen tape thickness']}
    (BASE/'docs/taped-battery-envelope-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
