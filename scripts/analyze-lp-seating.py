"""Reproducible nominal seating/sensitivity study; never modifies Fusion or source CAD."""
import json
import math
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def point_segment(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0, min(1, ((p[0]-a[0])*dx + (p[1]-a[1])*dy)/(dx*dx+dy*dy)))
    return math.hypot(p[0]-a[0]-t*dx, p[1]-a[1]-t*dy)


def polygon_gap(a, b):
    separated = False
    for poly in (a, b):
        for p, q in zip(poly, poly[1:]+poly[:1]):
            nx, ny = q[1]-p[1], p[0]-q[0]
            aa = [x*nx+y*ny for x, y in a]
            bb = [x*nx+y*ny for x, y in b]
            separated |= max(aa) < min(bb) or max(bb) < min(aa)
    if not separated:
        return 0.0
    return min(point_segment(p, v, w) for first, second in ((a, b), (b, a))
               for p in first for v, w in zip(second, second[1:]+second[:1]))


def main():
    board = json.loads((BASE/'cad/design/pcb_v2_layout_input.json').read_text(encoding='utf-8'))['boards'][0]
    u = next(f for f in board['footprints'] if f['reference'] == 'U1')
    ux, uy = map(float, u['at'][:2])
    keys = []
    for f in board['footprints']:
        if 'SW_MX' not in f['name']:
            continue
        pad = next(p for p in f['pads'] if p['drill'] and len(p['drill']) == 1 and float(p['drill'][0]) == 5)
        t = math.radians(float(f['at'][2]) if len(f['at']) > 2 else 0)
        px, py = map(float, pad['at'][:2]); fx, fy = map(float, f['at'][:2])
        x = fx + math.cos(t)*px + math.sin(t)*py - ux
        y = uy-fy + math.sin(t)*px - math.cos(t)*py
        h = 18.8/2
        poly = [(x+math.cos(t)*i-math.sin(t)*j, y+math.sin(t)*i+math.cos(t)*j)
                for i, j in [(-h,-h),(h,-h),(h,h),(-h,h)]]
        keys.append((f['reference'], poly))
    assert len(keys) == 23
    cover_studies = []
    for half_width, rear, front in [(9.9,-20.95,3),(9.9,-20.35,3),(9.7,-20.95,3),(9.5,-20.95,3),(9.3,-20.95,3),(9.3,-20.95,2.4),(9.3,-20.35,2.4)]:
        cover = [(-half_width,rear),(half_width,rear),(half_width,front),(-half_width,front)]
        gaps = sorted((polygon_gap(poly,cover), ref) for ref, poly in keys)
        cover_studies.append(dict(halfWidth_mm=half_width,rearY_mm=rear,frontY_mm=front, minimumGap_mm=gaps[0][0], closestKey=gaps[0][1],
                                  gaps=[dict(key=ref,gap_mm=g) for g,ref in gaps]))
    # Dimensions have different datums: 6.40 ends at flange underside, not PCB face.
    below_flange = 5.7-3.5
    stem_from_pcb = 6.4+below_flange
    pcb_z = 1.6
    roof_target = pcb_z+below_flange
    sensitivity = []
    for roof in [4.5, roof_target, 3.5]:
        for drop in [1.0,2.0,2.5,3.0,3.5,3.94]:
            gap = pcb_z+stem_from_pcb-3.05-drop-roof
            sensitivity.append(dict(roofZ_mm=round(roof,4), capLowestPointBelowReleasedStem_mm=drop,
                                    pressedGap_mm=round(gap,4), meetsAssumed0p3Gap=gap >= .3-1e-9))
    out = dict(date='2026-11-08', currentFusionDocument='left_case_two_stands_v05_NOT_FOR_MANUFACTURE',
               inspectedCloudVersion=6, geometryModified=False,
               switchDrawing='https://www.kailhswitch.com/uploads/15927/files/CPG1353D01D01-24-data-sheet.pdf',
               datumCorrection='6.40 is stem top to flange underside, not PCB seating face',
               nominalUnderFlangeDepth_mm=round(below_flange,4), nominalStemAbovePCB_mm=round(stem_from_pcb,4),
               nominalPCBTopZ_mm=pcb_z, nominalFlangeUndersideZ_mm=round(roof_target,4),
               currentRoofZ_mm=4.5, nominalCurrentRoofExcess_mm=round(4.5-roof_target,4),
               maxTravel_mm=3.05, assumedRequiredGap_mm=.3,
               capDropMaxAtNominalSeatingFor0p3Gap_mm=round(pcb_z+stem_from_pcb-3.05-roof_target-.3,4),
               heightSensitivity=sensitivity, coverPlanSensitivity=cover_studies,
               limitations=['Derived heights are nominal dimensions, not tolerance-qualified assembly targets.',
                            'Actual switch seating, PCB revision and cap insertion/underside geometry remain unverified.',
                            'Cap drops and 0.3 mm clearance are comparison assumptions, not measured specifications.',
                            '18.8 mm footprint is a provisional lateral envelope, not certified full cap motion.',
                            'Shortened cover candidates require renewed MCU coverage, wall, retention and USB checks.',
                            'No geometry or cloud document was changed.'])
    assert abs(cover_studies[0]['minimumGap_mm']-.11934) < 1e-5
    (BASE/'docs/lp-seating-clearance-study.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(nominalFlangeZ=roof_target, roofExcess=4.5-roof_target,
                         coverCandidates=[{k:r[k] for k in ('halfWidth_mm','rearY_mm','frontY_mm','minimumGap_mm','closestKey')} for r in cover_studies]),indent=2))


if __name__ == '__main__':
    main()
