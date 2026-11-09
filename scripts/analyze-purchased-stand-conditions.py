"""Product-informed conditional contacts; no actual motion certification.

The22/40 image labels are interpreted as normal heights ONLY for sensitivity
scenarios. The image shows vertical heights under a laptop, not this definition.
"""
import json,math,runpy,hashlib
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
hull=runpy.run_path(str(BASE/'scripts/analyze-stand-conditional-stability.py'))['hull']
cross=runpy.run_path(str(BASE/'scripts/analyze-stand-conditional-stability.py'))['cross']

def main():
    source=json.loads((BASE/'docs/stand-case-mass-reference.json').read_text(encoding='utf-8'))
    parts=source['caseMassesOnly'];mass=sum(p['mass_kg'] for p in parts)
    com=[sum(p['mass_kg']*p['centerOfMassGlobal_mm'][i] for p in parts)/mass for i in range(3)]
    rows=[]
    for height in [22.,40.]:
        for hingeZ in [-8.,-10.1,-12.2]:
            hingeX=-52.1+8.5;length=47.5;footZ=-8.-height;drop=hingeZ-footZ
            assert 0<drop<length
            footX=hingeX+math.sqrt(length**2-drop**2)
            theta=math.atan2(-11.5-footZ,footX+111.119997)
            project=lambda x,z:(x+111.119997)*math.cos(theta)-(z+11.5)*math.sin(theta)
            groundX=project(footX,footZ);cg=(project(com[0],com[2]),com[1])
            assert abs((footX+111.119997)*math.sin(theta)+(footZ+11.5)*math.cos(theta))<1e-10
            for width in [0.,14.4]:
                polygon=hull([(0.,-59.),(0.,-17.)]+[(groundX,y+offset) for y in [-61.1,-17.1] for offset in [-width/2,width/2]])
                assert all(cross(a,polygon[(i+1)%len(polygon)],cg)>0 for i,a in enumerate(polygon))
                keyrows=[]
                for key in source['keyPressXYReference']:
                    kp=(project(key['xy_mm'][0],key['stemTopZ_mm']),key['xy_mm'][1]);limits=[]
                    for i,a in enumerate(polygon):
                        b=polygon[(i+1)%len(polygon)];margin=cross(a,b,cg);side=cross(a,b,kp)
                        if side<0:limits.append(mass*9.80665*margin/-side)
                    keyrows.append({'xy_mm':key['xy_mm'],'outsideAssumedSupportPolygon':bool(limits),'caseOnlyCriticalVerticalForce_N':min(limits) if limits else None})
                outside=[k for k in keyrows if k['outsideAssumedSupportPolygon']]
                rows.append({'imageHeightInterpretedAsNormal_mm':height,'assumedHingeZ_mm':hingeZ,'derivedLeafAngle_deg':math.degrees(math.asin(drop/length)),'derivedCaseTilt_deg':math.degrees(theta),'assumedContactWidth_mm':width,'footGlobalXZ_mm':[footX,footZ],'supportPolygonGroundXY_mm':polygon,'keysOutsideAssumedPolygon':len(outside),'minimumCaseOnlyCriticalVerticalForce_N':min(k['caseOnlyCriticalVerticalForce_N'] for k in outside),'keyResults':keyrows})
    picture=BASE/'docs/images/stand-inspection/purchased-stand-product-height.jpg'
    result={'date':'2026-11-10','cloudVersion':source['cloudVersion'],'modelChanged':False,'actualProductMotionVerified':False,
            'productSource':{'purchaseURL':'https://ja.aliexpress.com/item/1005005605228469.html','livePageRetrieved':False,'evidence':'User-supplied purchased product image and approximate hinge measurement','imageFile':str(picture.relative_to(BASE)).replace('\\','/'),'imageSHA256':hashlib.sha256(picture.read_bytes()).hexdigest(),'imageClaims':{'heightLabels_mm':[22,40],'laptopAngleLabels_deg':[7,17],'adjustmentPositions':3},'imageHeightDatumConfirmed':False},
            'userApproxHingeOffset_mm':8.5,'assumedOffsetEnd':'NegativeX end, opposite lifted rubber end','derivedHingeX_mm':-43.6,
            'hypotheticalMovingLength_mm':47.5,'lengthDerivation':'Nominal56 minus approximate8.5 offset; not actual hinge-to-contact radius measurement',
            'normalHeightScenarios_mm':[22,40],'heightInterpretation':'Sensitivity calculation only: foot normal distance below mounting planeZ-8. Product image labels are vertical under an inclined laptop; the datum differs and intermediate third position is unknown.',
            'caseOnlyMass_kg':mass,'caseOnlyCOMGlobal_mm':com,'rows':rows,
            'limitations':['HingeZ and moving contact radius unmeasured','Actual contact shape, friction, tape peel, lock strength and assembled COM unknown','Advertised7/17deg are laptop examples, not case angle inputs','No actual force rating; case-only static calculation at stem top','Three hingeZ values and two heights are hypothetical scenarios, not certified product bounds']}
    (BASE/'docs/purchased-stand-conditional-study.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'rows':[{k:r[k] for k in ['imageHeightInterpretedAsNormal_mm','assumedHingeZ_mm','derivedCaseTilt_deg','assumedContactWidth_mm','keysOutsideAssumedPolygon']} for r in rows]}))

if __name__=='__main__':main()
