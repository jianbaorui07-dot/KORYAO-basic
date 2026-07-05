# ruff: noqa
# fmt: off
import json, os, unreal
root=os.path.dirname(os.path.normpath(unreal.Paths.project_dir()))
out=os.path.join(root,'03_WorldForge控制层','Logs','WorldForge_v02_inputcomponent_probe.json')
classes=['InputComponent','PlayerInput','PlayerController','DefaultPawn','Pawn','Actor','EnhancedInputComponent','EnhancedInputLocalPlayerSubsystem','EnhancedInputWorldSubsystem','InputSettings','K2Node','EdGraph','EdGraphNode']
res={}
for c in classes:
    obj=getattr(unreal,c,None)
    res[c]={'exists':obj is not None,'methods':[m for m in dir(obj) if not m.startswith('_')] if obj else []}
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out,'w',encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=2))
unreal.SystemLibrary.quit_editor()
