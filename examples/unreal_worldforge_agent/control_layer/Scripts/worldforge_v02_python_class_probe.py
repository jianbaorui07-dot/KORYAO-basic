# ruff: noqa
# fmt: off
import json, os, unreal
root=os.path.dirname(os.path.normpath(unreal.Paths.project_dir()))
out=os.path.join(root,'03_WorldForge控制层','Logs','WorldForge_v02_python_class_capability.json')
attrs=['uclass','ufunction','uproperty','PythonGeneratedClass','PythonScriptLibrary','PythonScriptPlugin','PythonBlueprintFunctionLibrary','PyTestStructLibrary']
res={a: hasattr(unreal,a) for a in attrs}
res['python_related_names']=[n for n in dir(unreal) if 'python' in n.lower() or n in ['uclass','ufunction','uproperty']]
open(out,'w',encoding='utf-8').write(json.dumps(res,ensure_ascii=False,indent=2))
unreal.SystemLibrary.quit_editor()
