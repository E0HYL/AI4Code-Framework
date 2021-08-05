
import soot.*;
import soot.jimple.*;
import soot.toolkits.graph.Block;
import soot.toolkits.graph.ExceptionalBlockGraph;
import soot.toolkits.graph.ExceptionalUnitGraph;

import java.io.Serializable;
import java.util.*;


public class My_slice implements Serializable {

    private ArrayList<Local> my_locals;
    private ArrayList<Unit> my_units;
    private Soot_utlilty utility = new Soot_utlilty();
    private String name = "tmp";
    private String feature = "tmp";
    private Activity_extractor a_e = new Activity_extractor();
    private static final double COMPLEXITY_RATIO=0.5;

    public My_slice(ArrayList<Local> my_locals, ArrayList<Unit> my_units) {
        this.my_locals = my_locals;
        this.my_units = my_units;
    }

    public ArrayList<Local> getMy_locals() {
        return my_locals;
    }

    public void setMy_locals(ArrayList<Local> my_locals) {
        this.my_locals = my_locals;
    }

    public ArrayList<Unit> getMy_units() {
        return my_units;
    }

    public void setMy_units(ArrayList<Unit> my_units) {
        this.my_units = my_units;
    }



    public String getFeature() {
        return feature;
    }

    public void setFeature(String feature) {
        this.feature = feature;
    }

    public ArrayList<Unit> clear_Unit_list(){
        ArrayList<Unit> to_ret = new ArrayList<>();
        for(Iterator<Unit> iter = getMy_units().iterator(); iter.hasNext();){
            Unit u = iter.next();
            if(!(u instanceof IdentityStmt)) {
                to_ret.add(u);
            }
        }
        return  to_ret;
    }

    public SootClass get_soot_class(){

        SootClass sClass = new SootClass(name, Modifier.PUBLIC);
        sClass.setSuperclass(Scene.v().getSootClass("java.lang.Object"));
        SootMethod method = new SootMethod(utility.to_underline(feature),
                null,
                VoidType.v(), Modifier.PUBLIC );
        Body b = Jimple.v().newBody(method);

        Local thisLocal = Jimple.v().newLocal("this", sClass.getType());
        b.getLocals().add(thisLocal);
        b.getUnits().add(Jimple.v().newIdentityStmt(thisLocal, Jimple.v().newThisRef(sClass.getType())));
        SootMethod get_context = Scene.v().getMethod("<android.content.Context: android.content.Context getApplicationContext()>");
        VirtualInvokeExpr vinvokeExpr = null;
        for(Local l: my_locals){

            b.getLocals().add(l);
            if(l.getType().toString().contains("android.content.Context")){
                vinvokeExpr = Jimple.v().newVirtualInvokeExpr(thisLocal,get_context.makeRef());
                AssignStmt astmt = Jimple.v().newAssignStmt(l, vinvokeExpr);
                b.getUnits().add(astmt);
            }
        }

        for(Unit u : clear_Unit_list()){

                b.getUnits().add(u);

        }
        Unit last = b.getUnits().getLast();

        if(!(last instanceof ReturnVoidStmt)) {
            if(last instanceof ReturnStmt){
                b.getUnits().remove(last);
            }
            b.getUnits().add(Jimple.v().newReturnVoidStmt());
        }
        method.setActiveBody(b);

        sClass.addMethod(method);
        b.validate();
        return  sClass;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public double slice_complexity_score(){
        int complex=0;
        ArrayList types= new ArrayList();
        for(Local l : my_locals){
            if(!types.contains(l.getType().toString())){
                types.add(l.getType().toString());
            }
            if(! (utility.isExcludeClass(l.getType().toString()))){
                complex++;
            }
        }
        int CC =calculate_cyclomatic_complexity(this.get_soot_class());
        return complex+types.size()+CC;
    }

    public int calculate_cyclomatic_complexity(SootClass c){
        int out = 0;

        for(SootMethod m : c.getMethods()){
            if(!m.hasActiveBody()){
                continue;
            }else{
                int edges, nodes,tmp_result;
                Body b = m.getActiveBody();
                ExceptionalUnitGraph CFG = new ExceptionalUnitGraph(b);
                try {
                    ExceptionalBlockGraph BFG = new ExceptionalBlockGraph(CFG);
                    Block first = BFG.getHeads().get(0);
                    edges = get_edges(new ArrayList<Block>(), first);
                    nodes = BFG.size();
                    tmp_result = edges - nodes + 2;
                    out += tmp_result;
                }catch (Exception e){
                    System.out.println("Error with Block Control Flow Graph, calulcating CC with normal CFG");
                    Unit first = CFG.getHeads().get(0);
                    edges = get_edges(new ArrayList<Unit>(), first, CFG);
                    nodes = CFG.size();
                    tmp_result = edges - nodes + 2;
                    out += tmp_result;
                }
            }
        }


        return out;
    }


    public int get_edges(ArrayList<Unit> to_avoid, Unit start, ExceptionalUnitGraph CFG){
        List<Unit> tmp =CFG.getSuccsOf(start);
        to_avoid.add(start);
        if(tmp.isEmpty()){
            return 0;
        }else{
            int result= tmp.size();
            for(Unit b : tmp){
                if(!to_avoid.contains(b)) {
                    to_avoid.add(b);
                    result += get_edges(to_avoid, b,CFG);
                }
            }
            return result;
        }
    }

    public int get_edges(ArrayList<Block> to_avoid, Block start){
        List<Block> tmp =start.getSuccs();
        to_avoid.add(start);
        if(tmp.isEmpty()){
            return 0;
        }else{
            int result= tmp.size();
            for(Block b : tmp){
                if(!to_avoid.contains(b)) {
                    to_avoid.add(b);
                    result += get_edges(to_avoid, b);
                }
            }
            return result;
        }
    }

    public ArrayList<String> get_dependencies(){
        ArrayList<String> slice_dependencies = new ArrayList<>();
        for(Unit u : my_units){

            for(ValueBox v : u.getUseAndDefBoxes()){
                if (v.getValue() instanceof InvokeExpr){
                    System.out.println("YO");
                    try {
                        InvokeExpr st = (InvokeExpr) v.getValue();
                        SootMethod m = st.getMethod();
                        SootClass sc = m.getDeclaringClass();
                        if(!utility.isExcludeClass(sc)) {
                            slice_dependencies.add(sc.getName());
                        }
                    }catch (Exception e){
                        continue;
                    }
                }
                if(!utility.isExcludeClass(v.getValue().getType().toString())) {
                    for(String s : a_e.extract_activity_dependencies_PDG(new ArrayList<String>(),v.getValue().getType().toString())){
                        if(!slice_dependencies.contains(s)){
                            slice_dependencies.add(s);
                        }
                    }
                }
            }
        }
        for(Local l : my_locals){
            if(!utility.isExcludeClass(l.getType().toString())) {
                for(String s : a_e.extract_activity_dependencies_PDG(new ArrayList<String>(),l.getType().toString())){
                    if(!slice_dependencies.contains(s)){
                        slice_dependencies.add(s);
                    }
                }
            }
        }
        Set<String> foo = new HashSet<String>(slice_dependencies);
        ArrayList<String> mainList = new ArrayList<String>();
        mainList.addAll(foo);
        return mainList;
    }

    @Override
    public String toString() {
        SootMethod method = new SootMethod("tmp",
                null,
                VoidType.v(), Modifier.PUBLIC );
        Body b = Jimple.v().newBody(method);
        for(Local l: my_locals){
            b.getLocals().add(l);
        }
        for(Unit u : my_units){
            b.getUnits().add(u);
        }
        return b.toString();
    }


}
