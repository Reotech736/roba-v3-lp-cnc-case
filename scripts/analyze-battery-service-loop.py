"""Nominal 40 mm lead study: exact line/3D circular-arc centerlines.

R3 and D3 bundle are comparison assumptions, not wire specifications.
This script never modifies Fusion or immutable source files.
"""
import math,json
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
def add(a,b):return [x+y for x,y in zip(a,b)]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def mul(a,t):return [x*t for x in a]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(a):return math.sqrt(dot(a,a))
def unit(a):return mul(a,1/norm(a))


def rounded(points,radius):
    corners=[]
    for a,b,c in zip(points,points[1:],points[2:]):
        incoming=unit(sub(b,a));outgoing=unit(sub(c,b))
        angle=math.acos(max(-1,min(1,dot(incoming,outgoing))))
        distance=radius*math.tan(angle/2)
        first=sub(b,mul(incoming,distance));last=add(b,mul(outgoing,distance))
        inward=unit(sub(outgoing,mul(incoming,dot(incoming,outgoing))))
        center=add(first,mul(inward,radius));u=unit(sub(first,center));v=incoming
        mid=add(center,mul(add(mul(u,math.cos(angle/2)),mul(v,math.sin(angle/2))),radius))
        corners.append(dict(first=first,last=last,mid=mid,center=center,radius_mm=radius,angle_rad=angle,tangentLength_mm=distance))
    segments=[];cursor=points[0]
    for index,c in enumerate(corners):
        prev=corners[index-1]['tangentLength_mm'] if index else 0
        available=math.dist(points[index],points[index+1])-prev-c['tangentLength_mm']
        if available<.05:return None
        segments.append(dict(type='line',start=cursor,end=c['first'],length_mm=math.dist(cursor,c['first'])))
        segments.append(dict(type='arc',start=c['first'],mid=c['mid'],end=c['last'],center=c['center'],radius_mm=radius,angle_rad=c['angle_rad'],length_mm=radius*c['angle_rad']))
        cursor=c['last']
    if math.dist(points[-2],points[-1])-corners[-1]['tangentLength_mm']<.05:return None
    segments.append(dict(type='line',start=cursor,end=points[-1],length_mm=math.dist(cursor,points[-1])))
    return segments


def candidate(gap,depth,radius):
    origin=[-13,-30,-5.6-gap];start=[-11.8,-28.8,-4.8-gap];end=[-1.38934,-19.341,-2]
    points=[start,[-8,-26,-4.2-gap],[2,depth,-4.2],[2,-22,-4.2],end]
    segments=rounded(points,radius)
    if segments is None:return None
    transition=math.dist(origin,start);branch=math.sqrt(1+1.5**2)+.5
    length=transition+sum(s['length_mm'] for s in segments)+branch
    return {'lowerDown_mm':gap,'bendRadiusAssumed_mm':radius,'controlVertexDepthY_mm':depth,
            'assumedExit_mm':origin,'unmodeledPouchTransition_mm':transition,
            'bundleSegments':segments,'bundleLength_mm':sum(s['length_mm'] for s in segments),
            'eachBranchIncludingSolderRise_mm':branch,'eachLeadLength_mm':length}


def main():
    poses=[];unresolved=[]
    for gap in [0,2,5,8,10,12,15]:
        for radius in [3,4,5]:
            options=[candidate(gap,-30-i*.1,radius) for i in range(251)]
            options=[p for p in options if p]
            crossing=next(((a,b) for a,b in zip(options,options[1:]) if (a['eachLeadLength_mm']-40)*(b['eachLeadLength_mm']-40)<=0),None)
            if not crossing:
                unresolved.append({'lowerDown_mm':gap,'radius_mm':radius,'reason':'No valid 40mm centerline in selected vertex family'});continue
            a,b=crossing
            for _ in range(32):
                c=candidate(gap,(a['controlVertexDepthY_mm']+b['controlVertexDepthY_mm'])/2,radius)
                if c['eachLeadLength_mm']<40:a=c
                else:b=c
            p=candidate(gap,(a['controlVertexDepthY_mm']+b['controlVertexDepthY_mm'])/2,radius)
            assert abs(p['eachLeadLength_mm']-40)<1e-7
            poses.append(p)
    out={'date':'2026-11-08','baselineCloudVersion':24,'wireNominalLength_mm':40,
         'bundleRadiusAssumed_mm':1.5,'individualWireRadiusAssumed_mm':.5,
         'poses':poses,'unresolved':unresolved,
         'limitations':['R3/R4/R5 are study radii, not certified minimum wire bend radii.',
             'Both nominal 40 mm leads use a bundle centerline plus symmetric terminal branches; independent pair offsets and length tolerances unmodeled.',
             'Each pose is a separate length-preserving curve; a continuous physical deformation between poses is not proven.',
             'Pouch exit corner/direction and final 0.5 mm solder rise remain assumptions.',
             'A full40mm curve alone supplies no strain relief or allowable opening force.']}
    (BASE/'docs/battery-service-loop-study.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'validPoses':len(poses),'unresolved':unresolved,'poses':[{'gap':p['lowerDown_mm'],'radius':p['bendRadiusAssumed_mm'],'depth':p['controlVertexDepthY_mm'],'length':p['eachLeadLength_mm']} for p in poses]},indent=2))


if __name__=='__main__':main()
