"""Compare actual backing footprints with the unchanged floor profile, including curves.

Usage: python scripts/verify-stand-footprints.py [--module-dir PATH_TO_SHAPELY]
Input sketches must be refreshed from Fusion if floor/stand geometry changes.
"""
import argparse,json,math,sys
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--module-dir');args=parser.parse_args()
if args.module_dir:sys.path.insert(0,args.module_dir)
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union
BASE=Path(__file__).resolve().parents[1]
r=json.loads((BASE/'docs/stand-correction-floor-outline.json').read_text(encoding='utf-8'));segments=r['segments'];chain=list(segments.pop(0))
while segments:
    distance,i,end=min((math.dist(chain[-1],s[e]),i,e) for i,s in enumerate(segments) for e in [0,-1]);assert distance<.001
    s=segments.pop(i);chain.extend((s if end==0 else s[::-1])[1:])
floor=Polygon(chain);assert floor.is_valid
actual=json.loads((BASE/'docs/corrected-stand-solid-verification.json').read_text(encoding='utf-8'))
axes=json.loads((BASE/'cad/design/left_case_two_stands_v05_NOT_FOR_MANUFACTURE.json').read_text(encoding='utf-8'))['screwAxesXY_mm']
rows=[]
for f in actual['actualBackingFootprints']:
    c=f['circle'];backing=unary_union([box(*f['rectXYXY_mm']),Point(*c['centerXY_mm']).buffer(c['radius_mm'],quad_segs=512)])
    outside=backing.difference(floor).area;gap=backing.distance(floor.boundary)
    seatGap=min(backing.distance(Point(*a).buffer(2.1,quad_segs=512)) for a in axes)
    assert outside<1e-8 and gap>1 and seatGap>1
    rows.append(dict(outsideBaseFootprintArea_mm2=outside,minBackingToBaseBoundary_mm=gap,minBackingToM2SeatProjection_mm=seatGap))
out=dict(method='Entire actual rectangles and D12 circle footprints vs original floor profile; explicit curve approximation bounds',
    floorChordTolerance_mm=.0001,circleMaxChordError_mm=6*(1-math.cos(math.pi/2048)),rows=rows,allBackingsInsideOriginalBaseFootprint=True,
    limitation='Projection geometry only; no strength, manufacturing or tolerance qualification; inputs must track live Fusion geometry')
(BASE/'docs/corrected-stand-footprint-verification.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
