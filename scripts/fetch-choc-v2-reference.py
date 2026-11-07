"""Fetch unmodified author CAD at a pinned commit; separate third-party license."""
import hashlib
import json
from pathlib import Path
import urllib.request

BASE=Path(__file__).resolve().parents[1]
REPO='koktoh/keyswitch_model'


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'roba-cad-reference'}),timeout=45).read()


def main():
    target=BASE/'cad/reference/third-party/koktoh'
    target.mkdir(parents=True,exist_ok=True)
    manifest=target/'manifest.json'
    commit=json.loads(manifest.read_text(encoding='utf-8'))['commit'] if manifest.exists() else json.loads(get('https://api.github.com/repos/'+REPO+'/commits/master'))['sha']
    paths={'choc-v2-red-kicad.step':'choc/v2/KiCad/red.step',
           'choc-socket-kicad.step':'socket/KiCad/choc.step',
           'upstream-README.md':'README.md'}
    records=[]
    for name,path in paths.items():
        url='https://raw.githubusercontent.com/'+REPO+'/'+commit+'/'+path
        data=get(url);dst=target/name
        if dst.exists():assert dst.read_bytes()==data,'Existing reference differs: '+name
        else:dst.write_bytes(data)
        records.append(dict(file=name,upstreamPath=path,url=url,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    out=dict(repository='https://github.com/'+REPO,commit=commit,date='2026-11-08',author='koktoh',
             license='CC BY-NC-SA 4.0',licenseURL='https://creativecommons.org/licenses/by-nc-sa/4.0/',
             usage='Unmodified component references. Separate from project GPL license. Not manufacturer-certified Spring Mini CAD.',files=records)
    manifest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out,indent=2))


if __name__=='__main__':main()
