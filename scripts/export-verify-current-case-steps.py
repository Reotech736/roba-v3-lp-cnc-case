"""Export v27 local bodies through isolated root components; round-trip STEP.

Works around an empty non-root-component export despite execute()==True.
Temporary unsaved documents are owned by this script and closed without saving.
Original design geometry, display and cloud version are not changed.
"""
import adsk.core,adsk.fusion,json,re
from pathlib import Path
BASE=Path('C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case')


def run(_context: str):
    app=adsk.core.Application.get();original=app.activeDocument;design=adsk.fusion.Design.cast(app.activeProduct)
    assert original.dataFile.id=='urn:adsk.wipprod:dm.lineage:H9Nq8f1PSl6GXmxJMgIkbw'
    assert original.dataFile.versionNumber==27 and original.dataFile.isComplete and not original.isModified
    mgr=adsk.fusion.TemporaryBRepManager.get()
    jobs=[('Lower_L_','left_case_two_stands_v05_NOT_FOR_MANUFACTURE_Lower_L_LOCAL.step'),
          ('Upper_L_','left_case_two_stands_v05_NOT_FOR_MANUFACTURE_Upper_L_protective_roof_LOCAL.step'),
          ('WIRE_STRAIN_RELIEF_CASE_BRACKET_','wire_strain_relief_case_bracket_NONMETAL_NOT_FOR_MANUFACTURE_LOCAL.step')]
    results=[]
    for prefix,file in jobs:
        comp=next(c for c in design.allComponents if c.name.startswith(prefix));assert comp.bRepBodies.count==1
        source=comp.bRepBodies.item(0);expectedVolume=source.volume*1000
        expectedBounds=[[v*10 for v in p.asArray()] for p in [source.preciseBoundingBox.minPoint,source.preciseBoundingBox.maxPoint]]
        body=mgr.copy(source);assert body.isSolid
        scratch=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        scratchDesign=adsk.fusion.Design.cast(app.activeProduct);scratchDesign.designType=adsk.fusion.DesignTypes.DirectDesignType
        root=scratchDesign.rootComponent
        localMaterial=scratchDesign.materials.itemByName(source.material.name) or scratchDesign.materials.addByCopy(source.material,source.material.name);root.material=localMaterial
        exportedBody=root.bRepBodies.add(body);exportedBody.material=localMaterial;exportedBody.name=source.name;exportedBody.isLightBulbOn=True;root.isBodiesFolderLightBulbOn=True
        assert abs(exportedBody.volume*1000-expectedVolume)<1e-5
        path=BASE/'cad/design'/file
        assert scratchDesign.exportManager.execute(scratchDesign.exportManager.createSTEPExportOptions(str(path),root))
        raw=path.read_text(encoding='utf-8')
        raw='\n'.join(line.rstrip() if line.lstrip().startswith('* from STEP Tools') or line.lstrip().startswith('/* name */') else line for line in raw.splitlines())+'\n'
        materialPolicy='Supplier6061T6 case properties'
        if prefix.startswith('WIRE_'):
            # Nonmetal grade is unselected. Strip only material-property subgraphs,
            # including the inherited default-steel density; keep geometry/units.
            entities={int(m.group(1)):m.group(2) for m in re.finditer(r'#(\d+)=(.*?);',raw,re.S)}
            refs={k:set(map(int,re.findall(r'#(\d+)',v))) for k,v in entities.items()}
            props={k for k,v in entities.items() if v.lstrip().startswith("PROPERTY_DEFINITION('material property'")}
            removed={k for k,v in entities.items() if v.lstrip().startswith('PROPERTY_DEFINITION_REPRESENTATION(') and refs[k]&props}
            candidates=set(removed)
            for _ in range(len(entities)):
                expanded=candidates|set().union(*(refs[k] for k in candidates))
                if expanded==candidates:break
                candidates=expanded
            while True:
                eligible={k for k in candidates-removed if not any(k in rr for q,rr in refs.items() if q not in removed)}
                if not eligible:break
                removed|=eligible
            raw=re.sub(r'#(\d+)=(.*?);',lambda m:'' if int(m.group(1)) in removed else m.group(0),raw,flags=re.S)
            assert not any("PROPERTY_DEFINITION('material property'" in v for k,v in entities.items() if k not in removed)
            materialPolicy='Unselected nonmetal: default steel material subgraph omitted; CAD bracket mass is not qualified'
        else:
            assert 'JLCCNC_6061_T6_SUPPLIER_MINIMUM_PROVISIONAL' in raw and '2800.' in raw
        path.write_text(raw,encoding='utf-8',newline='\n')
        assert raw.startswith('ISO-10303-21;') and 'END-ISO-10303-21;' in raw
        assert len(re.findall(r'=\s*MANIFOLD_SOLID_BREP\s*\(',raw))==1,file
        scratch.close(False)
        options=app.importManager.createSTEPImportOptions(str(path))
        imported=app.importManager.importToNewDocument(options);assert imported
        importedDesign=adsk.fusion.Design.cast(imported.products.itemByProductType('DesignProductType'))
        bodies=[]
        for b in importedDesign.rootComponent.bRepBodies:bodies.append(b)
        for o in importedDesign.rootComponent.allOccurrences:
            for b in o.bRepBodies:bodies.append(b)
        assert len(bodies)==1 and bodies[0].isSolid
        actualVolume=bodies[0].volume*1000
        bb=bodies[0].preciseBoundingBox;actualBounds=[[v*10 for v in p.asArray()] for p in [bb.minPoint,bb.maxPoint]]
        deltaVolume=abs(actualVolume-expectedVolume)
        deltaBounds=max(abs(a-b) for aa,bb in zip(expectedBounds,actualBounds) for a,b in zip(aa,bb))
        assert deltaVolume<=max(.01,expectedVolume*1e-6),str((file,deltaVolume))
        assert deltaBounds<.002,str((file,deltaBounds))
        results.append({'file':file,'materialPolicy':materialPolicy,'singleSolid':True,'bytes':path.stat().st_size,'expectedVolume_mm3':expectedVolume,
                        'roundTripVolume_mm3':actualVolume,'absoluteVolumeDifference_mm3':deltaVolume,
                        'expectedLocalBounds_mm':expectedBounds,'roundTripLocalBounds_mm':actualBounds,'maxBoundDifference_mm':deltaBounds})
        imported.close(False)
        original.activate()
        assert not original.isModified
        (BASE/'docs/case-wire-bracket-step-roundtrip.json').write_text(json.dumps({'date':'2026-11-09','cloudVersion':27,'method':'Copy native local BRep to an isolated direct-design root, STEP export, import to new temporary document; check single solid, volume and local bounds','results':results},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert original.dataFile.versionNumber==27 and original.dataFile.isComplete and not original.isModified
    print(json.dumps({'verifiedSTEPFiles':len(results),'results':[{k:v for k,v in r.items() if 'Bounds' not in k} for r in results],'originalUnmodified':True}))
