"""Explicit two-wire feasibility study. Does not mutate Fusion.

User inputs: two40mm leads, approximate insulated OD1mm. Pouch exit spacing,
R1 transition/R3 loop/R1.5 pad bends are unqualified geometric assumptions.
"""
import math,json,runpy
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
helpers=runpy.run_path(str(BASE/'scripts/analyze-battery-service-loop.py'))
add,sub,mul,dot,norm,unit=[helpers[k] for k in ['add','sub','mul','dot','norm','unit']]

def rounded(points,radii):
    corners=[]
    for a,b,c,radius in zip(points,points[1:],points[2:],radii):
        incoming=unit(sub(b,a));outgoing=unit(sub(c,b));angle=math.acos(max(-1,min(1,dot(incoming,outgoing))))
        distance=radius*math.tan(angle/2);first=sub(b,mul(incoming,distance));last=add(b,mul(outgoing,distance))
        inward=unit(sub(outgoing,mul(incoming,dot(incoming,outgoing))));center=add(first,mul(inward,radius));u=unit(sub(first,center));v=incoming
        mid=add(center,mul(add(mul(u,math.cos(angle/2)),mul(v,math.sin(angle/2))),radius))
        corners.append(dict(first=first,last=last,mid=mid,center=center,radius_mm=radius,angle_rad=angle,tangentLength_mm=distance))
    segments=[];cursor=points[0]
    for index,c in enumerate(corners):
        previous=corners[index-1]['tangentLength_mm'] if index else 0
        if math.dist(points[index],points[index+1])-previous-c['tangentLength_mm']<.05:return None
        segments.append(dict(type='line',start=cursor,end=c['first'],length_mm=math.dist(cursor,c['first'])))
        segments.append(dict(type='arc',start=c['first'],mid=c['mid'],end=c['last'],center=c['center'],radius_mm=c['radius_mm'],angle_rad=c['angle_rad'],length_mm=c['radius_mm']*c['angle_rad']))
        cursor=c['last']
    if math.dist(points[-2],points[-1])-corners[-1]['tangentLength_mm']<.05:return None
    segments.append(dict(type='line',start=cursor,end=points[-1],length_mm=math.dist(cursor,points[-1])))
    return segments

def candidate(gap,depth,side):
    offset=.8*side;pad=-1.38934+side
    points=[[-13,-30,-5.6+offset-gap],[-11.8,-28.8,-4.8+offset-gap],[-8,-26,-4.2+offset-gap],[2,depth,-4.2+offset],[2,-22,-4.2+offset],[pad,-19.341,-1.5],[pad,-19.341,0]]
    segments=rounded(points,[1.,3,3,3,1.5])
    if not segments:return None
    return {'lowerDown_mm':gap,'side':side,'controlDepthY_mm':depth,'assumedExit_mm':points[0],'padXY_mm':points[-1][:2],'segments':segments,'length_mm':sum(s['length_mm'] for s in segments)}

def main():
    poses=[];failures=[]
    for gap in [0,2,5,8,10]:
        leads=[]
        for side in [-1,1]:
            options=[candidate(gap,-29-i*.1,side) for i in range(301)];options=[p for p in options if p]
            crossing=next(((a,b) for a,b in zip(options,options[1:]) if (a['length_mm']-40)*(b['length_mm']-40)<=0),None)
            if crossing is None:failures.append({'gap':gap,'side':side,'reason':'No valid40mm route in selected family'});continue
            a,b=crossing
            for _ in range(40):
                c=candidate(gap,(a['controlDepthY_mm']+b['controlDepthY_mm'])/2,side)
                if c['length_mm']<40:a=c
                else:b=c
            p=candidate(gap,(a['controlDepthY_mm']+b['controlDepthY_mm'])/2,side);assert abs(p['length_mm']-40)<1e-8;leads.append(p)
        if len(leads)==2:poses.append({'lowerDown_mm':gap,'leads':leads})
    fixedEndDeviation=0.
    for pose in poses[1:]:
        for lead,closed in zip(pose['leads'],poses[0]['leads']):
            for segment,baseline in zip(lead['segments'][-4:],closed['segments'][-4:]):
                for key in ['start','mid','end']:
                    if key in segment:fixedEndDeviation=max(fixedEndDeviation,math.dist(segment[key],baseline[key]))
    assert fixedEndDeviation<1e-10
    result={'date':'2026-11-09','baselineCloudVersion':27,'wireNominalLengthEach_mm':40,'wireRadiusAssumed_mm':.5,'pouchExitSpacingAssumed_mm':1.6,'assumedCornerRadii_mm':[1.,3,3,3,1.5],'poses':poses,'failures':failures,'fixedTerminalLastFourSegmentsMaxDeviation_mm':fixedEndDeviation,'limitations':['Exit corner,1.6mm vertical exit spacing and exit tangents unmeasured','R1/R1.5/R3 are geometric trials, not certified bend specifications','Separate40mm poses do not prove continuous flexible opening','No force, fatigue, conductor strain or solder fillet modeled','Geometric trial only; complete tie routing, pressing wires into saddle and physical installation need separate qualification']}
    (BASE/'docs/individual-battery-lead-study.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'poses':len(poses),'failures':failures,'leads':[{'gap':p['lowerDown_mm'],'side':l['side'],'depth':l['controlDepthY_mm'],'length':l['length_mm']} for p in poses for l in p['leads']]}))

if __name__=='__main__':main()
