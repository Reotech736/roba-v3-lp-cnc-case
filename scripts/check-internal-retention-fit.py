"""Fusion MCP: separate actual candidate parts, reservations, and detailed sockets."""
import adsk.core,adsk.fusion,json
BASE='C:/Users/Reo Komatsubara/git-repositories/roba-v3-lp-cnc-case/'


def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct);root=d.rootComponent
    def get(prefix):return next(o for o in root.allOccurrences if o.component.name.startswith(prefix))
    prefixes=('Lower_L_','Upper_L_','MCU_RAISED_','PCB_L_','XIAO_KEY_SIDE_','SWITCH_','PCB_SUPPORT_INSULATION_','BATTERY_REMOVABLE_CARRIER_','CARRIER_BASE_REMOVABLE_','CELL_REMOVABLE_ADHESIVE_','BATTERY_CELL_NOMINAL_','B1_JST_PH_SMD_')
    core=[o for o in root.allOccurrences if o.component.name.startswith(prefixes)]
    def analyze(items):
        col=adsk.core.ObjectCollection.create()
        for item in items:col.add(item)
        ii=d.createInterferenceInput(col);ii.areCoincidentFacesIncluded=False;r=d.analyzeInterference(ii)
        return [dict(first=h.entityOne.parentComponent.name,second=h.entityTwo.parentComponent.name,volume_mm3=h.interferenceBody.volume*1000) for h in r]
    core_hits=analyze(core)
    wire=get('BATTERY_WIRE_ROUTE_');wire_hits=analyze(core+[wire])
    wire_hits=[h for h in wire_hits if wire.component.name in [h['first'],h['second']]]
    slack=get('BATTERY_SERVICE_SLACK_');slack_hits=analyze(core+[slack])
    slack_hits=[h for h in slack_hits if slack.component.name in [h['first'],h['second']]]
    pull=get('CELL_ADHESIVE_PULL_TAB_');pull_hits=analyze(core+[pull])
    pull_hits=[h for h in pull_hits if pull.component.name in [h['first'],h['second']]]
    plug=get('B1_MATING_PLUG_ACCESS_');plug_hits=analyze([get('Lower_L_'),get('Upper_L_'),get('BATTERY_REMOVABLE_CARRIER_'),get('BATTERY_CELL_NOMINAL_'),plug])
    # Inspect detailed sockets against all newly introduced physical candidates and wire route.
    physical=[o for o in root.allOccurrences if o.component.name.startswith(('PCB_SUPPORT_INSULATION_','BATTERY_REMOVABLE_CARRIER_','CARRIER_BASE_REMOVABLE_','CELL_REMOVABLE_ADHESIVE_','BATTERY_CELL_NOMINAL_','B1_JST_PH_SMD_'))]+[wire,slack]
    items=list(physical)
    def walk(o):
        for b in o.bRepBodies:items.append(b)
        for child in o.childOccurrences:walk(child)
    for o in root.allOccurrences:
        if o.component.name.startswith('CHOC_SOCKET_DETAILED_'):walk(o)
    sock=analyze(items);names={o.component.name for o in physical}
    socket_hits=[h for h in sock if (h['first'] in names)!=(h['second'] in names)]
    intentional=[h for h in sock if {h['first'],h['second']}=={wire.component.name,slack.component.name}]
    out=dict(date='2026-11-08',coreSolidCount=sum(o.component.bRepBodies.count for o in core),coreInterferences=core_hits,wireVsAssemblyInterferences=wire_hits,
             assumedPlugAccessVsCasesInterferences=plug_hits,slackSpaceVsAssemblyInterferences=slack_hits,pullTabAccessVsAssemblyInterferences=pull_hits,detailedSocketsVsNewPartsInterferences=socket_hits,intentionalWireVsSlackReservationOverlap= intentional)
    json.dump(out,open(BASE+'docs/internal-retention-fit-verification.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False))
