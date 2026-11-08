"""Fusion MCP: derive the current Spring MINI proxy by removing generic pin3.

Retain upstream STEP bytes and v20 checkpoint; remove via feature history, not visibility.
"""
import adsk.core,adsk.fusion,json,hashlib
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'
OLD='CHOC_V2_RED_DETAILED_AUTHOR_REFERENCE'
NEW='CHOC_V2_RED_DETAILED_DERIVED_SPRING_MINI_NO_FIX_PIN'

def run(_context: str):
    a=adsk.core.Application.get();doc=a.activeDocument;d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    assert doc.name=='left_case_two_stands_v05_NOT_FOR_MANUFACTURE' and doc.dataFile.versionNumber==20 and not doc.dataFile.isReadOnly
    assert not d.snapshots.hasPendingSnapshot
    refs=[o for o in root.allOccurrences if o.component.name==OLD];assert len(refs)==23
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(BASE+'cad/design/checkpoints/v05_cloud_v20_before_spring_mini_fix_pin_removal.f3d'))
    def record(o):return dict(name=o.component.name,path=o.fullPathName,matrix=list(o.transform2.asArray()),bodies=o.component.bRepBodies.count,volumes=[b.volume*1000 for b in o.component.bRepBodies],visible=o.isLightBulbOn)
    before=[record(o) for o in root.allOccurrences]
    pinRows=[r for r in before if r['name']=='pin3' and 'CHOC_SWITCHES_AND_SOCKETS_REFERENCE_23_PAIRS:1+' in r['path']];assert len(pinRows)==23
    red=refs[0].component.occurrences.item(0).component
    pin=next(o for o in red.occurrences if o.component.name=='pin3');assert pin.component.bRepBodies.count==1
    pinVolume=pin.component.bRepBodies.item(0).volume*1000
    feature=red.features.removeFeatures.add(pin);assert feature;feature.name='Omit_generic_fix_pin3_absent_on_target_Spring_MINI'
    refs[0].component.name=NEW
    assert d.computeAll()
    after=[record(o) for o in root.allOccurrences]
    assert len(before)-len(after)==23
    expected={r['path']:r for r in before if r not in pinRows}
    for r in after:
        path=r['path'].replace(NEW,OLD);old=expected[path]
        assert r['matrix']==old['matrix'] and r['bodies']==old['bodies'] and r['volumes']==old['volumes'] and r['visible']==old['visible'],path
    group=next(o for o in root.occurrences if o.component.name=='CHOC_SWITCHES_AND_SOCKETS_REFERENCE_23_PAIRS')
    def walk(o,counts):
        assert o.component.name!='pin3',o.fullPathName
        for b in o.component.bRepBodies:counts['bodies']+=1
        if o.component.name in ['pin1','pin2']:counts['electricalPinOccurrences']+=1
        if o.component.name=='stem':counts['stems']+=1
        for ch in o.childOccurrences:walk(ch,counts)
    totals=dict(bodies=0,electricalPinOccurrences=0,stems=0)
    for o in group.childOccurrences:
        if o.component.name.startswith('CHOC_V2_RED_DETAILED_'):
            one=dict(bodies=0,electricalPinOccurrences=0,stems=0);walk(o,one);assert one==dict(bodies=7,electricalPinOccurrences=2,stems=1),str(one)
            for k in totals:totals[k]+=one[k]
    assert totals==dict(bodies=161,electricalPinOccurrences=46,stems=23)
    manifest=json.load(open(BASE+'cad/reference/third-party/koktoh/manifest.json',encoding='utf-8'))
    for f in manifest['files']:
        b=open(BASE+'cad/reference/third-party/koktoh/'+f['file'],'rb').read();assert hashlib.sha256(b).hexdigest()==f['sha256']
    issues=[t.errorOrWarningMessage for t in d.timeline if t.errorOrWarningMessage];assert not issues,str(issues)
    report=dict(date='2026-11-08',baselineCloudVersion=20,selectedPart='pin3',targetProduct='Kailh Spring MINI ChocV2',derivedComponentName=NEW,
        operation='Parametric Remove feature on shared imported red component; removed from all23 instances, not merely hidden',removedPinOccurrences=23,removedPinBodyVolumeEach_mm3=pinVolume,
        switchBodies=161,socketBodies=161,totalDetailedChocBodies=322,electricalPinOccurrencesPreserved=46,stemsPreserved=23,remainingMatricesVolumesAndVisibilityPreserved=True,caseAndCarrierGeometryUnchanged=True,
        upstreamFilesHashVerified=True,timelineIssues=issues,decisionBasis='User reports target lacks selected pin; manufacturer old fix-pin design and retailer Spring MINI underside photo corroborate absence.',
        sources=[dict(url='https://www.kailhswitch.com/info/kailh-choc-v2-feature-44841625.html',finding='2020 generic ChocV2 design includes a movable fix pin'),dict(url='https://shop.talpkeyboard.com/products/kailh-spring-mini-chocv2',finding='Retailer product underside photo shows two metal contacts and central plastic post, with no corresponding opposite-corner metal fix pin',imageURL='https://shop.talpkeyboard.com/cdn/shop/files/2025-05-1522.10.58.png?v=1747314687'),dict(url='https://shop.yushakobo.jp/products/18433',finding='3pin listing exists; pin-count label alone does not prove three metal terminals')],
        limitations=['Spring MINI-specific full CAD/dimension drawing not obtained; remaining proxy dimensions and exact lot are not certified','Removal affects CAD reference only; no recommendation to cut a physical switch or electrical terminal','Remaining physical PCB hole/pad, latch, press-fit, tolerances and machining checks still pending'])
    json.dump(report,open(BASE+'docs/spring-mini-fix-pin-removal.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(report,ensure_ascii=False))
