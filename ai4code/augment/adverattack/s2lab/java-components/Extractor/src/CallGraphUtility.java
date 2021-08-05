import soot.Scene;
import soot.SootClass;
import soot.SootMethod;
import soot.Unit;
import soot.jimple.infoflow.android.SetupApplication;
import soot.jimple.toolkits.callgraph.CallGraph;
import soot.jimple.toolkits.callgraph.Edge;

import java.util.*;

public class CallGraphUtility {


    private int THRESHOLD = 15;

    Soot_utlilty utlity = new Soot_utlilty();

    public ArrayList<SootClass> get_callgraph(String apkPath, String sdk_path, SootClass searched) {

        SetupApplication app = new SetupApplication(sdk_path, apkPath);
        app.constructCallgraph();
        CallGraph cg = Scene.v().getCallGraph();
        ArrayList<SootClass> result = new ArrayList<>();
        ArrayList<SootClass> to_ret = new ArrayList<>();
        try{
            System.out.println("Searching Activity : "+searched.getName()+" with recursive depth : "+THRESHOLD+"\nThis could take some time ...\n");
            to_ret =search(cg, result, searched, null, 0);
        }catch (Exception e){
            System.out.println(e.getMessage());
        }
        return to_ret;

    }


    public Map<SootClass,ArrayList<SootMethod>> get_callgraph_for_method(String apkPath, String sdk_path, SootClass searched,SootMethod method) {

        SetupApplication app = new SetupApplication(sdk_path, apkPath);
        app.constructCallgraph();
        CallGraph cg = Scene.v().getCallGraph();
        Map<SootClass,ArrayList<SootMethod>> result = new HashMap<>();
        Map<SootClass,ArrayList<SootMethod>> to_ret = new HashMap<>();

        try{
            System.out.println("Searching Method : "+searched.getName()+" with recursive depth : "+THRESHOLD+"\nThis could take some time ...\n");
            to_ret =search_method(cg, result, searched, null, 0,method);
        }catch (Exception e){
            System.out.println(e.getMessage());
        }
        return to_ret;

    }





    private ArrayList<SootClass> search(CallGraph cg, ArrayList<SootClass> tmp, SootClass searched, SootClass previous, int deep) {

        for (Iterator<Edge> iter = cg.iterator(); iter.hasNext(); ) {
            Edge current_node = iter.next();
            if (current_node.getTgt().method().toString().contains(searched.getName()) && !current_node.getSrc().method().toString().contains(searched.getName())) {
                if(utlity.isExcludeClass(current_node.getSrc().method().getDeclaringClass())){
                    continue;
                }
                if (current_node.getSrc().method().getDeclaringClass().hasSuperclass() && utlity.get_if_ancient(current_node.getSrc().method().getDeclaringClass(),"android.app.Activity")) {
                    if(!tmp.contains(current_node.getSrc().method().getDeclaringClass())) {
                        tmp.add(current_node.getSrc().method().getDeclaringClass());
                    }
                }else{

                    if(previous!=null) {
                        if(!previous.getName().equals(current_node.getSrc().method().getDeclaringClass().getName())){
                            if(deep<THRESHOLD) {
                                deep++;
                                search(cg, tmp, current_node.getSrc().method().getDeclaringClass(), searched, deep);
                            }
                        }

                    }else{
                        if(deep<THRESHOLD) {
                            deep++;
                            search(cg, tmp, current_node.getSrc().method().getDeclaringClass(), searched, deep);
                        }
                    }
                    }


            }
        }
        return tmp;
    }

    private Map<SootClass,ArrayList<SootMethod>> search_method(CallGraph cg, Map<SootClass,ArrayList<SootMethod>> tmp, SootClass searched, SootClass previous, int deep,SootMethod method) {


        for (Iterator<Edge> iter = cg.iterator(); iter.hasNext(); ) {
            Edge current_node = iter.next();

            if (current_node.getTgt().method().getSignature().equals(method.getSignature())) {
                if (utlity.isExcludeClass(current_node.getSrc().method().getDeclaringClass())) {
                    continue;
                }
                if(current_node.getSrc().method().getDeclaringClass().getName().equals(searched.getName()) && !current_node.isClinit()){
                    if(Instrumenter.DEBUG) {
                        System.out.println("DEBUG : To recurse " + current_node.toString());
                    }
                    if(deep<THRESHOLD){
                     deep++;
                     if(previous!=null){
                         if(!previous.getName().equals(current_node.getSrc().method().getDeclaringClass().getName())){
                             search_method(cg, tmp, current_node.getSrc().method().getDeclaringClass(), searched, deep,current_node.getSrc().method());
                         }
                    }else{
                         search_method(cg, tmp, current_node.getSrc().method().getDeclaringClass(), searched, deep,current_node.getSrc().method());
                     }
                    }

                }else{
                    SootClass to_add = current_node.getSrc().method().getDeclaringClass();
                    SootMethod to_add_m = current_node.getSrc().method();
                    if(tmp.keySet().contains(to_add)) {
                        ArrayList<SootMethod> tmp_list = tmp.get(to_add);
                        if(!tmp_list.contains(to_add_m)) {
                            tmp_list.add(to_add_m);
                            if(Instrumenter.DEBUG) {
                                System.out.println("Extracting method "+to_add_m.getSignature()+"which calls "+method.getSignature() );
                            }
                        }
                        tmp.put(to_add,tmp_list);
                    }else{
                        ArrayList<SootMethod> tmp_list = new ArrayList<>();
                        tmp_list.add(to_add_m);
                        if(Instrumenter.DEBUG) {
                            System.out.println("Extracting method "+to_add_m.getSignature()+"which calls "+method.getSignature() );
                        }
                        tmp.put(to_add, tmp_list);
                    }

                }

            }
        }
        return tmp;

    }




}
