# ruff: noqa
# fmt: off
import json, os, unreal
root=os.path.dirname(os.path.normpath(unreal.Paths.project_dir()))
out=os.path.join(root,'03_WorldForge控制层','Logs','WorldForge_v02_widget_property_probe.json')
paths=['/Game/WorldForge/UI/WBP_WorldForgeStatus','/Game/WorldForge/EditorTools/EUW_WorldForgeControlDesk']
res={}
for path in paths:
    asset=unreal.EditorAssetLibrary.load_asset(path)
    item={'exists': asset is not None, 'class': str(asset.get_class().get_name()) if asset else None, 'dir_filtered': []}
    if asset:
        item['dir_filtered']=[n for n in dir(asset) if any(t in n.lower() for t in ['widget','tree','graph','button','bind','delegate','anim','generated','blueprint','layout'])]
        for prop in ['widget_tree','WidgetTree','ubergraph_pages','function_graphs','event_graph','generated_class']:
            try:
                v=asset.get_editor_property(prop)
                item[prop]=str(v)
            except Exception as e:
                item[prop+'_error']=str(e)
    res[path]=item
open(out,'w',encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=2))
unreal.SystemLibrary.quit_editor()
