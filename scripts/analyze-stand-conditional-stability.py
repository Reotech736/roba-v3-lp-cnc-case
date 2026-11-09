"""Conditional stand contacts from explicitly assumed hinge/leaf dimensions.
No Fusion mutations. Case-only weight is not the assembled keyboard weight.
"""
import json,math
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def hull(points):
 p=sorted(set(points));lower=[];upper=[]
 for v in p:
  while len(lower)>1 and cross(lower[-2],lower[-1],v)<=0:lower.pop()
  lower.append(v)
 for v in reversed(p):
  while len(upper)>1 and cross(upper[-2],upper[-1],v)<=0:upper.pop()
  upper.append(v)
 return lower[:-1]+upper[:-1]
def main():
 source=json.loads((BASE/'docs/stand-case-mass-reference.json').read_text(encoding='utf-8'));parts=source['caseMassesOnly']
 mass=sum(p['mass_kg'] for p in parts);com=[sum(p['mass_kg']*p['centerOfMassGlobal_mm'][i] for p in parts)/mass for i in range(3)]
 contactx=-111.119997;contactz=-11.5;rows=[]
 for alpha in [30,45,60,75]:
  angle=math.radians(alpha);hingex=-50.1;hingez=-10.;length=52.
  fx=hingex+length*math.cos(angle);fz=hingez-length*math.sin(angle)
  theta=math.atan2(contactz-fz,fx-contactx)
  project=lambda x,z:(x-contactx)*math.cos(theta)-(z-contactz)*math.sin(theta)
  fground=project(fx,fz);cg=(project(com[0],com[2]),com[1])
  for width in [0.,14.4]:
   contacts=[(0.,-59.),(0.,-17.)]+[(fground,y+dy) for y in [-61.1,-17.1] for dy in [-width/2,width/2]]
   polygon=hull(contacts);keyrows=[]
   assert all(cross(polygon[i],polygon[(i+1)%len(polygon)],cg)>0 for i in range(len(polygon)))
   for key in source['keyPressXYReference']:
    # Provisional vertical load point at stem top, not exact keycap surface.
    kp=(project(key['xy_mm'][0],key['stemTopZ_mm']),key['xy_mm'][1]);limits=[]
    for i,a in enumerate(polygon):
     b=polygon[(i+1)%len(polygon)];margin=cross(a,b,cg);keyside=cross(a,b,kp)
     if keyside<0:limits.append(mass*9.80665*margin/-keyside)
    keyrows.append({'xy_mm':key['xy_mm'],'outsideAssumedSupportPolygon':bool(limits),'caseOnlyCriticalVerticalForce_N':min(limits) if limits else None})
   outside=[r for r in keyrows if r['outsideAssumedSupportPolygon']]
   rows.append({'assumedLeafAngle_deg':alpha,'impliedCaseTilt_deg':math.degrees(theta),'assumedGroundFootWidth_mm':width,'footGlobalXZ_mm':[fx,fz],'supportPolygonGroundXY_mm':polygon,'caseOnlyGravityProjection_mm':cg,'keysOutsideAssumedPolygon':len(outside),'minimumCaseOnlyCriticalForce_N':min([r['caseOnlyCriticalVerticalForce_N'] for r in outside],default=None),'keyResults':keyrows})
 result={'date':'2026-11-09','cloudVersion':source['cloudVersion'],'caseGeometryChanged':False,'actualStandMotionValidated':False,'assumptions':{'hingeGlobalXZ_mm':[-50.1,-10.],'leafLength_mm':52.,'hingeAxisDirection':'Y','leafAngles_deg':[30,45,60,75],'contactEdgeGlobalXZY_mm':[contactx,contactz,[-59,-17]],'standFootY_mm':[-61.1,-17.1],'footWidthsCompared_mm':[0,14.4],'forcePoint':'stem top, actual cap shape/force point unverified'},'caseOnlyMass_kg':mass,'caseOnlyCOMGlobal_mm':com,'foldedStandProtrusionNominal_mm':4.2-3.5,'equations':{'tilt':'atan2(contactZ-footZ, footX-contactX)','groundX':'(x-contactX)*cos(theta)-(z-contactZ)*sin(theta)','edgeTipForce':'caseMass*g*inwardCross(COM)/(-inwardCross(key)) for outside key'},'limitations':['Assumed leaf length, hinge position and stop angles are not measurements','No friction, adhesive peel, stand lock strength, rubber compression or dynamic load calculation','Full assembly mass/COM and actual keycap force points unknown; computed force is a case-only conditional illustration, not allowable load','Both stands assumed equal angle and coplanar; no actual hinge sweep or mechanism collision proof'],'rows':rows}
 (BASE/'docs/stand-conditional-stability-study.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'caseOnlyMass_kg':mass,'rows':[{k:r[k] for k in ['assumedLeafAngle_deg','impliedCaseTilt_deg','assumedGroundFootWidth_mm','keysOutsideAssumedPolygon','minimumCaseOnlyCriticalForce_N']} for r in rows]},ensure_ascii=False))
if __name__=='__main__':main()
