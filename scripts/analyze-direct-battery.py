"""Read immutable KiCad B1 pads; derive direct-solder 40 mm routing study."""
import json, re, math, hashlib
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]


def main():
    source=BASE/'cad/reference/pcb/public-v2-left.kicad_pcb'
    raw=source.read_bytes();tokens=re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+',raw.decode())
    stack=[];tree=None
    for t in tokens:
        if t=='(':stack.append([])
        elif t==')':
            row=stack.pop()
            if stack:stack[-1].append(row)
            else:tree=row
        else:stack[-1].append(t[1:-1] if t.startswith('"') else t)
    def child(row,key):return next(x for x in row if isinstance(x,list) and x[0]==key)
    def footprint(ref):return next(x for x in tree if isinstance(x,list) and x[0]=='footprint' and any(isinstance(y,list) and y[:3]==['property','Reference',ref] for y in x))
    u=footprint('U1');f=footprint('B1');ux,uy=map(float,child(u,'at')[1:3]);fx,fy,angle=map(float,child(f,'at')[1:4])
    ct,st=math.cos(math.radians(angle)),math.sin(math.radians(angle))
    pads=[]
    for pad in f:
        if not isinstance(pad,list) or pad[0]!='pad' or pad[1] not in ['1','2']:continue
        px,py=map(float,child(pad,'at')[1:3])
        pads.append({'number':pad[1],'layer':child(f,'layer')[1],'sizeXY_mm':list(map(float,child(pad,'size')[1:3])),
                     'net':child(pad,'net')[1:],'centerGlobalXY_mm':[fx+ct*px+st*py-ux,uy-fy+st*px-ct*py]})
    assert len(pads)==2
    origin=[-13,-30,-5.6]
    # D3 bundle up to branch point, then D1 wire reservations to pad undersides.
    route=[origin,[-11.8,-28.8,-4.8],[-8,-25,-3.5],[-5,-22,-2.5],[-1.38934,-19.341,-2]]
    branches=[]
    for p in pads:
        x,y=p['centerGlobalXY_mm'];end=[x,y,-.5]
        points=route+[end]
        length=sum(math.dist(a,b) for a,b in zip(points,points[1:]))+.5
        # Extra .5 reaches PCB plane at Z0 from last wire center.
        gaps=[]
        for gap in [0,5,10,15,20,25,30,40]:
            start=[origin[0],origin[1],origin[2]-gap]
            lower=math.dist(start,[x,y,0])
            gaps.append({'lowerDown_mm':gap,'endpointDistanceLowerBound_mm':lower,
                         'routePlusTranslationComparison_mm':length+gap,
                         'comparisonRemainingFrom40_mm':40-length-gap})
        branches.append({'pad':p['number'],'net':p['net'],'wireCenterRoute_mm':points,
                         'assumedSolderPlaneZ_mm':0,'assumedWireRadius_mm':.5,
                         'routePlusFinalHalfMillimeter_mm':length,'remainingFrom40_mm':40-length,
                         'serviceComparisons':gaps})
    out={'date':'2026-11-08','baselineCloudVersion':22,'userConfirmed':{
        'connection':'Direct solder to PCB battery connector pads; no battery connector on this unit',
        'wire40mmEndpoints':'Pouch exit to solder termination, not connector tip'},
        'repositoryMainAtInspection':'69fc34d2996e6aaf63b29f6a58d104b32669f610',
        'sourceURL':'https://github.com/kumamuk-git/roBa/blob/69fc34d2996e6aaf63b29f6a58d104b32669f610/pcb/v2/roBa_L/roba_L.kicad_pcb',
        'sourceSHA256':hashlib.sha256(raw).hexdigest(),'pcbRevisionStatus':'Public v2 mechanical/electrical reference; exact physical board revision still unconfirmed',
        'pads':pads,'assumedPouchExit_mm':origin,'bundleRadius_mm':1.5,'bundleRoute_mm':route,
        'branches':branches,'oldConnectorRouteLength_mm':31.081941524002584,
        'supersedes':['JST component assumed installed','JST mating-plug service access','31.08 mm connector route as current solution'],
        'limitations':['Exit corner, wire diameters and solder fillet shape remain assumptions.',
            'Polyline lengths do not certify minimum bend radius, a retained service loop or collision-free motion.',
            'With direct solder, the lower and PCB remain tethered; never prescribe unplugging a nonexistent connector.',
            'Service comparisons add translation to assembled path as a numerical comparison, not a proven flexible route.',
            'Strain relief must support insulated wire, not load solder pads or pouch tabs; exact material/retention unqualified.']}
    (BASE/'docs/direct-solder-battery-study.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'pads':pads,'lengths_mm':[b['routePlusFinalHalfMillimeter_mm'] for b in branches]},ensure_ascii=False))


if __name__=='__main__':main()
